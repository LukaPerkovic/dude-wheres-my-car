"""LlamaIndex document loading and chunking."""

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.anthropic import Anthropic

from src.config import Settings

settings = Settings()  # type: ignore


def initialize_llama_settings():
    """Configure LlamaIndex global variables"""
    LlamaSettings.llm = Anthropic(
        model=settings.rag_model,
        api_key=settings.anthropic_api_key,
    )

    LlamaSettings.embed_model = HuggingFaceEmbedding(
        model_name=settings.embedding_model
    )


def load_and_chunk_documents(
    data_dir: str = "data/static", chunk_size: int = 256, chunk_overlap: int = 50
):
    """Load the markdown files and split it into chunks"""
    documents = SimpleDirectoryReader(data_dir).load_data()
    parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes = parser.get_nodes_from_documents(documents)
    return nodes


def build_vector_index(nodes):
    """Build a ChromaDB-backed vector index from nodes"""
    index = VectorStoreIndex(nodes)
    return index
