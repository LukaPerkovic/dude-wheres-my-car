"""LlamaIndex document loading and chunking."""

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter, SentenceWindowNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic

from src.config import Settings

settings = Settings()  # type: ignore

parsers_map = {
    "sentence_splitter": SentenceSplitter,
    "window_mode": SentenceWindowNodeParser,
}


def initialize_llama_settings():
    """Configure LlamaIndex global variables"""
    LlamaSettings.llm = Anthropic(
        model=settings.rag_model,
        api_key=settings.anthropic_api_key,
    )

    LlamaSettings.embed_model = HuggingFaceEmbedding(
        model_name=settings.embedding_model
    )


def load_and_chunk_documents(parser_type: str, data_dir: str = "data/static", **kwargs):
    """Load the markdown files and split it into chunks"""
    documents = SimpleDirectoryReader(data_dir).load_data()
    parser_class = parsers_map.get(parser_type)
    if not parser_class:
        raise ValueError(f"Unknown parser type: {parser_type}")
    parser = parser_class(**kwargs)
    nodes = parser.get_nodes_from_documents(documents)
    return nodes


def build_vector_index(nodes):
    """Build a ChromaDB-backed vector index from nodes"""
    index = VectorStoreIndex(nodes)
    return index
