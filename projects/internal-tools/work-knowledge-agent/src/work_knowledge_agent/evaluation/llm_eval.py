"""Evaluation helpers for the Watsonx-backed Phase 3 generation path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Sequence

from work_knowledge_agent.guardrails import LLMBoundaryRequest, enforce_llm_boundary
from work_knowledge_agent.models import GenerationRequest, LLMClient


@dataclass(frozen=True)
class LLMEvalCase:
	id: str
	prompt: str
	context: str = ""
	expected_contains: tuple[str, ...] = ()
	provider_mode: str = "api"
	confidentiality_level: str = "public"
	temperature: float = 0.0
	max_output_tokens: int = 128


def load_llm_eval_cases(path: Path) -> list[LLMEvalCase]:
	if not path.exists() or not path.read_text(encoding="utf-8").strip():
		return []
	rows = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(rows, list):
		raise ValueError("LLM eval cases file must contain a JSON array")

	cases: list[LLMEvalCase] = []
	for idx, row in enumerate(rows, start=1):
		if not isinstance(row, dict):
			continue
		prompt = str(row.get("prompt", "")).strip()
		if not prompt:
			continue
		case_id = str(row.get("id", "")).strip() or f"llm-case-{idx}"
		expected = row.get("expected_contains", [])
		if not isinstance(expected, list):
			expected = []
		cases.append(
			LLMEvalCase(
				id=case_id,
				prompt=prompt,
				context=str(row.get("context", "")),
				expected_contains=tuple(str(value) for value in expected if str(value).strip()),
				provider_mode=str(row.get("provider_mode", "api") or "api"),
				confidentiality_level=str(row.get("confidentiality_level", "public") or "public"),
				temperature=float(row.get("temperature", 0.0)),
				max_output_tokens=int(row.get("max_output_tokens", 128)),
			)
		)
	return cases


def evaluate_llm_cases(cases: Sequence[LLMEvalCase], client: LLMClient) -> dict[str, Any]:
	total = 0
	boundary_allowed = 0
	generation_success = 0
	expected_match = 0
	latencies: list[float] = []
	input_tokens: list[int] = []
	output_tokens: list[int] = []
	per_case: list[dict[str, Any]] = []

	for case in cases:
		total += 1
		boundary = enforce_llm_boundary(
			LLMBoundaryRequest(
				prompt=case.prompt,
				context=case.context,
				provider_mode=case.provider_mode,
				confidentiality_level=case.confidentiality_level,
			)
		)
		if boundary.allowed:
			boundary_allowed += 1

		row: dict[str, Any] = {
			"id": case.id,
			"provider_mode": case.provider_mode,
			"confidentiality_level": case.confidentiality_level,
			"expected_contains": list(case.expected_contains),
			"boundary_allowed": boundary.allowed,
			"boundary_reason": boundary.reason,
		}

		if not boundary.allowed:
			row["success"] = False
			row["expected_match"] = False
			row["error"] = f"boundary_blocked:{boundary.reason}"
			per_case.append(row)
			continue

		try:
			result = client.generate(
				GenerationRequest(
					prompt=boundary.sanitized_prompt,
					context=boundary.sanitized_context,
					metadata={"eval_case_id": case.id},
					temperature=case.temperature,
					max_output_tokens=case.max_output_tokens,
				)
			)
		except Exception as exc:  # noqa: BLE001
			row["success"] = False
			row["expected_match"] = False
			row["error"] = str(exc)
			per_case.append(row)
			continue

		generation_success += 1
		text = result.text
		matched = _contains_all(text, case.expected_contains)
		if matched:
			expected_match += 1

		if result.metadata.latency_ms is not None:
			latencies.append(float(result.metadata.latency_ms))
		if result.metadata.input_token_count is not None:
			input_tokens.append(int(result.metadata.input_token_count))
		if result.metadata.output_token_count is not None:
			output_tokens.append(int(result.metadata.output_token_count))

		row.update(
			{
				"success": True,
				"expected_match": matched,
				"text": text,
				"latency_ms": result.metadata.latency_ms,
				"input_token_count": result.metadata.input_token_count,
				"output_token_count": result.metadata.output_token_count,
				"model_name": result.metadata.model_name,
				"prompt_version": result.metadata.prompt_version,
				"request_id": result.metadata.request_id,
			}
		)
		per_case.append(row)

	return {
		"total_cases": total,
		"metrics": {
			"boundary_allow_rate_pct": round(_percent(boundary_allowed, total), 3),
			"generation_success_rate_pct": round(_percent(generation_success, total), 3),
			"expected_match_rate_pct": round(_percent(expected_match, total), 3),
			"latency_p50_ms": round(float(median(latencies)) if latencies else 0.0, 3),
			"latency_p95_ms": round(_p95(latencies), 3),
			"avg_input_tokens": round(_mean(input_tokens), 3),
			"avg_output_tokens": round(_mean(output_tokens), 3),
		},
		"per_case": per_case,
	}


def _contains_all(text: str, expected: Iterable[str]) -> bool:
	value = (text or "").lower()
	for token in expected:
		if str(token).lower() not in value:
			return False
	return True


def _percent(num: int, den: int) -> float:
	return (num / den * 100.0) if den else 0.0


def _p95(values: list[float]) -> float:
	if not values:
		return 0.0
	sorted_vals = sorted(values)
	idx = min(len(sorted_vals) - 1, int(round(0.95 * (len(sorted_vals) - 1))))
	return float(sorted_vals[idx])


def _mean(values: list[int]) -> float:
	if not values:
		return 0.0
	return sum(values) / len(values)