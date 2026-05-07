"""Graph topology definition."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.memory.state import ParkingState
from src.graph.edges import (
    route_intent,
    route_after_hitl,
    route_after_persist,
    check_reservation_complete,
)


def build_graph(
    *,
    router_node,
    chatbot_node,
    reservation_node,
    approval_request_node,
    hitl_node,
    persist_node,
    approve_response_node,
    reject_response_node,
    persistence_failure_response_node,
    checkpointer=None,
):
    if checkpointer is None:
        checkpointer = MemorySaver()

    builder = StateGraph(ParkingState)

    builder.add_node("router", router_node)
    builder.add_node("chatbot", chatbot_node)
    builder.add_node("reservation", reservation_node)
    builder.add_node("approval_request", approval_request_node)
    builder.add_node("hitl", hitl_node)

    builder.add_node("persist_reservation", persist_node)

    builder.add_node("approve_response", approve_response_node)
    builder.add_node("reject_response", reject_response_node)
    builder.add_node(
        "persistence_failure_response",
        persistence_failure_response_node,
    )

    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        route_intent,
        {
            "info": "chatbot",
            "reservation": "reservation",
        },
    )

    builder.add_edge("chatbot", END)
    builder.add_conditional_edges(
        "reservation",
        check_reservation_complete,
        {
            "collecting": END,
            "pending_approval": "approval_request",
            "approved": END,
            "rejected": END,
        },
    )
    builder.add_edge("approval_request", "hitl")

    builder.add_conditional_edges(
        "hitl",
        route_after_hitl,
        {
            "approved": "persist_reservation",
            "rejected": "reject_response",
        },
    )

    builder.add_conditional_edges(
        "persist_reservation",
        route_after_persist,
        {
            "success": "approve_response",
            "failed": "persistence_failure_response",
        },
    )

    builder.add_edge("approve_response", END)
    builder.add_edge("reject_response", END)
    builder.add_edge("persistence_failure_response", END)

    return builder.compile(checkpointer=checkpointer, interrupt_before=["hitl"])
