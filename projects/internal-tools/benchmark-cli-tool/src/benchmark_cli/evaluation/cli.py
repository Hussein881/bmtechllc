"""Command-line runner for retrieval-only golden-dataset evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..config import EVALUATION_LOG_PATH, GOLDEN_DATASET_PATH
from ..retrieval import hybrid_search
from .dataset import load_golden_dataset, resolve_golden_dataset
from .metrics import evaluate_retrieval
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
    args = parser.parse_args()
    cases = resolve_golden_dataset(load_golden_dataset(args.dataset))
    summary = evaluate_retrieval(cases, hybrid_search)
    append_evaluation_log(args.metrics_csv, args.dataset, summary)
    payload = summary.as_dict()
    payload["metrics_csv"] = str(args.metrics_csv)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
