from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.main import graph

app = FastAPI(title="Neo-Terra Parking Assistant")


class ChatRequest(BaseModel):
    message: str
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    is_waiting_for_admin: bool = False


class AdminDecision(BaseModel):
    approved: bool
    reason: str = ""


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    state = graph.get_state(config)

    if state.next:
        return ChatResponse(
            response="Your reservation is pending admin approval. Please wait.",
            is_waiting_for_admin=True,
        )

    result = graph.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config,
    )

    new_state = graph.get_state(config)
    is_waiting = bool(new_state.next)

    return ChatResponse(
        response=result["messages"][-1].content,
        is_waiting_for_admin=is_waiting
    )

@app.post("/reservations/{thread_id}/approve")
def approve_reservation(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    state = graph.get_state(config)
    if not state.next:
        raise HTTPException(404, "No pending reservations for this thread.")

    result = graph.invoke(
        Command(resume={"approved": True})
    )
    return {"status": "approved", "message": result["messages"][-1].content}



@app.post("/reservations/{thread_id}/reject")
def reject_reservation(thread_id: str, body: AdminDecision = None):
    config = {"configurable": {"thread_id": thread_id}}

    state = graph.get_state(config)
    if not state.next:
        raise HTTPException(404, "No pending reservations for this thread.")

    reason = body.reason if body else "No reason provided."
    result = graph.invoke(
        Command(resume={"approved": False, "reason": reason})
    )
    return {"status": "rejected", "message": result["messages"][-1].content}

