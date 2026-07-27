"""Evaluation helpers for the Phase 5 curation workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Sequence

from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow


@dataclass(frozen=True)
class CurationEvalCase:
	id: str
	topic: str
	expected_types: tuple[str, ...] = ()


def load_curation_eval_cases(path: Path) -> list[CurationEvalCase]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(rows, list):
		raise ValueError("Curation eval cases file must contain a JSON array")

	cases: list[CurationEvalCase] = []
	for idx, row in enumerate(rows, start=1):
		if not isinstance(row, dict):
			continue
		topic = str(row.get("topic", "")).strip()
		if not topic:
			continue
		case_id = str(row.get("id", "")).strip() or f"curation-case-{idx}"
		expected_types = row.get("expected_types", [])
		if not isinstance(expected_types, list):
			expected_types = []
		cases.append(
			CurationEvalCase(
				id=case_id,
				topic=topic,
				expected_types=tuple(str(value) for value in expected_types if str(value).strip()),
			)
		)
	return cases


def evaluate_curation_cases(
	cases: Sequence[CurationEvalCase],
	*,
	chunks_path: Path,
	metadata_path: Path,
	keyword_index_path: Path,
	vector_index_path: Path,
	config: CurationWorkflowConfig,
) -> dict[str, Any]:
	total_cases = 0
	runs = 0
	expected_type_match = 0
	non_empty_proposals = 0
	latencies: list[float] = []
	proposal_counts: list[int] = []
	per_case: list[dict[str, Any]] = []

	for case in cases:
		total_cases += 1
		runs += 1
		result = run_curation_workflow(
			topic=case.topic,
			chunks_path=chunks_path,
			metadata_path=metadata_path,
			keyword_index_path=keyword_index_path,
			vector_index_path=vector_index_path,
			config=config,
		)
		proposal_types = sorted({proposal.proposal_type for proposal in result.proposals})
		proposal_count = len(result.proposals)
		matched = _type_match(proposal_types, case.expected_types)
		if matched:
			expected_type_match += 1
		if proposal_count > 0:
			non_empty_proposals += 1
		latencies.append(float(result.stage_times_ms.get("total", 0.0)))
		proposal_counts.append(float(proposal_count))
		per_case.append(
			{
				"id": case.id,
				"topic": case.topic,
				"expected_types": list(case.expected_types),
				"proposal_count": proposal_count,
				"proposal_types": proposal_types,
				"expected_type_match": matched,
				"summary": result.summary,
				"stage_times_ms": result.stage_times_ms,
			}
		)

	return {
		"total_cases": total_cases,
		"total_runs": runs,
		"metrics": {
			"expected_type_match_rate_pct": round(_percent(expected_type_match, runs), 3),
			"non_empty_proposal_rate_pct": round(_percent(non_empty_proposals, runs), 3),
			"proposal_count_avg": round(_mean(proposal_counts), 3),
			"latency_p50_ms": round(float(median(latencies)) if latencies else 0.0, 3),
			"latency_p95_ms": round(_p95(latencies), 3),
		},
		"per_case": per_case,
	}


def _type_match(proposal_types: Sequence[str], expected_types: Sequence[str]) -> bool:
	if not expected_types:
		return True
	actual = {str(value).strip().lower() for value in proposal_types if str(value).strip()}
	for expected in expected_types:
		if str(expected).strip().lower() not in actual:
			return False
	return True


def _percent(num: int, den: int) -> float:
	return (num / den * 100.0) if den else 0.0


def _mean(values: list[float]) -> float:
	if not values:
		return 0.0
	return sum(values) / float(len(values))


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])
