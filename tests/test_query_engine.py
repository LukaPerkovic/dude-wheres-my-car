"""Unit tests for src.rag.query_engine"""

from unittest.mock import MagicMock, patch


def test_create_sql_query_engine_targets_spaces_table():
    """NLSQLTableQueryEngine must be initialised with the 'spaces' table."""
    with (
        patch("src.rag.query_engine.create_engine"),
        patch("src.rag.query_engine.SQLDatabase"),
        patch("src.rag.query_engine.NLSQLTableQueryEngine") as mock_nl_cls,
    ):

        mock_nl_cls.return_value = MagicMock()

        from src.rag.query_engine import create_sql_query_engine

        result = create_sql_query_engine()

    mock_nl_cls.assert_called_once()
    _, kwargs = mock_nl_cls.call_args
    assert "spaces" in kwargs.get("tables", [])
    assert result is mock_nl_cls.return_value


def test_create_vector_query_engine_skips_loading_when_collection_has_data():
    """If ChromaDB already holds documents, load_and_chunk_documents must NOT be called."""
    with (
        patch("src.rag.query_engine.initialize_llama_settings"),
        patch("src.rag.query_engine.get_chroma_vector_store") as mock_store,
        patch("src.rag.query_engine.build_chroma_vector_index") as mock_build,
        patch("src.rag.query_engine.load_and_chunk_documents") as mock_load,
        patch("src.rag.query_engine.SentenceTransformerRerank"),
    ):

        mock_store.return_value._collection.count.return_value = 10
        mock_build.return_value.as_query_engine.return_value = MagicMock()

        from src.rag.query_engine import create_vector_query_engine

        result = create_vector_query_engine(parser_type="sentence_splitter")

    mock_load.assert_not_called()
    mock_build.assert_called_once_with(nodes=None)
    assert result is mock_build.return_value.as_query_engine.return_value
