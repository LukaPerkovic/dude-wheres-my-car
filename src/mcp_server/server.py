"""
MCP Server for writing confirmed reservations to file.
"""

import os
import re
import fcntl
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_DIR = Path(os.getenv("RESERVATIONS_DATA_DIR", "data"))
RESERVATIONS_FILE = DATA_DIR / "approved_reservations.txt"
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

mcp = FastMCP(
    "ReservationWriter",
)


def _sanitize(value: str) -> str:
    """Strip pipe characters and excess whitespace to protect the file format."""
    return re.sub(r"\s+", " ", value.replace("|", "/")).strip()


def _validate_token(token: str) -> bool:
    """Constant-time token comparison to resist timing attacks."""
    import hmac

    if not MCP_AUTH_TOKEN:
        return True

    return hmac.compare_digest(token, MCP_AUTH_TOKEN)


@mcp.tool()
def write_reservation(
    name: str,
    vehicle_number: str,
    period: str,
    approval_time: str,
    auth_token: str = "",
) -> str:
    """
    Write an approved reservation to the persistent text file.

    Args:
        name: Full name of the person (e.g. "John Doe")
        vehicle_number: Vehicle plate number (e.g. "ABC-1234")
        period: Reservation period (e.g. "2025-02-01 to 2025-02-05")
        approval_time: ISO timestamp when admin approved
        auth_token: Secret token for authorization

    Returns:
        Confirmation message or error description.
    """

    if not _validate_token(auth_token):
        return "ERROR: Invalid Auth token."

    if not name or not vehicle_number or not period:
        return "ERROR: name, vehicle_number, and period are required"

    safe_name = _sanitize(name)
    safe_vehicle = _sanitize(vehicle_number)
    safe_period = _sanitize(period)
    safe_time = _sanitize(approval_time) or datetime.now(timezone.utc).isoformat()

    line = f"{safe_name} | {safe_vehicle} | {safe_period} | {safe_time}\n"

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(RESERVATIONS_FILE, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(line)
            fcntl.flock(f, fcntl.LOCK_UN)
    except OSError as e:
        return f"ERROR: Could not write to file - {e}"

    return f"OK: Reservation saved for {safe_name} ({safe_vehicle})."


app = mcp.sse_app()

if __name__ == "__main__":
    mcp.run()
