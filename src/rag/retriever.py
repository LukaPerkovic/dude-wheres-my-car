"""Single entrypoint that wires guardrails → router → response."""

from sentence_transformers import SentenceTransformer

from dataclasses import dataclass, field
from src.config import Settings
from src.rag.guardrails import GuardrailsEngine
from src.rag.query_engine import create_hybrid_query_engine, initialize_llama_settings

settings = Settings()  # type: ignore


@dataclass
class PipelineConfig:
    parser_type: str = "sentence_splitter"
    chunk_size: int = 256
    similarity_top_k: int = 3
    use_window: bool = False
    parser_kwargs: dict = field(default_factory=dict)


def build_pipeline(config: PipelineConfig):
    initialize_llama_settings()

    _shared_embedder = SentenceTransformer(settings.embedding_model)
    guardrails = GuardrailsEngine(embedding_model=_shared_embedder)

    query_engine = create_hybrid_query_engine(
        vector_args={
            "parser_type": config.parser_type,
            "similarity_top_k": config.similarity_top_k,
            "use_window": config.use_window,
            **config.parser_kwargs,
        }
    )

    return guardrails, query_engine


def query(
    user_input: str, guardrails: GuardrailsEngine, engine, is_eval: bool = False
) -> dict:

    verdict = {"allowed": True, "reason": None} # Default
    
    # Evaluation skips guardrails to avoid noise
    if not is_eval:
        verdict = guardrails.validate(user_input)

        if not verdict["allowed"]:
            return {
                "response": f"I can't help with that. {verdict['reason']}",
                "blocked": True,
                "guardrails": verdict,
            }

    response = engine.query(user_input)

    return {
        "response": str(response),
        "blocked": False,
        "source_nodes": [
            {
                "text": node.node.text[:200] if not is_eval else node.node.text,
                "score": node.score,
            }
            for node in response.source_nodes
        ],
        "guardrails": verdict,
    }
