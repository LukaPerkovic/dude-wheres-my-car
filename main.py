import atexit
import sqlite3

from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.sqlite import SqliteSaver

from src.config import Settings
from src.rag.retriever import build_pipeline, PipelineConfig
from src.agents.chatbot import make_chatbot_node
from src.agents.reservation import ReservationAgent
from src.agents.hitl import HITLAgent
from src.agents.approval_request import ApprovalRequestNode
from src.graph.nodes import RouterNode
from src.graph.workflow import build_graph
from src.graph.post_approval_nodes import (
    PersistReservationNode,
    approve_response_node,
    reject_response_node,
    persistence_failure_response_node,
)
from src.persistence.file_writer import LocalReservationWriter


settings = Settings()

router_llm = ChatAnthropic(
    model=settings.router_model,
    api_key=settings.anthropic_api_key,
    max_tokens=10,
)

agent_llm = ChatAnthropic(
    model=settings.agent_model,
    api_key=settings.anthropic_api_key,
    max_tokens=512,
)

guardrails, query_engine = build_pipeline(PipelineConfig())


class LoggingNotificationChannel:
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

approval_request = ApprovalRequestNode(notification_channel=notification_channel)
hitl = HITLAgent()

writer = LocalReservationWriter(settings.approved_reservations_file)
persist_reservation = PersistReservationNode(writer=writer)

sqlite_conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
atexit.register(sqlite_conn.close)

checkpointer = SqliteSaver(sqlite_conn)

graph = build_graph(
    router_node=router,
    chatbot_node=chatbot,
    reservation_node=reservation,
    approval_request_node=approval_request,
    hitl_node=hitl,
    persist_node=persist_reservation,
    approve_response_node=approve_response_node,
    reject_response_node=reject_response_node,
    persistence_failure_response_node=persistence_failure_response_node,
    checkpointer=checkpointer,
)