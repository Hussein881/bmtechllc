"""Unit tests for the Phase 4 planning evaluation harness."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.evaluation.planning_eval import PlanningEvalCase, evaluate_planning_cases
from work_knowledge_agent.models.llm_client import GenerationMetadata, GenerationRequest, GenerationResult, LLMClient
from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig


class _FakePlanningEvalClient(LLMClient):
	def generate(self, request: GenerationRequest) -> GenerationResult:
		return GenerationResult(
			text=(
				"## Summary\nCreate a grounded plan.\n\n"
				"## Objectives\n- Complete the rollout safely.\n\n"
				"## Ordered Tasks\n1. Identify prerequisites.\n2. Validate access.\n3. Execute the change.\n\n"
				"## Dependencies\n- Access to the target system.\n\n"
				"## Open Questions\n- Which environment is in scope?\n\n"
				"## Risks and Unknowns\n- Missing environment details may delay execution.\n\n"
				"## Sources\nUse the retrieved runbook and command notes."
			),
			metadata=GenerationMetadata(
				provider="watsonx-api",
				model_name="ibm/granite-3-8b-instruct",
				prompt_version="phase4-watsonx-v1",
				request_id="req-plan-eval-1",
				input_token_count=20,
				output_token_count=18,
				latency_ms=200.0,
				extra={},
			),
		)


class PlanningEvalTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_evaluate_planning_cases_reports_metrics(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc1::chunk-0001"
			content = "Plan a safe service restart rollout: identify prerequisites, validate access, then execute the change."
			self._write_jsonl(
				chunks_path,
				[{"chunk_id": chunk_id, "content": content, "metadata": {"source_file": "sample_runbook.md", "section_heading": "Restart Plan"}}],
			)
			self._write_jsonl(
				metadata_path,
				[{"chunk_id": chunk_id, "source_file": "sample_runbook.md", "section_heading": "Restart Plan", "metadata_confidence": 0.9, "confidentiality_level": "internal", "provenance": {}}],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"plan": [chunk_id], "safe": [chunk_id], "restart": [chunk_id], "rollout": [chunk_id], "validate": [chunk_id], "execute": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"plan": 1.0, "restart": 2.0, "validate": 1.0, "execute": 1.0}}}}), encoding="utf-8")

			cases = [
				PlanningEvalCase(
					id="case-1",
					goal="Plan a safe service restart rollout.",
					expected_tasks=("Identify prerequisites", "Validate access", "Execute the change"),
					expected_sources=("sample_runbook",),
					expected_supported=True,
					required_unknown_signals=("open questions",),
					min_open_questions_count=1,
				)
			]

			report = evaluate_planning_cases(
				cases,
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=PlanningWorkflowConfig(),
				llm_client=_FakePlanningEvalClient(),
				trials_per_case=2,
			)

			self.assertEqual(report["total_cases"], 1)
			self.assertEqual(report["trials_per_case"], 2)
			self.assertEqual(report["total_runs"], 2)
			self.assertEqual(report["metrics"]["supported_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["required_sections_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["expected_task_match_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["expected_support_match_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["unknown_signal_match_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["open_questions_presence_rate_pct"], 100.0)
			self.assertEqual(len(report["per_case"][0]["trials"]), 2)


if __name__ == "__main__":
	unittest.main()