"""MCP Client that connects to the reservation writer server."""

import os
import asyncio

from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")


class MCPReservationClient:
    """Synchronous wrapper around the async MCP SSE client"""

    def __init__(self, server_url: str = None, auth_token: str = None):
        self.server_url = server_url or MCP_SERVER_URL
        self.auth_token = auth_token or MCP_AUTH_TOKEN

    def write_reservation(
        self,
        name: str,
        vehicle_number: str,
        period: str,
        approval_time: str,
    ) -> str:
        """Write a reservation via MCP server. Return response string."""

        return self._run_sync(
            self._async_write(name, vehicle_number, period, approval_time)
        )

    async def _async_write(
        self, name: str, vehicle_number: str, period: str, approval_time: str
    ) -> str:

        async with sse_client(self.server_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "write_reservation",
                    arguments={
                        "name": name,
                        "vehicle_number": vehicle_number,
                        "period": period,
                        "approval_time": approval_time,
                        "auth_token": self.auth_token,
                    },
                )

                if result.content:
                    return result.content[0].text
                return "ERROR: Empty response from MCP server."

    def _run_sync(self, coro):
        """Run async coroutine from sync context safely."""

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=30)
