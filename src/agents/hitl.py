from datetime import datetime, timezone
from langgraph.types import interrupt

from src.memory.state import ParkingState


class HITLAgent:
    """Waits for admin approval/rejection."""

    def __call__(self, state: ParkingState) -> dict:
        reservation_id = state["reservation_id"]

        admin_response = interrupt(
            {
                "reservation_id": reservation_id,
                "type": "admin_approval",
            }
        )

        approved = bool(admin_response.get("approved"))

        if approved:
            approval_time = admin_response.get("approval_time")
            if not approval_time:
                approval_time = datetime.now(timezone.utc).isoformat()

            return {
                "reservation_status": "approved",
                "approval_time": approval_time,
                "rejection_reason": None,
            }

        return {
            "reservation_status": "rejected",
            "approval_time": None,
            "rejection_reason": admin_response.get("reason", "No reason provided"),
        }
