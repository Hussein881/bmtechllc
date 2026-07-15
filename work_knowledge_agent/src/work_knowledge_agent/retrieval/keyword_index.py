"""Keyword index loader and lexical scoring utilities."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable


def load_keyword_index(index_path: Path) -> dict:
	if not index_path.exists():
		return {"postings": {}}
	with index_path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def score_keyword(query_tokens: Iterable[str], index_payload: dict) -> Dict[str, float]:
	inverted_index = index_payload.get("inverted_index")
	if isinstance(inverted_index, dict) and inverted_index:
		return _score_keyword_bm25(query_tokens, index_payload)
	return _score_keyword_legacy(query_tokens, index_payload)


def _score_keyword_legacy(query_tokens: Iterable[str], index_payload: dict) -> Dict[str, float]:
	postings = index_payload.get("postings", {})
	scores: Counter[str] = Counter()
	for token in query_tokens:
		for chunk_id in postings.get(token, []):
			scores[chunk_id] += 1.0

	if not scores:
		return {}
	max_score = max(scores.values())
	if max_score <= 0:
		return {chunk_id: 0.0 for chunk_id in scores}
	return {chunk_id: score / max_score for chunk_id, score in scores.items()}


def _score_keyword_bm25(query_tokens: Iterable[str], index_payload: dict) -> Dict[str, float]:
	inverted_index = index_payload.get("inverted_index", {})
	doc_lengths = index_payload.get("doc_lengths", {})
	total_docs = int(index_payload.get("total_docs", max(1, len(doc_lengths))))
	avgdl = float(index_payload.get("avgdl", 1.0) or 1.0)
	k1 = float(index_payload.get("k1", 1.2))
	b = float(index_payload.get("b", 0.75))
	doc_freq = index_payload.get("doc_freq", {})

	q_counts = Counter(token for token in query_tokens if token)
	raw_scores: Counter[str] = Counter()
	for token, qtf in q_counts.items():
		doc_tf = inverted_index.get(token, {})
		if not doc_tf:
			continue
		df = int(doc_freq.get(token, len(doc_tf)))
		idf = math.log(((total_docs - df + 0.5) / (df + 0.5)) + 1.0)
		for chunk_id, tf_val in doc_tf.items():
			dl = int(doc_lengths.get(chunk_id, 0))
			tf = float(tf_val)
			denom = tf + k1 * (1.0 - b + b * (dl / avgdl if avgdl > 0 else 1.0))
			if denom <= 0:
				continue
			contrib = idf * ((tf * (k1 + 1.0)) / denom) * float(qtf)
			raw_scores[chunk_id] += contrib

	if not raw_scores:
		return {}
	max_score = max(raw_scores.values())
	if max_score <= 0:
		return {chunk_id: 0.0 for chunk_id in raw_scores}
	return {chunk_id: score / max_score for chunk_id, score in raw_scores.items()}
