"""Conditional edge functions."""

from src.memory.state import ParkingState

def route_intent(state: ParkingState) -> str:
    return state["intent"]


def check_reservation_complete(state: ParkingState) -> str:
    return state["reservation_status"]

def route_after_hitl(state: ParkingState) -> str:
    return state["reservation_status"]


def route_after_persist(state: ParkingState) -> str:
    return state.get("persistence_status", "failed")