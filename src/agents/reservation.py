from __future__ import annotations
from typing import Optional
from uuid import uuid4

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from pydantic import BaseModel, Field

from src.memory.state import ParkingState


class ExtractedFields(BaseModel):
    """Parking reservation fields found in the user's message."""

    name: Optional[str] = Field(None, description="First name if explicitly mentioned")
    surname: Optional[str] = Field(None, description="Last / family name if explicitly mentioned")
    car_plate: Optional[str] = Field(None, description="Vehicle license plate if mentioned")
    date_start: Optional[str] = Field(None, description="Reservation start date if mentioned")
    date_end: Optional[str] = Field(None, description="Reservation end date if mentioned")


REQUIRED_FIELDS: dict[str, str] = {
    "name": "first name",
    "surname": "last name",
    "car_plate": "license plate number",
    "date_start": "start date",
    "date_end": "end date",
}


EXTRACTION_SYSTEM = (
    "You are extracting parking reservation details from a user's message.\n"
    "Only extract fields the user explicitly provides.\n"
    "If the user corrects a previously given value, return the corrected value.\n"
    "Do not guess or fabricate any information.\n\n"
    "Already collected: {existing}"
)


class ReservationAgent:
    """Collects reservation details over one or more conversational turns.

    Each invocation:
      1. Extracts whatever fields the latest message contains.
      2. Merges them with previously collected data.
      3. Returns either a prompt for missing fields
         or a summary + status flip to ``pending_approval``.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self.extractor = llm.with_structured_output(ExtractedFields)

    
    def __call__(self, state: ParkingState) -> dict:
        existing = state.get("reservation") or {}
        last_msg = state["messages"][-1]

        extracted = self._extract(last_msg.content, existing)
        merged = self._merge(existing, extracted)
        missing = self._get_missing(merged)

        if not missing:
            return {
                "reservation": merged,
                "reservation_status": "pending_approval",
                "reservation_id": str(uuid4()),
                "messages": [AIMessage(content=self._format_summary(merged))]
            }

        return {
            "reservation": merged,
            "reservation_status": "collecting",
            "messages": [
                AIMessage(content=self._format_ask(missing, is_first_turn=not existing))
            ],
        }
    
    def _extract(self, message: str, existing: dict) -> ExtractedFields:
        return self.extractor.invoke(
            [
                SystemMessage(
                    content=EXTRACTION_SYSTEM.format(existing=existing)
                ),
                HumanMessage(content=message),
            ]
        )
    
    @staticmethod
    def _merge(existing: dict, extraced: ExtractedFields) -> dict:
        """Overlay non-None extracted values onto existing data."""
        merged = {**existing}
        for field, value in extraced.model_dump().items():
            if value is not None:
                merged[field] = value

        return merged

    @staticmethod
    def _get_missing(reservation: dict) -> list[str]:
        return [f for f in REQUIRED_FIELDS if not reservation.get(f)]

    @staticmethod
    def _format_ask(missing: list[str], *, is_first_turn: bool) -> str:
        friendly = [REQUIRED_FIELDS[f] for f in missing] 
        joined = ", ".join(friendly)

        if is_first_turn:
            return (
                "I'd be happy to help you reserve a parking spot! "
                "I'll need your {joined}. "
            )
        
        return f"Thanks! I still need your {joined}."

    @staticmethod
    def _format_summary(reservation: dict) -> str:
        return (
            "Here's your reservation summary:\n"
            f"  Name: {reservation['name']} {reservation['surname']}\n"
            f"  Plate: {reservation['vehicle_plate']}\n"
            f"  From: {reservation['date_start']} to {reservation['date_end']}\n\n"
            "Sending this to our admin for approval…"
        )
