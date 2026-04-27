"""Query engine that will search for input terms across vector DB"""

from src.rag.indexer import (
    initialize_llama_settings,
    load_and_chunk_documents,
    build_vector_index,
)


def create_query_engine(similarity_top_k: int = 3):
    """Build the full RAG pipeline and return a query engine."""
    initialize_llama_settings()
    nodes = load_and_chunk_documents()
    index = build_vector_index(nodes)
    query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
    return query_engine
