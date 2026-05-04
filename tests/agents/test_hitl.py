from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def hitl_agent():
    from src.agents.hitl import HITLAgent
    return HITLAgent(MagicMock())


def test_hitl_approved(hitl_agent):
    with patch("src.agents.hitl.interrupt", return_value={"approved": True, "reason": "All good"}):
        result = hitl_agent({"reservation": {"name": "Alice"}, "reservation_id": "r-001"})

    assert result["reservation_status"] == "approved"
    assert "r-001" in result["messages"][0].content
    hitl_agent.channel.send_approval_request.assert_called_once_with("r-001", {"name": "Alice"})


def test_hitl_rejected(hitl_agent):
    with patch("src.agents.hitl.interrupt", return_value={"approved": False, "reason": "No spots available"}):
        result = hitl_agent({"reservation": {}, "reservation_id": "r-002"})

    assert result["reservation_status"] == "rejected"
    assert "No spots available" in result["messages"][0].content