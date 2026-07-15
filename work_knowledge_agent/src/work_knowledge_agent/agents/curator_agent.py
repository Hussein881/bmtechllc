"""Curator agent helpers for Phase 5 baseline."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import List

from work_knowledge_agent.agents.qa_agent import build_citation
from work_knowledge_agent.retrieval.hybrid_retriever import RetrievalHit


@dataclass(frozen=True)
class CurationProposal:
	proposal_type: str
	title: str
	rationale: str
	actions: List[str]
	evidence: List[dict]
	confidence: float

	def to_dict(self) -> dict:
		return asdict(self)


def build_curation_proposals(
	topic: str,
	hits: List[RetrievalHit],
	min_query_token_coverage: float = 0.40,
	duplicate_similarity_threshold: float = 0.92,
	outdated_year_cutoff: int = 2021,
) -> List[CurationProposal]:
	proposals: List[CurationProposal] = []
	proposals.extend(_missing_knowledge_proposals(topic, hits, min_query_token_coverage=min_query_token_coverage))
	proposals.extend(_duplicate_content_proposals(hits, similarity_threshold=duplicate_similarity_threshold))
	proposals.extend(_outdated_content_proposals(hits, year_cutoff=outdated_year_cutoff))
	return proposals


def _missing_knowledge_proposals(topic: str, hits: List[RetrievalHit], min_query_token_coverage: float) -> List[CurationProposal]:
	if not hits:
		return [
			CurationProposal(
				proposal_type="missing_knowledge",
				title="No grounded evidence found for requested topic",
				rationale="No retrieval hits were found after filters, so the knowledge base is missing direct coverage for this topic.",
				actions=[
					"Add or ingest an approved runbook/spec covering this topic",
					"Tag the new source with explicit component/system metadata",
				],
				evidence=[],
				confidence=0.95,
			)
		]

	query_tokens = _tokens(topic)
	evidence_tokens = set()
	for hit in hits:
		evidence_tokens.update(_tokens(hit.content))

	query_entity_tokens = {token for token in query_tokens if any(ch.isdigit() for ch in token)}
	entity_anchor_ok = all(token in evidence_tokens for token in query_entity_tokens) if query_entity_tokens else True
	if not entity_anchor_ok:
		evidence = [build_citation(hit) for hit in hits[:3]]
		return [
			CurationProposal(
				proposal_type="missing_knowledge",
				title="Missing evidence for entity-specific topic",
				rationale=(
					"Retrieved content did not include one or more entity anchors from the request "
					f"({', '.join(sorted(query_entity_tokens))})."
				),
				actions=[
					"Add a source explicitly covering the requested entity/system",
					"Verify metadata tags so entity-specific docs are retrievable",
				],
				evidence=evidence,
				confidence=0.9,
			)
		]

	coverage = 0.0
	if query_tokens:
		coverage = len(query_tokens.intersection(evidence_tokens)) / float(len(query_tokens))

	if coverage >= min_query_token_coverage:
		return []

	evidence = [build_citation(hit) for hit in hits[:3]]
	return [
		CurationProposal(
			proposal_type="missing_knowledge",
			title="Low topic coverage in retrieved evidence",
			rationale=(
				"Retrieved content does not cover enough query concepts "
				f"(coverage={round(coverage * 100.0, 1)}%)."
			),
			actions=[
				"Add a focused runbook section for uncovered concepts",
				"Review metadata tags so relevant docs are discoverable",
			],
			evidence=evidence,
			confidence=0.75,
		)
	]


def _duplicate_content_proposals(hits: List[RetrievalHit], similarity_threshold: float) -> List[CurationProposal]:
	proposals: List[CurationProposal] = []
	by_source: dict[str, list[RetrievalHit]] = {}
	for hit in hits:
		source = str(hit.metadata.get("source_file", "") or "unknown")
		by_source.setdefault(source, []).append(hit)

	for source, source_hits in by_source.items():
		if len(source_hits) < 2:
			continue
		first = source_hits[0].content.strip()
		for candidate in source_hits[1:]:
			similarity = _content_similarity(first, candidate.content.strip())
			if similarity < similarity_threshold:
				continue
			confidence = _calibrated_duplicate_confidence(similarity=similarity, threshold=similarity_threshold)
			proposals.append(
				CurationProposal(
					proposal_type="duplicate_content",
					title="Potential duplicate content chunks detected",
					rationale=(
						f"Highly similar chunks were retrieved from {source} "
						f"(similarity={round(similarity, 3)}, threshold={round(similarity_threshold, 3)})."
					),
					actions=[
						"Merge or de-duplicate repeated sections",
						"Keep a canonical section and link other references",
					],
					evidence=[build_citation(source_hits[0]), build_citation(candidate)],
					confidence=confidence,
				)
			)
			break
	return proposals


def _outdated_content_proposals(hits: List[RetrievalHit], year_cutoff: int) -> List[CurationProposal]:
	proposals: List[CurationProposal] = []
	current_year = datetime.now(timezone.utc).year
	for hit in hits:
		content = (hit.content or "")
		years = [int(value) for value in re.findall(r"\b(20\d{2})\b", content)]
		if not years:
			continue
		latest_year = max(years)
		if latest_year > year_cutoff:
			continue
		source = str(hit.metadata.get("source_file", "") or "unknown")
		confidence = _calibrated_outdated_confidence(current_year=current_year, latest_year=latest_year, cutoff_year=year_cutoff)
		proposals.append(
			CurationProposal(
				proposal_type="outdated_content",
				title="Potentially outdated operational guidance",
				rationale=(
					"Retrieved evidence appears old (latest year observed "
					f"{latest_year}, cutoff={year_cutoff}) and may need refresh for current procedures."
				),
				actions=[
					"Validate whether commands/process remain current",
					"Update the source with current version/date metadata",
				],
				evidence=[build_citation(hit)],
				confidence=confidence,
			)
		)
	return proposals


def _tokens(value: str) -> set[str]:
	return {token for token in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(token) > 1}


def _content_similarity(a: str, b: str) -> float:
	if not a or not b:
		return 0.0
	return SequenceMatcher(None, a, b).ratio()


def _calibrated_duplicate_confidence(similarity: float, threshold: float) -> float:
	if threshold >= 0.999:
		return 0.95
	range_width = max(0.001, 1.0 - threshold)
	normalized = max(0.0, min(1.0, (similarity - threshold) / range_width))
	confidence = 0.7 + normalized * 0.25
	return round(max(0.0, min(0.95, confidence)), 3)


def _calibrated_outdated_confidence(current_year: int, latest_year: int, cutoff_year: int) -> float:
	age = max(0, current_year - latest_year)
	cutoff_gap = max(0, cutoff_year - latest_year)
	confidence = 0.55 + min(0.3, age * 0.03) + min(0.1, cutoff_gap * 0.02)
	return round(max(0.0, min(0.95, confidence)), 3)
