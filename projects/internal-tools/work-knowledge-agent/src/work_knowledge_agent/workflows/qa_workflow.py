"""Q&A workflow orchestration for Phase 2 baseline."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from work_knowledge_agent.agents.qa_agent import QAResponse, answer_question
from work_knowledge_agent.guardrails.citation_guardrail import enforce_citation_guardrail
from work_knowledge_agent.guardrails.confidentiality_guardrail import filter_by_confidentiality
from work_knowledge_agent.guardrails.unsupported_step_guardrail import evaluate_support
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit
from work_knowledge_agent.retrieval.query_rewriter import rewrite_query
from work_knowledge_agent.tools.search_docs import search_docs


@dataclass(frozen=True)
class QAWorkflowConfig:
	top_k: int = 8
	min_metadata_confidence: float = 0.30
	min_support_score: float = 0.35
	min_query_token_coverage: float = 0.25
	allowed_confidentiality: tuple[str, ...] = ("public", "internal", "confidential")


@dataclass(frozen=True)
class QAWorkflowResult:
	response: QAResponse
	retrieval_hits: List[RetrievalHit]
	guardrail_status: dict
	stage_times_ms: dict


def _enforce_output_confidentiality(citations: List[dict], allowed_levels: tuple[str, ...]) -> bool:
	allowed = {level.lower() for level in allowed_levels}
	for citation in citations:
		level = str(citation.get("confidentiality_level", "internal")).lower()
		if level not in allowed:
			return False
	return True


def _query_token_coverage(question: str, hits: List[RetrievalHit]) -> float:
	rewritten = rewrite_query(question)
	query_tokens = set(rewritten.tokens)
	if not query_tokens:
		return 0.0
	evidence_text = "\n".join(hit.content for hit in hits)
	evidence_tokens = set(rewrite_query(evidence_text).tokens)
	if not evidence_tokens:
		return 0.0
	overlap = query_tokens & evidence_tokens
	return len(overlap) / max(1, len(query_tokens))


def _query_entity_anchor_ok(question: str, hits: List[RetrievalHit]) -> bool:
	rewritten_q = rewrite_query(question)
	evidence_text = "\n".join(hit.content for hit in hits)
	evidence_tokens = set(rewrite_query(evidence_text).tokens)
	entity_tokens = [token for token in rewritten_q.tokens if any(ch.isdigit() for ch in token)]
	if not entity_tokens:
		return True
	return all(token in evidence_tokens for token in entity_tokens)


def _definition_target(question: str) -> str | None:
	q = (question or "").strip().lower()
	patterns = [
		r"^what\s+is\s+([a-z0-9_./ -]{2,})\??$",
		r"^who\s+is\s+([a-z0-9_./ -]{2,})\??$",
		r"^define\s+([a-z0-9_./ -]{2,})\??$",
	]
	for pattern in patterns:
		m = re.match(pattern, q)
		if not m:
			continue
		target = m.group(1).strip(" ?.")
		tokens = [tok for tok in target.split() if tok not in {"a", "an", "the"}]
		if tokens:
			return tokens[-1]
	return None


def _definition_boost(term: str, hit: RetrievalHit) -> float:
	if not term:
		return 0.0
	metadata = hit.metadata or {}
	source = str(metadata.get("source_file", "")).lower()
	section = str(metadata.get("section_heading", "")).lower()
	content = (hit.content or "").lower()

	boost = 0.0
	if f"/{term}/readme.md" in source or source.endswith(f"/{term}/readme.md"):
		boost += 0.55
	if section == term or section in {"quick links", "overview", "introduction"}:
		boost += 0.20
	if re.search(rf"`?{re.escape(term)}`?\s+is\s+", content):
		boost += 0.45
	if f"{term} script" in content or f"{term} workload" in content:
		boost += 0.05
	return boost


def _rerank_definition_hits(question: str, hits: List[RetrievalHit]) -> List[RetrievalHit]:
	term = _definition_target(question)
	if not term or not hits:
		return hits

	ranked = sorted(
		hits,
		key=lambda hit: float(hit.score) + _definition_boost(term, hit),
		reverse=True,
	)
	return ranked


def run_qa_workflow(
	question: str,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: QAWorkflowConfig | None = None,
) -> QAWorkflowResult:
	cfg = config or QAWorkflowConfig()
	start_total = time.perf_counter()
	start_retrieval = time.perf_counter()
	hits = search_docs(
		query=question,
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
	hits = _rerank_definition_hits(question, hits)
	confidentiality_ms = (time.perf_counter() - start_conf) * 1000.0

	start_answer = time.perf_counter()
	query_coverage = _query_token_coverage(question, hits)
	entity_anchor_ok = _query_entity_anchor_ok(question, hits)
	has_evidence = (
		bool(hits)
		and float(hits[0].score) >= cfg.min_support_score
		and query_coverage >= cfg.min_query_token_coverage
		and entity_anchor_ok
	)
	support_check = evaluate_support(has_evidence=has_evidence)
	answer_hits = hits if has_evidence else []
	response = answer_question(question, answer_hits)
	answer_ms = (time.perf_counter() - start_answer) * 1000.0

	evidence_by_chunk = {hit.chunk_id: hit.content for hit in answer_hits}
	start_guardrails = time.perf_counter()
	citation_check = enforce_citation_guardrail(
		response.answer,
		response.citations,
		evidence_by_chunk=evidence_by_chunk,
	)
	output_confidentiality_ok = _enforce_output_confidentiality(
		response.citations,
		cfg.allowed_confidentiality,
	)
	guardrails_ms = (time.perf_counter() - start_guardrails) * 1000.0
	total_ms = (time.perf_counter() - start_total) * 1000.0

	guardrail_status = {
		"supported": support_check.is_supported,
		"support_message": support_check.message,
		"citation_ok": citation_check.passed,
		"citation_reason": citation_check.reason,
		"citation_details": citation_check.details,
		"retrieval_hits_before_confidentiality": len(hits_before_confidentiality),
		"retrieval_hits_after_confidentiality": len(hits),
		"confidentiality_filtered_out": len(hits_before_confidentiality) - len(hits),
		"query_token_coverage": round(query_coverage, 4),
		"entity_anchor_ok": entity_anchor_ok,
		"output_confidentiality_ok": output_confidentiality_ok,
	}

	if not citation_check.passed or not output_confidentiality_ok:
		reason = citation_check.reason if not citation_check.passed else "output_confidentiality_violation"
		response = QAResponse(
			answer=(
				"Unsupported: answer generation blocked by citation guardrail "
				f"({reason})."
			),
			citations=[],
			supported=False,
		)

	stage_times_ms = {
		"retrieval": round(retrieval_ms, 3),
		"confidentiality_filter": round(confidentiality_ms, 3),
		"answer_generation": round(answer_ms, 3),
		"guardrails": round(guardrails_ms, 3),
		"total": round(total_ms, 3),
	}

	return QAWorkflowResult(
		response=response,
		retrieval_hits=hits,
		guardrail_status=guardrail_status,
		stage_times_ms=stage_times_ms,
	)
