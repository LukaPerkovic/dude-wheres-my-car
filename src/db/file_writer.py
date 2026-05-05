"""
Reservation writer that delegates to the MCP server.
"""

from src.mcp.client import MCPReservationClient


class ReservationWriter:
    """Writes approved reservations via the MCP server."""

    def __init__(self, server_url: str = None, auth_token: str = None):
        self.client = MCPReservationClient(
            server_url=server_url,
            auth_token=auth_token,
        )

    def write_reservation(
        self,
        name: str,
        vehicle_number: str,
        period: str,
        approval_time: str,
    ) -> None:
        result = self.client.write_reservation(
            name=name,
            vehicle_number=vehicle_number,
            period=period,
            approval_time=approval_time,
        )

        if result.startswith("ERROR"):
            raise RuntimeError(result)