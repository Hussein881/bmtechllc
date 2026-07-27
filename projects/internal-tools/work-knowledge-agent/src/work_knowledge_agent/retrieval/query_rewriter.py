"""Query normalization and lightweight rewrite helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")
STOP_WORDS = {
	"a",
	"an",
	"and",
	"are",
	"as",
	"at",
	"be",
	"by",
	"for",
	"from",
	"how",
	"i",
	"in",
	"is",
	"it",
	"of",
	"on",
	"or",
	"that",
	"the",
	"to",
	"what",
	"when",
	"where",
	"why",
	"with",
}


@dataclass(frozen=True)
class RewrittenQuery:
	original: str
	normalized: str
	tokens: List[str]


def rewrite_query(query: str) -> RewrittenQuery:
	normalized = " ".join((query or "").strip().split())
	all_tokens = [tok.lower() for tok in TOKEN_RE.findall(normalized)]
	tokens = [tok for tok in all_tokens if tok not in STOP_WORDS]
	if not tokens:
		tokens = all_tokens
	return RewrittenQuery(original=query or "", normalized=normalized, tokens=tokens)
