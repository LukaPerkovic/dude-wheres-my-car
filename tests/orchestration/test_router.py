from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage
import pytest


@pytest.fixture
def router_node():
    from src.graph.nodes import RouterNode
    return RouterNode(MagicMock())


def test_router_skips_llm_when_collecting(router_node):
    result = router_node({"reservation_status": "collecting", "messages": [HumanMessage(content="hi")]})

    assert result["intent"] == "reservation"
    router_node.llm.invoke.assert_not_called()


def test_router_uses_llm_for_fresh_message():
    from src.graph.nodes import RouterNode

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="  reservation  ")
    result = RouterNode(llm)({"reservation_status": None, "messages": [HumanMessage(content="Book a spot")]})

    assert result["intent"] == "reservation"


def test_router_defaults_unknown_llm_response_to_info():
    from src.graph.nodes import RouterNode

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="i_have_no_idea")
    result = RouterNode(llm)({"reservation_status": None, "messages": [HumanMessage(content="?")]})

    assert result["intent"] == "info"