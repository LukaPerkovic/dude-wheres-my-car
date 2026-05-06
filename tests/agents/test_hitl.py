from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.fixture
def hitl_agent():
    from src.agents.hitl import HITLAgent

    return HITLAgent()


def test_hitl_approved_with_provided_time(hitl_agent):
    with patch(
        "src.agents.hitl.interrupt",
        return_value={
            "approved": True,
            "approval_time": "2026-01-01T12:00:00Z",
        },
    ):
        result = hitl_agent(
            {
                "reservation": {"name": "Alice"},
                "reservation_id": "r-001",
            }
        )

    assert result["reservation_status"] == "approved"
    assert result["approval_time"] == "2026-01-01T12:00:00Z"
    assert result["rejection_reason"] is None


def test_hitl_approved_without_time_sets_timestamp(hitl_agent):
    with patch(
        "src.agents.hitl.interrupt",
        return_value={"approved": True},
    ):
        result = hitl_agent(
            {
                "reservation": {"name": "Alice"},
                "reservation_id": "r-001",
            }
        )

    assert result["reservation_status"] == "approved"
    assert result["approval_time"] is not None

    # sanity check that it's an ISO datetime
    datetime.fromisoformat(result["approval_time"].replace("Z", "+00:00"))


def test_hitl_rejected_with_reason(hitl_agent):
    with patch(
        "src.agents.hitl.interrupt",
        return_value={
            "approved": False,
            "reason": "No spots available",
        },
    ):
        result = hitl_agent(
            {
                "reservation": {},
                "reservation_id": "r-002",
            }
        )

    assert result["reservation_status"] == "rejected"
    assert result["approval_time"] is None
    assert result["rejection_reason"] == "No spots available"


def test_hitl_rejected_without_reason_uses_default(hitl_agent):
    with patch(
        "src.agents.hitl.interrupt",
        return_value={"approved": False},
    ):
        result = hitl_agent(
            {
                "reservation": {},
                "reservation_id": "r-003",
            }
        )

    assert result["reservation_status"] == "rejected"
    assert result["approval_time"] is None
    assert result["rejection_reason"] == "No reason provided"
