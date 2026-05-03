from langchain_core.messages import AIMessage
from src.memory.state import ParkingState
from src.rag.pipeline import query, GuardrailsEngine

def make_chatbot_node(guardrails: GuardrailsEngine, engine):
    def chatbot_node(state: ParkingState) -> dict:
        user_msg = state["messages"][-1].content
        result = query(user_msg, guardrails, engine)

        return {"messages": [AIMessage(content=result["response"])]}

    return chatbot_node
