"""Runs once at startup. Populates Chroma + SQLite."""

from src.rag.indexer import (
    load_and_chunk_documents,
    build_chroma_vector_index,
    get_chroma_vector_store,
    initialize_llama_settings,
)


from sqlalchemy import create_engine, text
from src.config import Settings

settings = Settings()  # type: ignore


def init_chroma():
    """Chunk docs, embed and then store in Chroma. Skips if already populated"""

    vector_store = get_chroma_vector_store()
    if vector_store._collection.count() > 0:
        print(
            f"Chroma already has {vector_store._collection.count()} vectors. Skipping..."
        )
        return

    nodes = load_and_chunk_documents(
        parser_type="window_mode",
        use_window=True,
        window_size=3,
        window_metadata_key="window",
    )

    build_chroma_vector_index(nodes=nodes)
    print(f"Indexed {len(nodes)} chunks into Chroma")


def init_sqllite():
    "Create schema + seed data. Skips if table exists."

    engine = create_engine(f"sqlite:///{settings.sqlite_db_path}")

    # PRAGMAs via SQLAlchemy (single statements, fine here)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.execute(text("PRAGMA busy_timeout=5000;"))

    # Multi-statement script via raw DBAPI connection
    raw_conn = engine.raw_connection()
    try:
        with open("data/dynamic/seed_spaces.sql") as f:
            raw_conn.executescript(f.read())
    finally:
        raw_conn.close()

    print("SQL schema and data ready.")


if __name__ == "__main__":
    init_sqllite()
    initialize_llama_settings()
    init_chroma()
