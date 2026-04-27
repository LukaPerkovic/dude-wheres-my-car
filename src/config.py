from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    anthropic_api_key: str

    router_model: str = "claude-haiku-4-5-20251001"
    rag_model: str = "claude-sonnet-4-6"
    agent_model: str = "claude-sonnet-4-6"

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    chroma_persist_dir: str = "./chroma_db"
