from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage


def test_chatbot_node_returns_ai_message():
    from src.agents.chatbot import make_chatbot_node

    with patch(
        "src.agents.chatbot.query", return_value={"response": "Open 24/7."}
    ) as mock_q:
        node = make_chatbot_node(guardrails=MagicMock(), engine=MagicMock())
        result = node({"messages": [HumanMessage(content="What are the hours?")]})

    assert isinstance(result["messages"][0], AIMessage)
    assert result["messages"][0].content == "Open 24/7."
    mock_q.assert_called_once()
