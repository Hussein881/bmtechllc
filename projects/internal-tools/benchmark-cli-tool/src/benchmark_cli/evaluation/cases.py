"""Frozen Week 2 evaluation cases loaded from a reviewed, corpus-grounded file.

The repository intentionally contains no Discord export or meeting transcript.
Supplying fabricated cross-source questions would make the benchmark look
complete while measuring nothing. Add the reviewed case file named below after
ingestion, then commit it before similarity-threshold tuning.
"""

from __future__ import annotations

import json

from ..paths import PROJECT_ROOT
from .runner import EvalCase

CASES_PATH = PROJECT_ROOT / "data" / "eval_cases_week2.json"


def load_week2_cases() -> tuple[EvalCase, ...]:
    """Load ten reviewed cases, or fail with an actionable corpus prerequisite."""
    if not CASES_PATH.is_file():
        raise RuntimeError(
            "Week 2 evaluation is data-gated: add reviewed week2_cases.json with 5 easy lookups, "
            "3 genuine cross-source cases, and 2 near-miss out-of-corpus cases after corpus ingestion."
        )
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or len(payload) != 10:
        raise RuntimeError("week2_cases.json must contain exactly 10 frozen evaluation cases.")
    cases = tuple(EvalCase(**item) for item in payload)
    categories = [case.category for case in cases]
    if categories.count("easy-lookup") != 5 or categories.count("cross-source") != 3 or categories.count("out-of-corpus") != 2:
        raise RuntimeError("Week 2 cases must be 5 easy-lookup, 3 cross-source, and 2 out-of-corpus.")
    if any(case.expected_tier != "cheap" for case in cases if case.category == "easy-lookup"):
        raise RuntimeError("Every easy lookup must expect the cheap tier.")
    if any(case.expected_tier != "flagship" for case in cases if case.category == "cross-source"):
        raise RuntimeError("Every cross-source case must expect the flagship tier.")
    if any(case.expected_confidence != 0.0 for case in cases if case.category == "out-of-corpus"):
        raise RuntimeError("Every out-of-corpus case must require confidence 0.0.")
    return cases
