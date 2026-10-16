"""Complexity routing for the answer layer."""

from __future__ import annotations

import re
import warnings

from .llm import call_llm

CLASSIFIER_PROMPT = """Classify the question. Reply with exactly EASY or HARD.
EASY is a factual lookup. HARD needs multiple facts, multiple chunks, filters, or synthesis."""


def classify_query(question: str) -> str:
    """Route a question to cheap or flagship, defaulting safely to flagship."""
    if not question.strip():
        raise ValueError("question must not be empty.")
    completion = call_llm(
        tier="cheap",
        component="classifier",
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": question.strip()},
        ],
    )
    content = completion.choices[0].message.content or ""
    match = re.search(r"\b(EASY|HARD)\b", content.upper())
    if match is None:
        warnings.warn("Invalid router label; using flagship.", RuntimeWarning, stacklevel=2)
        return "flagship"
    return "cheap" if match.group(1) == "EASY" else "flagship"
