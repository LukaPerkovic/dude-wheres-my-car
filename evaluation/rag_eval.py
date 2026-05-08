"""Module for RAG retrieval evaluation"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from src.rag.retriever import build_pipeline, PipelineConfig, query

_IS_EVAL = True


def load_dataset(path: str) -> List[Dict[str, Any]]:
    lines = Path(path).read_text().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def normalize(s: str) -> str:
    return " ".join(s.lower().split())


def fuzzy_contains(text: str, ref: str, min_overlap: float = 0.5) -> bool:
    text_n, ref_n = normalize(text), normalize(ref)
    if ref_n in text_n:  # direct substring hit
        return True
    t_words = set(text_n.split())
    r_words = set(ref_n.split()) - {
        "a",
        "an",
        "the",
        "is",
        "are",
        "by",
        "in",
        "of",
        "to",
        "you",
        "can",
        "my",
    }
    if not r_words:
        return False
    return len(t_words & r_words) / len(r_words) >= min_overlap


# Evaluation for RAG based on retrieval ONLY
# Consists of precision, recall, and Mean Reciprocal Rank (MRR)
def run_rag_evaluation(
    dataset: List[Dict[str, Any]],
    guardrails,
    engine,
    k: int = 3,
):
    per_question = []
    recalls, precisions, mrrs = [], [], []

    for row in dataset:
        out = query(row["question"], guardrails, engine, is_eval=_IS_EVAL)

        refs = row["reference"]
        refs = [refs] if isinstance(refs, str) else refs

        recall: float = 0.0
        precision: float = 0.0
        mrr: float = 0.0

        source_type = row.get("source_type", "vector")

        if out.get("blocked"):
            # blocked queries score 0 across the board
            pass

        elif source_type == "sql":
            response_text = (out.get("response") or "").lower()
            # Normalize numbers and separators
            norm_response = response_text.replace(",", "").replace("_", " ")
            hit = any(
                r.lower().replace(",", "").replace("_", " ") in norm_response
                for r in refs
            )

        else:  # vector
            nodes = out.get("source_nodes") or []
            if nodes:
                texts = [n["text"].lower() for n in nodes[:k]]
                rel = [any(fuzzy_contains(t, r) for r in refs) for t in texts]

                if any(rel):
                    recall = 1.0
                    precision = sum(rel) / min(k, len(nodes))
                    rank = rel.index(True) + 1
                    mrr = 1.0 / rank

        recalls.append(recall)
        precisions.append(precision)
        mrrs.append(mrr)

        per_question.append(
            {
                "id": row["id"],
                "source_type": source_type,
                "recall": recall,
                "precision": precision,
                "mrr": mrr,
            }
        )

    # Optional: also break out aggregates by source type for clearer diagnostics
    def _avg(values):
        return float(np.mean(values)) if values else 0.0

    vec_idx = [i for i, r in enumerate(dataset) if r.get("source_type") != "sql"]
    sql_idx = [i for i, r in enumerate(dataset) if r.get("source_type") == "sql"]

    return {
        "recall@k": _avg(recalls),
        "precision@k": _avg(precisions),
        "mrr": _avg(mrrs),
        "by_source_type": {
            "vector": {
                "recall@k": _avg([recalls[i] for i in vec_idx]),
                "precision@k": _avg([precisions[i] for i in vec_idx]),
                "mrr": _avg([mrrs[i] for i in vec_idx]),
                "n": len(vec_idx),
            },
            "sql": {
                "recall@k": _avg([recalls[i] for i in sql_idx]),
                "precision@k": _avg([precisions[i] for i in sql_idx]),
                "mrr": _avg([mrrs[i] for i in sql_idx]),
                "n": len(sql_idx),
            },
        },
        "per_question": per_question,
    }


# NOTE: Ragas could be used for additional and improved RAG evaluation
#       but is skipped due to increased costs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/rag_golden_dataset.jsonl")
    parser.add_argument("--output", default="evaluation/report.json")
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--chunk_size", type=int, default=256)
    parser.add_argument("--parser_type", default="window_mode")
    parser.add_argument("--use_window", action="store_true")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset)

    config = PipelineConfig(
        parser_type=args.parser_type,
        chunk_size=args.chunk_size,
        similarity_top_k=args.top_k,
        use_window=args.use_window,
    )

    guardrails, engine = build_pipeline(config)

    report = run_rag_evaluation(dataset, guardrails, engine, k=args.top_k)

    Path(args.output).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
