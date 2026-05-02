from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    anthropic_api_key: str

    router_model: str = "claude-haiku-4-5-20251001"
    rag_model: str = "claude-sonnet-4-6"
    agent_model: str = "claude-sonnet-4-6"

    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    guardrails_model: str = "cross-encoder/nli-deberta-v3-small"

    sqlite_db_path: str = "./parking.db"

    chroma_host: str = "chroma"
    chroma_port: int = 8000
