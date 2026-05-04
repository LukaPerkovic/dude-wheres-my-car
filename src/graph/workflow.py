"""Graph topology definition."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.memory.state import ParkingState
from src.graph.edges import route_intent, check_reservation_complete


def build_graph(
    *,
    router_node,
    chatbot_node,
    reservation_node,
    hitl_node,
    checkpointer=None,
):
    """Construct and compile the parking chatbot state graph.

    Args:
        router_node: Callable[[ParkingState], dict] — intent classifier
        chatbot_node: Callable[[ParkingState], dict] — RAG-backed info agent
        reservation_node: Callable[[ParkingState], dict] — data collection agent
        hitl_node: Callable[[ParkingState], dict] — admin approval agent
        checkpointer: LangGraph checkpointer instance. Defaults to MemorySaver.

    Returns:
        Compiled LangGraph StateGraph, ready for .invoke()
    """

    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(ParkingState)


    builder.add_node("router", router_node)
    builder.add_node("chatbot", chatbot_node)
    builder.add_node("reservation", reservation_node)
    builder.add_node("hitl", hitl_node)

    builder.add_edge(START, "router")
    
    builder.add_conditional_edges(
        "router",
        route_intent,
        {
            "info": "chatbot",
            "reservation": "reservation",
        }
    )

    builder.add_edge("chatbot", END)

    builder.add_conditional_edges(
        "reservation",
        check_reservation_complete,
        {
            "collecting": END,
            "pending_approval": "hitl",
        }
    )

    builder.add_edge("hitl", END)

    return builder.compile(checkpointer=checkpointer)