"""Command-line runner for retrieval-only golden-dataset evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..config import EVALUATION_LOG_PATH, GOLDEN_DATASET_PATH
from ..retrieval import search_docs, vector_only_search
from .dataset import load_golden_dataset, resolve_golden_dataset
from .metrics import compare_retrieval_modes, comparison_markdown, evaluate_retrieval
from .telemetry import append_evaluation_log


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=GOLDEN_DATASET_PATH)
    parser.add_argument(
        "--metrics-csv",
        type=Path,
        default=EVALUATION_LOG_PATH,
        help=f"Append per-query evaluation metrics to this CSV (default: {EVALUATION_LOG_PATH}).",
    )
    parser.add_argument(
        "--compare-vector",
        action="store_true",
        help="Measure vector-only and hybrid RRF retrieval against the same golden dataset.",
    )
    parser.add_argument(
        "--comparison-report",
        type=Path,
        help="Write the vector-only versus hybrid Recall@5/MRR table to this Markdown file.",
    )
    args = parser.parse_args()
    if args.comparison_report and not args.compare_vector:
        parser.error("--comparison-report requires --compare-vector")
    cases = resolve_golden_dataset(load_golden_dataset(args.dataset))
    if args.compare_vector:
        comparison = compare_retrieval_modes(
            cases,
            vector_search=vector_only_search,
            hybrid_search=search_docs,
        )
        append_evaluation_log(
            args.metrics_csv,
            args.dataset,
            comparison.vector_only,
            retrieval_mode="vector_only",
        )
        append_evaluation_log(
            args.metrics_csv,
            args.dataset,
            comparison.hybrid,
            retrieval_mode="hybrid_rrf",
        )
        payload = comparison.as_dict()
        if args.comparison_report:
            args.comparison_report.parent.mkdir(parents=True, exist_ok=True)
            args.comparison_report.write_text(comparison_markdown(comparison) + "\n", encoding="utf-8")
            payload["comparison_report"] = str(args.comparison_report)
    else:
        summary = evaluate_retrieval(cases, search_docs)
        append_evaluation_log(args.metrics_csv, args.dataset, summary, retrieval_mode="hybrid_rrf")
        payload = summary.as_dict()
    payload["metrics_csv"] = str(args.metrics_csv)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
