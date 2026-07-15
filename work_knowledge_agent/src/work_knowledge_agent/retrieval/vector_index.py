"""Vector index loader and scoring for tfidf-lite artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable


def load_vector_index(index_path: Path) -> dict:
	if not index_path.exists():
		return {"model": "tfidf-lite", "vectors": {}}
	with index_path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def score_vector(query_tokens: Iterable[str], index_payload: dict) -> Dict[str, float]:
	vectors = index_payload.get("vectors", {})
	query_counts = Counter(token for token in query_tokens if token)
	if not query_counts:
		return {}

	raw_scores: Dict[str, float] = {}
	for chunk_id, payload in vectors.items():
		weights = payload.get("weights", {})
		score = 0.0
		for token, q_tf in query_counts.items():
			score += float(weights.get(token, 0.0)) * float(q_tf)
		if score > 0:
			raw_scores[chunk_id] = score

	if not raw_scores:
		return {}
	max_score = max(raw_scores.values())
	if max_score <= 0:
		return {chunk_id: 0.0 for chunk_id in raw_scores}
	return {chunk_id: score / max_score for chunk_id, score in raw_scores.items()}
