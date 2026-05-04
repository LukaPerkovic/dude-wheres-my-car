from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from src.memory.state import ParkingState
from src.notifications.base import NotificationChannel


class HITLAgent:
    """Sends a reservation to the admin and waits for approval.

    Uses LangGraph's interrupt() to pause the graph.
    Execuation resumes when the external callback invokes
    graph.invoke(Command(resume=...). config).
    """

    def __init__(self, notification_channel: NotificationChannel) -> None:
        self.channel = notification_channel

    def __call__(self, state: ParkingState) -> dict:
        reservation = state["reservation"]
        reservation_id = state["reservation_id"]

        self.channel.send_approval_request(reservation_id, reservation)

        admin_response = interrupt(
            {
            "reservation_id": reservation_id,
            "type": "admin_approval",
            }
        )

        approved = admin_response.get("approved")

        if approved:
            return {
                "reservation_status": "approved",
                "messages": [
                    AIMessage(
                        content=(
                            "Great news — your reservation has been approved!\n"
                            f"Reservation ID: {reservation_id}"
                        )
                    )
                ],
            }
            
        reason = admin_response.get("reason", "No reason provided")
        return {
            "reservation_status": "rejected",
            "messages": [
                AIMessage(
                    content=(
                        "Unfortunately your reservation was declined.\n"
                        f"Reason: {reason}"
                    )
                )
            ]
        }
