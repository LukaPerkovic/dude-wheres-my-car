"""Unit tests for src.rag.indexer"""

from unittest.mock import MagicMock, patch

import pytest


def test_load_and_chunk_raises_for_unknown_parser():
    """Unknown parser_type must raise a descriptive ValueError."""
    with patch("src.rag.indexer.SimpleDirectoryReader") as mock_reader:
        mock_reader.return_value.load_data.return_value = [MagicMock()]

        from src.rag.indexer import load_and_chunk_documents

        with pytest.raises(ValueError, match="Unknown parser type: bad_parser"):
            load_and_chunk_documents(parser_type="bad_parser")


def test_load_and_chunk_returns_nodes_for_valid_parser():
    """sentence_splitter path should return exactly the nodes the parser produces."""
    expected_nodes = [MagicMock(), MagicMock()]

    mock_parser_instance = MagicMock()
    mock_parser_instance.get_nodes_from_documents.return_value = expected_nodes
    mock_parser_cls = MagicMock(return_value=mock_parser_instance)

    with (
        patch("src.rag.indexer.SimpleDirectoryReader") as mock_reader,
        patch.dict(
            "src.rag.indexer.parsers_map", {"sentence_splitter": mock_parser_cls}
        ),
    ):

        mock_reader.return_value.load_data.return_value = [MagicMock()]

        from src.rag.indexer import load_and_chunk_documents

        result = load_and_chunk_documents(parser_type="sentence_splitter")

    assert result == expected_nodes
    mock_parser_cls.assert_called_once()
