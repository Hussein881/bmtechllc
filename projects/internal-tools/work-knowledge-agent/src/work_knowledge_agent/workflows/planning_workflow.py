"""Planning workflow orchestration for Phase 4 baseline."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from work_knowledge_agent.agents.planner_agent import (
	PlannerResponse,
	build_evidence_context,
	build_planner_prompt,
	build_planner_response,
)
from work_knowledge_agent.guardrails import LLMBoundaryRequest, enforce_llm_boundary
from work_knowledge_agent.guardrails.citation_guardrail import enforce_citation_guardrail
from work_knowledge_agent.guardrails.confidentiality_guardrail import filter_by_confidentiality
from work_knowledge_agent.guardrails.unsupported_step_guardrail import evaluate_support
from work_knowledge_agent.models import GenerationRequest, LLMClient, build_default_llm_client
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit
from work_knowledge_agent.retrieval.query_rewriter import rewrite_query
from work_knowledge_agent.tools.search_docs import search_docs


@dataclass(frozen=True)
class PlanningWorkflowConfig:
	top_k: int = 8
	max_citations: int = 8
	min_metadata_confidence: float = 0.30
	min_support_score: float = 0.35
	min_query_token_coverage: float = 0.25
	allowed_confidentiality: tuple[str, ...] = ("public", "internal", "confidential")
	provider_mode: str = "approved_api"
	temperature: float = 0.0
	max_output_tokens: int = 700
	seed: int | None = None


@dataclass(frozen=True)
class PlanningWorkflowResult:
	response: PlannerResponse
	retrieval_hits: List[RetrievalHit]
	guardrail_status: dict
	stage_times_ms: dict
	generation_metadata: dict


def _append_guardrail_note(answer: str, reason: str, details: dict) -> str:
	note_lines = [
		"",
		"## Guardrail Review",
		"- Status: blocked",
		f"- Reason: {reason}",
	]
	if details:
		detail_parts = [f"{key}={value}" for key, value in details.items()]
		note_lines.append(f"- Details: {', '.join(detail_parts)}")
	return (answer.rstrip() + "\n" + "\n".join(note_lines)).strip()


def _enforce_output_confidentiality(citations: List[dict], allowed_levels: tuple[str, ...]) -> bool:
	allowed = {level.lower() for level in allowed_levels}
	for citation in citations:
		level = str(citation.get("confidentiality_level", "internal")).lower()
		if level not in allowed:
			return False
	return True


def _query_token_coverage(goal: str, hits: List[RetrievalHit]) -> float:
	rewritten = rewrite_query(goal)
	query_tokens = set(rewritten.tokens)
	if not query_tokens:
		return 0.0
	evidence_text = "\n".join(hit.content for hit in hits)
	evidence_tokens = set(rewrite_query(evidence_text).tokens)
	if not evidence_tokens:
		return 0.0
	overlap = query_tokens & evidence_tokens
	return len(overlap) / max(1, len(query_tokens))


def _query_entity_anchor_ok(goal: str, hits: List[RetrievalHit]) -> bool:
	rewritten_q = rewrite_query(goal)
	evidence_text = "\n".join(hit.content for hit in hits)
	evidence_tokens = set(rewrite_query(evidence_text).tokens)
	entity_tokens = [token for token in rewritten_q.tokens if any(ch.isdigit() for ch in token)]
	if not entity_tokens:
		return True
	return all(token in evidence_tokens for token in entity_tokens)


def _highest_confidentiality_level(hits: List[RetrievalHit]) -> str:
	rank = {"public": 0, "internal": 1, "confidential": 2}
	highest = "public"
	for hit in hits:
		level = str(hit.metadata.get("confidentiality_level", "internal")).lower()
		if rank.get(level, 1) > rank.get(highest, 0):
			highest = level
	return highest


def _goal_hint_queries(goal: str) -> list[str]:
	goal_l = (goal or "").lower()
	hints: list[str] = []
	if any(token in goal_l for token in ("linux", "disk", "log", "cleanup", "pressure")):
		hints.append("linux commands disk usage log cleanup")
		hints.append("linux_commands SKLM Log Cleanup")
	if any(token in goal_l for token in ("restart", "rollout", "service")):
		hints.append("sample runbook service restart validation")
	return hints


def _goal_alignment_boost(goal: str, hit: RetrievalHit) -> float:
	goal_l = (goal or "").lower()
	metadata = hit.metadata or {}
	source = str(metadata.get("source_file", "")).lower()
	section = str(metadata.get("section_heading", "")).lower()
	content = (hit.content or "").lower()

	boost = 0.0
	if any(token in goal_l for token in ("linux", "disk", "log", "cleanup", "pressure")):
		if "sample_runbook" in source:
			boost -= 0.15
		if "/linux/" in source:
			boost += 0.20
		if "linux_commands" in source:
			boost += 0.35
		if "sklm log cleanup" in source or "log cleanup" in source:
			boost += 0.25
		if re.search(r"\b(df|du|journalctl|log|disk)\b", content):
			boost += 0.10
	if any(token in goal_l for token in ("restart", "rollout", "service")):
		if "sample_runbook" in source:
			boost += 0.30
		if re.search(r"\b(restart|systemctl|status|verify)\b", content):
			boost += 0.10
	if "prerequisite" in section or "overview" in section:
		boost += 0.03
	return boost


def _merge_and_rank_hits(goal: str, hits: List[RetrievalHit], top_k: int) -> List[RetrievalHit]:
	best_by_chunk: dict[str, RetrievalHit] = {}
	for hit in hits:
		existing = best_by_chunk.get(hit.chunk_id)
		if existing is None or hit.score > existing.score:
			best_by_chunk[hit.chunk_id] = hit

	def rank_value(hit: RetrievalHit) -> tuple[float, float]:
		return (float(hit.score) + _goal_alignment_boost(goal, hit), float(hit.score))

	ranked = sorted(best_by_chunk.values(), key=rank_value, reverse=True)
	return ranked[: max(1, top_k)]


def run_planning_workflow(
	goal: str,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: PlanningWorkflowConfig | None = None,
	llm_client: LLMClient | None = None,
) -> PlanningWorkflowResult:
	cfg = config or PlanningWorkflowConfig()
	client = llm_client or build_default_llm_client()
	start_total = time.perf_counter()
	start_retrieval = time.perf_counter()
	candidate_pool_k = max(cfg.top_k * 4, 24)
	hits = search_docs(
		query=goal,
		chunks_path=chunks_path,
		metadata_path=metadata_path,
		keyword_index_path=keyword_index_path,
		vector_index_path=vector_index_path,
		top_k=candidate_pool_k,
		min_metadata_confidence=cfg.min_metadata_confidence,
		allowed_confidentiality=cfg.allowed_confidentiality,
	)
	retrieval_ms = (time.perf_counter() - start_retrieval) * 1000.0

	# Retrieve extra candidates for domain-specific goals and merge, then rank by goal alignment.
	for hint_query in _goal_hint_queries(goal):
		hint_hits = search_docs(
			query=hint_query,
			chunks_path=chunks_path,
			metadata_path=metadata_path,
			keyword_index_path=keyword_index_path,
			vector_index_path=vector_index_path,
			top_k=candidate_pool_k,
			min_metadata_confidence=cfg.min_metadata_confidence,
			allowed_confidentiality=cfg.allowed_confidentiality,
		)
		hits = _merge_and_rank_hits(goal, hits + hint_hits, cfg.top_k)

	hits_before_confidentiality = list(hits)
	start_conf = time.perf_counter()
	hits = filter_by_confidentiality(hits_before_confidentiality, cfg.allowed_confidentiality)
	hits = _merge_and_rank_hits(goal, hits, cfg.top_k)
	confidentiality_ms = (time.perf_counter() - start_conf) * 1000.0

	query_coverage = _query_token_coverage(goal, hits)
	entity_anchor_ok = _query_entity_anchor_ok(goal, hits)
	has_evidence = (
		bool(hits)
		and float(hits[0].score) >= cfg.min_support_score
		and query_coverage >= cfg.min_query_token_coverage
		and entity_anchor_ok
	)
	support_check = evaluate_support(has_evidence=has_evidence)
	selected_hits = hits[: cfg.max_citations] if has_evidence else []

	generation_metadata: dict = {}
	if not selected_hits:
		response = PlannerResponse(
			answer=(
				f"# Plan: {goal.strip()}\n\n"
				"## Summary\nUnsupported: I could not find enough grounded evidence to build a reliable plan.\n\n"
				"## Objectives\nNot provided from available evidence.\n\n"
				"## Ordered Tasks\nNot provided from available evidence.\n\n"
				"## Dependencies\nNot provided from available evidence.\n\n"
				"## Open Questions\nNot provided from available evidence.\n\n"
				"## Risks and Unknowns\nNot provided from available evidence.\n\n"
				"## Sources\nNone."
			),
			citations=[],
			supported=False,
		)
		answer_ms = 0.0
		guardrails_ms = 0.0
		guardrail_status = {
			"supported": support_check.is_supported,
			"support_message": support_check.message,
			"citation_ok": False,
			"citation_reason": "missing_evidence",
			"citation_details": {},
			"boundary_allowed": False,
			"boundary_reason": "missing_evidence",
			"retrieval_hits_before_confidentiality": len(hits_before_confidentiality),
			"retrieval_hits_after_confidentiality": len(hits),
			"confidentiality_filtered_out": len(hits_before_confidentiality) - len(hits),
			"query_token_coverage": round(query_coverage, 4),
			"entity_anchor_ok": entity_anchor_ok,
			"output_confidentiality_ok": True,
		}
	else:
		evidence_context = build_evidence_context(selected_hits)
		boundary = enforce_llm_boundary(
			LLMBoundaryRequest(
				prompt=build_planner_prompt(goal),
				context=evidence_context,
				provider_mode=cfg.provider_mode,
				confidentiality_level=_highest_confidentiality_level(selected_hits),
			)
		)
		start_answer = time.perf_counter()
		if boundary.allowed:
			generation = client.generate(
				GenerationRequest(
					prompt=boundary.sanitized_prompt,
					context=boundary.sanitized_context,
					metadata={"workflow": "planning", "goal": goal.strip()},
					temperature=cfg.temperature,
					max_output_tokens=cfg.max_output_tokens,
					seed=cfg.seed,
				)
			)
			generation_metadata = {
				"provider": generation.metadata.provider,
				"model_name": generation.metadata.model_name,
				"prompt_version": generation.metadata.prompt_version,
				"request_id": generation.metadata.request_id,
				"input_token_count": generation.metadata.input_token_count,
				"output_token_count": generation.metadata.output_token_count,
				"latency_ms": generation.metadata.latency_ms,
				"extra": dict(generation.metadata.extra),
			}
			response = build_planner_response(goal, generation.text, selected_hits, max_citations=cfg.max_citations)
		else:
			response = PlannerResponse(
				answer=(
					f"# Plan: {goal.strip()}\n\n"
					f"## Summary\nUnsupported: generation blocked by LLM boundary ({boundary.reason}).\n\n"
					"## Objectives\nNot provided from available evidence.\n\n"
					"## Ordered Tasks\nNot provided from available evidence.\n\n"
					"## Dependencies\nNot provided from available evidence.\n\n"
					"## Open Questions\nNot provided from available evidence.\n\n"
					"## Risks and Unknowns\nNot provided from available evidence.\n\n"
					"## Sources\nNone."
				),
				citations=[],
				supported=False,
			)
		answer_ms = (time.perf_counter() - start_answer) * 1000.0

		evidence_by_chunk = {hit.chunk_id: hit.content for hit in selected_hits}
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
		guardrail_status = {
			"supported": support_check.is_supported and response.supported,
			"support_message": support_check.message,
			"citation_ok": citation_check.passed,
			"citation_reason": citation_check.reason,
			"citation_details": citation_check.details,
			"boundary_allowed": boundary.allowed,
			"boundary_reason": boundary.reason,
			"retrieval_hits_before_confidentiality": len(hits_before_confidentiality),
			"retrieval_hits_after_confidentiality": len(hits),
			"confidentiality_filtered_out": len(hits_before_confidentiality) - len(hits),
			"query_token_coverage": round(query_coverage, 4),
			"entity_anchor_ok": entity_anchor_ok,
			"output_confidentiality_ok": output_confidentiality_ok,
		}

		if not citation_check.passed or not output_confidentiality_ok:
			reason = citation_check.reason if not citation_check.passed else "output_confidentiality_violation"
			if not citation_check.passed:
				response = PlannerResponse(
					answer=_append_guardrail_note(response.answer, reason, citation_check.details),
					citations=response.citations,
					supported=False,
				)
			else:
				response = PlannerResponse(
					answer=f"Unsupported: plan generation blocked by citation guardrail ({reason}).",
					citations=[],
					supported=False,
				)

	total_ms = (time.perf_counter() - start_total) * 1000.0
	stage_times_ms = {
		"retrieval": round(retrieval_ms, 3),
		"confidentiality_filter": round(confidentiality_ms, 3),
		"answer_generation": round(answer_ms, 3),
		"guardrails": round(guardrails_ms, 3),
		"total": round(total_ms, 3),
	}

	return PlanningWorkflowResult(
		response=response,
		retrieval_hits=hits,
		guardrail_status=guardrail_status,
		stage_times_ms=stage_times_ms,
		generation_metadata=generation_metadata,
	)
