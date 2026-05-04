from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import MemorySaver

from src.config import Settings
from src.rag.retriever import build_pipeline, PipelineConfig
from src.agents.chatbot import make_chatbot_node
from src.agents.reservation import ReservationAgent
from src.agents.hitl import HITLAgent
from src.graph.nodes import RouterNode
from src.graph.workflow import build_graph


settings = Settings()

router_llm = ChatAnthropic(
    model=settings.router_model,
    api_key=settings.anthropic_api_key,
    max_tokens=10
)


agent_llm = ChatAnthropic(
    model=settings.agent_model,
    api_key=settings.anthropic_api_key,
    max_tokens=512 # Better is 1024+ but Anthropic is PRICYYY!
)

guardrails, query_engine = build_pipeline(PipelineConfig())


#PLACEHOLDER
class LoggingNotificationChannel:
    """Placeholder: prints to stdout. Swap for Discord/Teams/email."""

    def send_approval_request(self, reservation_id: str, details: dict) -> bool:
        print(f"\n{'='*50}")
        print(" ADMIN APPROVAL REQUEST")
        print(f"   Reservation ID: {reservation_id}")
        print(f"   Name: {details.get('name')} {details.get('surname')}")
        print(f"   Plate: {details.get('car_plate')}")
        print(f"   Dates: {details.get('date_start')} → {details.get('date_end')}")
        print(f"{'='*50}\n")
        return True

notification_channel = LoggingNotificationChannel()

router = RouterNode(llm=router_llm)
chatbot = make_chatbot_node(guardrails, query_engine)
reservation = ReservationAgent(llm=agent_llm)
hitl = HITLAgent(notification_channel=notification_channel)

graph = build_graph(
    router_node=router,
    chatbot_node=chatbot,
    reservation_node=reservation,
    hitl_node=hitl,
    checkpointer=MemorySaver()
)