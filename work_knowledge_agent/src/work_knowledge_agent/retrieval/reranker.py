"""Result reranking utilities."""

from __future__ import annotations

from typing import Dict


def rerank_scores(
	combined_scores: Dict[str, float],
	metadata_by_chunk: Dict[str, dict],
	min_metadata_confidence: float,
	allowed_confidentiality: set[str] | None = None,
) -> Dict[str, float]:
	allowed = {level.lower() for level in (allowed_confidentiality or {"public", "internal", "confidential"})}
	reranked: Dict[str, float] = {}
	for chunk_id, score in combined_scores.items():
		metadata = metadata_by_chunk.get(chunk_id, {})
		metadata_confidence = float(metadata.get("metadata_confidence", 0.0))
		if metadata_confidence < min_metadata_confidence:
			continue

		conf_level = str(metadata.get("confidentiality_level", "internal")).lower()
		if conf_level not in allowed:
			continue

		boost = 0.10 * metadata_confidence
		reranked[chunk_id] = score + boost

	if not reranked:
		return {}
	max_score = max(reranked.values())
	if max_score <= 0:
		return {chunk_id: 0.0 for chunk_id in reranked}
	return {chunk_id: score / max_score for chunk_id, score in reranked.items()}
