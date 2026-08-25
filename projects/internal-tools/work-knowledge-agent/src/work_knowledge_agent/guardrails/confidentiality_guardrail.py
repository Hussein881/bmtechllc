"""Confidentiality filtering for retrieval hits."""

from __future__ import annotations

from typing import Iterable, List

from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit


def filter_by_confidentiality(
	hits: Iterable[RetrievalHit],
	allowed_levels: tuple[str, ...] = ("public", "internal", "confidential"),
) -> List[RetrievalHit]:
	allowed = {level.lower() for level in allowed_levels}
	filtered: List[RetrievalHit] = []
	for hit in hits:
		level = str(hit.metadata.get("confidentiality_level", "internal")).lower()
		if level in allowed:
			filtered.append(hit)
	return filtered
