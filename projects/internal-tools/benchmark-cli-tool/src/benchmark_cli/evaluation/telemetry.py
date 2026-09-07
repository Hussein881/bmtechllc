"""Append-only CSV logging for retrieval evaluation runs."""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .metrics import EvaluationSummary

CSV_COLUMNS = (
    "run_id",
    "run_at_utc",
    "dataset",
    "question_id",
    "query_category",
    "retrieval_time_ms",
    "generation_time_ms",
    "top_chunk_ids",
    "top_chunk_rrf_scores",
    "top_chunk_vector_similarity_scores",
    "recall_at_5",
    "run_recall_at_5",
    "run_mrr",
)


def append_evaluation_log(path: Path, dataset: Path, summary: EvaluationSummary) -> None:
    """Append one transparent metrics row for every query in an evaluation run.

    This project has no answer-generation stage, so ``generation_time_ms`` is
    intentionally blank rather than reported as zero.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    run_id = uuid4().hex
    run_at = datetime.now(UTC).isoformat()
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS)
        if write_header:
            writer.writeheader()
        for record in summary.per_query:
            writer.writerow(
                {
                    "run_id": run_id,
                    "run_at_utc": run_at,
                    "dataset": str(dataset),
                    "question_id": record.question_id,
                    "query_category": record.query_category,
                    "retrieval_time_ms": f"{record.retrieval_time_ms:.3f}",
                    "generation_time_ms": "",
                    "top_chunk_ids": json.dumps(record.retrieved_chunk_ids),
                    "top_chunk_rrf_scores": json.dumps(record.top_chunk_rrf_scores),
                    "top_chunk_vector_similarity_scores": json.dumps(
                        record.top_chunk_vector_similarity_scores
                    ),
                    "recall_at_5": "" if record.recall_at_5 is None else record.recall_at_5,
                    "run_recall_at_5": summary.recall_at_5,
                    "run_mrr": summary.mrr,
                }
            )
