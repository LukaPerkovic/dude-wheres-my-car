from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage

from src.memory.state import ParkingState

ROUTER_SYSTEM = (
    "Classify the user's intent as exactly one of these words:\n"
    " - 'info' user asks about parking details, location, prices, hours, rules\n"
    "- - 'reservation' - user wants to book or reserve a parking spot\n\n"
    "Reply with ONLY that one word, nothing else."
)

class RouterNode:
    """Classifies user intent. Stays in reservation flow if already collecting."""

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm

    
    def __call__(self, state: ParkingState) -> dict:
        if state.get("reservation_status") == "collecting":
            return {"intent": "reservation"}

        response = self.llm.invoke(
            [
                SystemMessage(content=ROUTER_SYSTEM),
                state["messages"][-1]
            ]
        )

        intent = response.content.strip().lower()
        if intent not in ("info", "reservation"):
            intent = "info"
        
        return {"intent": intent}
