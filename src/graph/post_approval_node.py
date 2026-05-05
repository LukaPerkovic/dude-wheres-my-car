from langchain_core.messages import AIMessage

from src.memory.state import ParkingState


class PersistReservationNode:
    def __init__(self, writer) -> None:
        self.writer = writer

    def __call__(self, state: ParkingState) -> dict:
        reservation = state["reservation"]

        full_name = " ".join(
            part for part in [
                reservation.get("name", "").strip(),
                reservation.get("surname", "").strip(),
            ]
            if part
        )

        vehicle_number = reservation.get("vehicle_plate", "").strip()
        period = f"{reservation.get('date_start')} to {reservation.get('date_end')}"
        approval_time = state["approval_time"]

        try:
            self.writer.write_reservation(
                name=full_name,
                vehicle_number=vehicle_number,
                period=period,
                approval_time=approval_time,
            )
            return {
                "persistence_status": "success",
                "persistence_error": None,
            }
        except Exception as e:
            return {
                "persistence_status": "failed",
                "persistence_error": str(e),
            }


def approve_response_node(state: ParkingState) -> dict:
    return {
        "messages": [
            AIMessage(
                content=(
                    "Your reservation has been approved and saved!\n"
                    f"Reservation ID: {state['reservation_id']}"
                )
            )
        ]
    }


def reject_response_node(state: ParkingState) -> dict:
    reason = state.get("rejection_reason", "No reason provided")
    return {
        "messages": [
            AIMessage(
                content=(
                    "Unfortunately your reservation was declined.\n"
                    f"Reason: {reason}"
                )
            )
        ]
    }


def persistence_failure_response_node(state: ParkingState) -> dict:
    return {
        "messages": [
            AIMessage(
                content=(
                    "Your reservation was approved, but I couldn't save it to storage.\n"
                    f"Reservation ID: {state['reservation_id']}"
                )
            )
        ]
    }