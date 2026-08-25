"""Route questions to the appropriate model tier."""

from __future__ import annotations

import re
import warnings
from typing import Final

from llm import call_llm

CLASSIFIER_PROMPT: Final[str] = """Classify the user's question by complexity.

Reply with exactly one word:
- EASY: a simple factual lookup or a question answerable from one document section.
- HARD: complex reasoning, synthesis across sources, ambiguity, or multi-step analysis.
"""

_VALID_LABELS: Final[dict[str, str]] = {"EASY": "cheap", "HARD": "flagship"}


def classify_query(question: str) -> str:
    """Return ``cheap`` for easy questions and ``flagship`` for hard questions."""
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("question must not be empty.")

    completion = call_llm(
        tier="cheap",
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": normalized_question},
        ],
        component="classifier",
    )
    content = completion.choices[0].message.content or ""
    label_match = re.search(r"\b(EASY|HARD)\b", content.upper())
    if label_match is None:
        warnings.warn(
            f"Query classifier returned an invalid label {content!r}; defaulting to flagship.",
            RuntimeWarning,
            stacklevel=2,
        )
        return "flagship"
    return _VALID_LABELS[label_match.group(1)]
