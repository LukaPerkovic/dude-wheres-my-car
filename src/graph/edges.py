"""Conditional edge functions."""

from src.memory.state import ParkingState

def route_intent(state: ParkingState) -> str:
    """Routes after the router ndoe based on classified intent."""
    return state["intent"]


def check_reservation_complete(state: ParkingState) -> str:
    """Routes after the reservation node based on collection status."""
    return state["reservation_status"]