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
        if row.get("source_type") != "vector":
            continue

        out = query(row["question"], guardrails, engine, is_eval=_IS_EVAL)

        nodes = out.get("source_nodes") or []
        refs = row["reference"]
        refs = [refs] if isinstance(refs, str) else refs

        recall: float = 0.0
        precision: float = 0.0
        mrr: float = 0.0

        if not out.get("blocked") and nodes:
            texts = [n["text"].lower() for n in nodes[:k]]
            rel = [any(r.lower() in t for r in refs) for t in texts]

            if any(rel):
                recall = 1.0
                precision = sum(rel) / min(k, len(nodes))
                rank = rel.index(True) + 1
                mrr = 1.0 / rank

        recalls.append(recall)
        precisions.append(precision)
        mrrs.append(mrr)

        per_question.append(
            {"id": row["id"], "recall": recall, "precision": precision, "mrr": mrr}
        )

    return {
        "recall@k": float(np.mean(recalls)) if recalls else 0.0,
        "precision@k": float(np.mean(precisions)) if precisions else 0.0,
        "mrr": float(np.mean(mrrs)) if mrrs else 0.0,
        "per_question": per_question,
    }


# NOTE: Ragas could be used for additional and improved RAG evaluation
#       but is skipped due to increased costs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="eval/golden_dataset.jsonl")
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
