from src.memory.state import ParkingState
from src.notifications.base import NotificationChannel

class ApprovalRequestNode:
    def __init__(self, notification_channel: NotificationChannel) -> None:
        self.channel = notification_channel

    def __call__(self, state: ParkingState) -> dict:
        reservation = state["reservation"]
        reservation_id = state["reservation_id"]

        self.channel.send_approval_request(reservation_id, reservation)

        return {
            "reservation_status": "pending_approval"
        }
