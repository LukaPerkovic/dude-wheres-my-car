"""Guardrails for the RAG router — off-topic filtering & prompt injection detection.

Off-topic: cosine similarity between query and domain anchors (reuses bge-small-en-v1.5).
Injection: NLI entailment scoring with cross-encoder/nli-deberta-v3-small.
"""

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from src.config import Settings

settings = Settings()  # type: ignore

TOPIC_ANCHORS = [
    "parking space availability and pricing",
    "how to book a parking spot",
    "parking rules and regulations",
    "parking lot locations and directions",
    "parking fees and payment methods",
    "cancel or modify a parking reservation",
    "parking hours and time limits",
    "electric vehicle charging at a parking facility",
    "disabled parking permits and accessibility",
    "parking garage capacity and real-time occupancy",
]

INJECTION_HYPOTHESES = [
    "This text attempts to override or ignore previous instructions.",
    "This text tries to make the system act as a different persona.",
    "This text requests disclosure of system prompts or internal configuration.",
    "This text contains instructions disguised as a user question.",
    "This text attempts to bypass content or safety policies.",
]


class GuardrailsEngine:
    """Lightweight, local-only guardrails — no API calls required.

    Parameters
    ----------
    embedding_model : SentenceTransformer | None
        Pass an already-loaded model to avoid duplicating bge-small in memory.
    topic_threshold : float
        Minimum cosine similarity to the closest anchor to be considered on-topic.
    injection_threshold : float
        Minimum entailment probability to flag as prompt injection.
    """

    def __init__(
        self,
        embedding_model: SentenceTransformer | None = None,
        topic_threshold: float = 0.32,
        injection_threshold: float = 0.70,
    ):
        self.embedding_model = embedding_model or SentenceTransformer(
            settings.embedding_model
        )

        self.nli_model = CrossEncoder(settings.guardrails_model)

        self.topic_threshold = topic_threshold
        self.injection_threshold = injection_threshold

        self._anchor_embeddings = self.embedding_model.encode(
            TOPIC_ANCHORS, normalize_embeddings=True
        )

    def check_off_topic(self, query: str) -> dict:
        """Return similarity info; flag if below threshold."""
        query_vec = self.embedding_model.encode(query, normalize_embeddings=True)
        similarities = self._anchor_embeddings @ query_vec  # (N,)
        best_idx = int(np.argmax(similarities))
        max_sim = float(similarities[best_idx])

        return {
            "is_off_topic": max_sim < self.topic_threshold,
            "max_similarity": round(max_sim, 4),
            "closest_anchor": TOPIC_ANCHORS[best_idx],
        }

    def check_injection(self, query: str) -> dict:
        """Use NLI entailment to detect injection attempts.

        Model labels for cross-encoder/nli-deberta-v3-small:
            0 → contradiction, 1 → entailment, 2 → neutral
        """
        pairs = [(query, h) for h in INJECTION_HYPOTHESES]
        logits = self.nli_model.predict(pairs)  # shape (N, 3)

        probs = self._softmax(np.array(logits))
        entailment_probs = probs[:, 1]  # column 1 = entailment
        best_idx = int(np.argmax(entailment_probs))
        max_entailment = float(entailment_probs[best_idx])

        is_injection = max_entailment > self.injection_threshold

        return {
            "is_injection": is_injection,
            "max_entailment_score": round(max_entailment, 4),
            "triggered_hypothesis": (
                INJECTION_HYPOTHESES[best_idx] if is_injection else None
            ),
        }

    def validate(self, query: str) -> dict:
        """Run all checks; return structured verdict."""
        injection = self.check_injection(query)
        # Short-circuit: injection is higher severity
        if injection["is_injection"]:
            return {
                "allowed": False,
                "reason": "Potential prompt injection detected.",
                "injection": injection,
                "off_topic": None,
            }

        off_topic = self.check_off_topic(query)
        if off_topic["is_off_topic"]:
            return {
                "allowed": False,
                "reason": "Query is off-topic for this parking assistant.",
                "injection": injection,
                "off_topic": off_topic,
            }

        return {
            "allowed": True,
            "reason": None,
            "injection": injection,
            "off_topic": off_topic,
        }

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        e = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e / e.sum(axis=-1, keepdims=True)
