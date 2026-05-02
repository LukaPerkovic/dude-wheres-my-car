"""Unit tests for src.rag.retriever"""

from unittest.mock import MagicMock

from src.rag.retriever import query


def test_query_is_blocked_when_guardrails_deny():
    """query() must short-circuit and never call the engine when input is rejected."""
    mock_guardrails = MagicMock()
    mock_guardrails.validate.return_value = {
        "allowed": False,
        "reason": "Off-topic request.",
    }
    mock_engine = MagicMock()

    result = query("tell me a joke", mock_guardrails, mock_engine)

    assert result["blocked"] is True
    assert "I can't help with that" in result["response"]
    assert "Off-topic request." in result["response"]
    mock_engine.query.assert_not_called()


def test_query_returns_structured_response_when_guardrails_allow():
    """query() must return the engine response with source nodes when input passes guardrails."""
    verdict = {"allowed": True, "reason": ""}
    mock_guardrails = MagicMock()
    mock_guardrails.validate.return_value = verdict

    mock_node = MagicMock()
    mock_node.node.text = "Parking is available on level 2."
    mock_node.score = 0.92

    mock_response = MagicMock()
    mock_response.__str__ = lambda self: "Level 2 has free spaces."
    mock_response.source_nodes = [mock_node]

    mock_engine = MagicMock()
    mock_engine.query.return_value = mock_response

    result = query("where can I park?", mock_guardrails, mock_engine)

    assert result["blocked"] is False
    assert result["response"] == "Level 2 has free spaces."
    assert len(result["source_nodes"]) == 1
    assert result["source_nodes"][0]["score"] == 0.92
    mock_engine.query.assert_called_once_with("where can I park?")
