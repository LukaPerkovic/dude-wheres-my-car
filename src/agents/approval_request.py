from __future__ import annotations

from src.memory.state import ParkingState


class ApprovalRequestNode:
    """Fires a notification to the admin channel and confirms pending status."""

    def __init__(self, notification_channel) -> None:
        self.notification_channel = notification_channel

    def __call__(self, state: ParkingState) -> dict:
        reservation_id: str = state.get("reservation_id", "unknown")
        reservation: dict = state.get("reservation") or {}

        self.notification_channel.send_approval_request(
            reservation_id=reservation_id,
            details=reservation,
        )

        return {
            "reservation_status": "pending_approval",
        }
