from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage
import pytest


@pytest.fixture
def reservation_agent():
    from src.agents.reservation import ReservationAgent, ExtractedFields

    extractor = MagicMock()
    extractor.invoke.return_value = ExtractedFields(name="Bob")
    llm = MagicMock()
    llm.with_structured_output.return_value = extractor
    return ReservationAgent(llm)


def test_reservation_collecting_on_partial_data(reservation_agent):
    result = reservation_agent(
        {"messages": [HumanMessage(content="My name is Bob")], "reservation": {}}
    )

    assert result["reservation_status"] == "collecting"
    assert result["reservation"]["name"] == "Bob"


def test_reservation_merge_skips_none_values():
    from src.agents.reservation import ReservationAgent, ExtractedFields

    merged = ReservationAgent._merge(
        {"name": "Alice", "surname": "Smith"},
        ExtractedFields(surname="Jones", vehicle_plate=None),
    )

    assert merged["surname"] == "Jones"  # overwritten
    assert merged["name"] == "Alice"  # preserved
    assert "vehicle_plate" not in merged  # None not written


def test_reservation_get_missing_identifies_absent_fields():
    from src.agents.reservation import ReservationAgent

    missing = ReservationAgent._get_missing({"name": "Alice", "surname": "Smith"})

    assert set(missing) == {"vehicle_plate", "date_start", "date_end"}
