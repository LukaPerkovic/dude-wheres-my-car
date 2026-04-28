"""Query engine that will search for input terms across vector DB"""

from llama_index.core.postprocessor import (
    MetadataReplacementPostProcessor,
    SentenceTransformerRerank,
)
from sqlalchemy import create_engine
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine, RouterQueryEngine
from llama_index.core.selectors import PydanticSingleSelector
from llama_index.core.tools import QueryEngineTool


from src.config import Settings
from src.rag.indexer import (
    initialize_llama_settings,
    load_and_chunk_documents,
    build_vector_index,
)


settings = Settings()  # type: ignore


def create_vector_query_engine(
    similarity_top_k: int = 3, use_window: bool = False, **kwargs
):
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


def create_sql_query_engine():
    # SQLAlchemy engine — just a connection, no ORM
    engine = create_engine(f"sqlite:///{settings.sqlite_db_path}")

    # LlamaIndex wrapper that inspects the schema automatically
    sql_database = SQLDatabase(engine)

    # Natural language → SQL → result
    return NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=["spaces"],
    )


def create_hybrid_query_engine(vector_args: dict = {}, sql_args: dict = {}):
    """
    RouterQueryEngine picks ONE tool per query based on descriptions.
    PydanticSingleSelector uses structured output for reliable tool selection —
    more deterministic than plain LLMSingleSelector.
    """

    initialize_llama_settings()

    tools = [
        QueryEngineTool.from_defaults(
            query_engine=create_vector_query_engine(**vector_args),
            name="vector_search",
            description=(
                "for questions about parking rules, locations, booking process, general information"
            ),
        ),
        QueryEngineTool.from_defaults(
            query_engine=create_sql_query_engine(**sql_args),
            name="sql_search",
            description=(
                "for questions about current availability, live pricing, real-time space count"
            ),
        ),
    ]

    return RouterQueryEngine(
        selector=PydanticSingleSelector.from_defaults(),
        query_engine_tools=tools,
        verbose=True,
    )
