"""Command-line runner for retrieval-only golden-dataset evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..config import GOLDEN_DATASET_PATH
from ..retrieval import hybrid_search
from .dataset import load_golden_dataset
from .metrics import evaluate_retrieval


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=GOLDEN_DATASET_PATH)
    args = parser.parse_args()
    cases = load_golden_dataset(args.dataset)
    summary = evaluate_retrieval(cases, hybrid_search)
    print(json.dumps(summary.as_dict(), indent=2))


if __name__ == "__main__":
    main()
