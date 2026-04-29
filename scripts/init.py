"""Runs once at startup. Populates Chroma + SQLite."""

from src.rag.indexer import (
    initialize_llama_settings,
    load_and_chunk_documents,
    build_chroma_vector_index,
    get_chroma_vector_store,
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

    engine = create_engine(f"sqllite:///{settings.sqlite_db_path}")
    with engine.connect() as conn:
        conn.execute(text("""WIP"""))

        conn.commit()

    print("SQL schema and data ready.")
