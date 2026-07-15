"""Curation workflow orchestration for Phase 5 baseline."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from work_knowledge_agent.agents.curator_agent import CurationProposal, build_curation_proposals
from work_knowledge_agent.guardrails.confidentiality_guardrail import filter_by_confidentiality
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit
from work_knowledge_agent.tools.search_docs import search_docs


@dataclass(frozen=True)
class CurationWorkflowConfig:
	top_k: int = 12
	min_metadata_confidence: float = 0.30
	allowed_confidentiality: tuple[str, ...] = ("public", "internal", "confidential")
	min_query_token_coverage: float = 0.40
	duplicate_similarity_threshold: float = 0.92
	outdated_year_cutoff: int = 2021


@dataclass(frozen=True)
class CurationWorkflowResult:
	proposals: List[CurationProposal]
	retrieval_hits: List[RetrievalHit]
	stage_times_ms: dict
	summary: dict


def run_curation_workflow(
	topic: str,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: CurationWorkflowConfig | None = None,
) -> CurationWorkflowResult:
	cfg = config or CurationWorkflowConfig()
	start_total = time.perf_counter()
	start_retrieval = time.perf_counter()
	hits = search_docs(
		query=topic,
		chunks_path=chunks_path,
		metadata_path=metadata_path,
		keyword_index_path=keyword_index_path,
		vector_index_path=vector_index_path,
		top_k=cfg.top_k,
		min_metadata_confidence=cfg.min_metadata_confidence,
		allowed_confidentiality=cfg.allowed_confidentiality,
	)
	retrieval_ms = (time.perf_counter() - start_retrieval) * 1000.0

	hits_before_confidentiality = list(hits)
	start_conf = time.perf_counter()
	hits = filter_by_confidentiality(hits_before_confidentiality, cfg.allowed_confidentiality)
	confidentiality_ms = (time.perf_counter() - start_conf) * 1000.0

	start_proposals = time.perf_counter()
	proposals = build_curation_proposals(
		topic,
		hits,
		min_query_token_coverage=cfg.min_query_token_coverage,
		duplicate_similarity_threshold=cfg.duplicate_similarity_threshold,
		outdated_year_cutoff=cfg.outdated_year_cutoff,
	)
	proposal_ms = (time.perf_counter() - start_proposals) * 1000.0
	total_ms = (time.perf_counter() - start_total) * 1000.0

	type_counts: dict[str, int] = {}
	for proposal in proposals:
		type_counts[proposal.proposal_type] = type_counts.get(proposal.proposal_type, 0) + 1

	summary = {
		"topic": topic,
		"retrieval_hits_before_confidentiality": len(hits_before_confidentiality),
		"retrieval_hits_after_confidentiality": len(hits),
		"confidentiality_filtered_out": len(hits_before_confidentiality) - len(hits),
		"proposal_count": len(proposals),
		"proposal_type_counts": type_counts,
	}

	stage_times_ms = {
		"retrieval": round(retrieval_ms, 3),
		"confidentiality_filter": round(confidentiality_ms, 3),
		"proposal_generation": round(proposal_ms, 3),
		"total": round(total_ms, 3),
	}

	return CurationWorkflowResult(
		proposals=proposals,
		retrieval_hits=hits,
		stage_times_ms=stage_times_ms,
		summary=summary,
	)
