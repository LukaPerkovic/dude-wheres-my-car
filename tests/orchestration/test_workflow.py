from unittest.mock import MagicMock

def test_build_graph_compiles():
    from src.graph.workflow import build_graph
    from langgraph.checkpoint.memory import MemorySaver

    graph = build_graph(
        router_node=MagicMock(),
        chatbot_node=MagicMock(),
        reservation_node=MagicMock(),
        approval_request_node=MagicMock(),
        hitl_node=MagicMock(),
        persist_node=MagicMock(),
        approve_response_node=MagicMock(),
        reject_response_node=MagicMock(),
        persistence_failure_response_node=MagicMock(),
        checkpointer=MemorySaver(),
    )

    assert graph is not None