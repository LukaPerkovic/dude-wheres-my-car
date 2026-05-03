from typing import TypedDict, Literal, Optional
from langgraph.graph import MessagesState

class ReservationDetails(TypedDict, total=False):
    name: Optional[str]
    surname: Optional[str]
    vehicle_plate: Optional[str]
    date_start: Optional[str]
    date_end: Optional[str]

class ParkingState(MessagesState):
    intent: Literal["info", "reservation", "unknown"]
    reservation: ReservationDetails
    reservation_status: Literal[
        "idle", "collecting", "pending_approval", "approved", "rejected"
    ]
    reservation_id: Optional[str]
