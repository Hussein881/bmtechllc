"""Hybrid retriever for Phase 2 baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from work_knowledge_agent.retrieval.keyword_index import load_keyword_index, score_keyword
from work_knowledge_agent.retrieval.query_rewriter import rewrite_query
from work_knowledge_agent.retrieval.reranker import rerank_scores
from work_knowledge_agent.retrieval.vector_index import load_vector_index, score_vector


@dataclass(frozen=True)
class RetrievalHit:
	chunk_id: str
	score: float
	content: str
	metadata: dict


@dataclass(frozen=True)
class RetrievalConfig:
	top_k: int = 8
	keyword_weight: float = 0.45
	vector_weight: float = 0.55
	min_metadata_confidence: float = 0.30
	allowed_confidentiality: tuple[str, ...] = ("public", "internal", "confidential")


def _load_chunks(chunks_path: Path) -> Dict[str, dict]:
	rows: Dict[str, dict] = {}
	if not chunks_path.exists():
		return rows
	with chunks_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			row = json.loads(line)
			chunk_id = str(row.get("chunk_id", "")).strip()
			if not chunk_id:
				continue
			rows[chunk_id] = row
	return rows


def _load_metadata(metadata_path: Path) -> Dict[str, dict]:
	rows: Dict[str, dict] = {}
	if not metadata_path.exists():
		return rows
	with metadata_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			row = json.loads(line)
			chunk_id = str(row.pop("chunk_id", "")).strip()
			if not chunk_id:
				continue
			rows[chunk_id] = row
	return rows


def retrieve(
	query: str,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: RetrievalConfig | None = None,
) -> List[RetrievalHit]:
	cfg = config or RetrievalConfig()
	rewritten = rewrite_query(query)
	if not rewritten.tokens:
		return []

	chunks_by_id = _load_chunks(chunks_path)
	metadata_by_id = _load_metadata(metadata_path)
	keyword_payload = load_keyword_index(keyword_index_path)
	vector_payload = load_vector_index(vector_index_path)

	keyword_scores = score_keyword(rewritten.tokens, keyword_payload)
	vector_scores = score_vector(rewritten.tokens, vector_payload)

	all_chunk_ids = set(keyword_scores) | set(vector_scores)
	combined_scores: Dict[str, float] = {}
	for chunk_id in all_chunk_ids:
		combined_scores[chunk_id] = (
			cfg.keyword_weight * keyword_scores.get(chunk_id, 0.0)
			+ cfg.vector_weight * vector_scores.get(chunk_id, 0.0)
		)

	reranked_scores = rerank_scores(
		combined_scores,
		metadata_by_chunk=metadata_by_id,
		min_metadata_confidence=cfg.min_metadata_confidence,
		allowed_confidentiality=set(cfg.allowed_confidentiality),
	)

	ranked_ids = sorted(reranked_scores, key=reranked_scores.get, reverse=True)[: cfg.top_k]
	hits: List[RetrievalHit] = []
	for chunk_id in ranked_ids:
		chunk_row = chunks_by_id.get(chunk_id)
		if not chunk_row:
			continue
		metadata = metadata_by_id.get(chunk_id) or chunk_row.get("metadata", {})
		hits.append(
			RetrievalHit(
				chunk_id=chunk_id,
				score=float(reranked_scores.get(chunk_id, 0.0)),
				content=str(chunk_row.get("content", "")),
				metadata=metadata,
			)
		)
	return hits
