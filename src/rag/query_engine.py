"""Query engine that will search for input terms across vector DB"""

from src.config import Settings
from src.rag.indexer import (
    initialize_llama_settings,
    load_and_chunk_documents,
    build_vector_index,
)
from llama_index.core.postprocessor import (
    MetadataReplacementPostProcessor,
    SentenceTransformerRerank,
)

settings = Settings()  # type: ignore


def create_query_engine(similarity_top_k: int = 3, use_window: bool = False, **kwargs):
    """Build the full RAG pipeline and return a query engine."""

    initialize_llama_settings()
    nodes = load_and_chunk_documents(**kwargs)
    index = build_vector_index(nodes)

    postprocessors = []
    if use_window:
        postprocessors.append(
            MetadataReplacementPostProcessor(target_metadata_key="window")
        )

    postprocessors.append(
        SentenceTransformerRerank(top_n=3, model=settings.reranker_model)
    )

    query_engine = index.as_query_engine(
        similarity_top_k=similarity_top_k,
        node_postprocessors=postprocessors,
    )
    return query_engine
