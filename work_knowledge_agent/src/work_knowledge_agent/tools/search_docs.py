"""Tool: search_docs

Tag: reusable-asset

Purpose:
- Search document corpus with query and optional metadata filters.

Status:
- Placeholder module. Implementation scheduled in retrieval phase.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalConfig, RetrievalHit, retrieve


def search_docs(
	query: str,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	top_k: int = 8,
	min_metadata_confidence: float = 0.30,
	allowed_confidentiality: tuple[str, ...] = ("public", "internal", "confidential"),
) -> List[RetrievalHit]:
	config = RetrievalConfig(
		top_k=top_k,
		min_metadata_confidence=min_metadata_confidence,
		allowed_confidentiality=allowed_confidentiality,
	)
	return retrieve(
		query=query,
		chunks_path=chunks_path,
		metadata_path=metadata_path,
		keyword_index_path=keyword_index_path,
		vector_index_path=vector_index_path,
		config=config,
	)

