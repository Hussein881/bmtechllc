"""Unit tests for the Phase 4 planning workflow baseline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.models.llm_client import GenerationMetadata, GenerationRequest, GenerationResult, LLMClient
from work_knowledge_agent.workflows.planning_workflow import PlanningWorkflowConfig, run_planning_workflow


class _FakePlannerClient(LLMClient):
	def generate(self, request: GenerationRequest) -> GenerationResult:
		return GenerationResult(
			text=(
				"## Summary\nCreate a grounded execution plan.\n\n"
				"## Objectives\n- Complete the target change safely.\n\n"
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
				request_id="req-plan-1",
				input_token_count=40,
				output_token_count=32,
				latency_ms=150.0,
				extra={},
			),
		)


class PlanningWorkflowTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_supported_plan_includes_required_sections_and_citations(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc1::chunk-0001"
			content = "Plan a safe service restart rollout: validate access, confirm prerequisites, then execute the service restart and verification steps."
			self._write_jsonl(
				chunks_path,
				[
					{
						"chunk_id": chunk_id,
						"content": content,
						"metadata": {"source_file": "doc1.md", "section_heading": "Execution Plan"},
					}
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{
						"chunk_id": chunk_id,
						"source_file": "doc1.md",
						"section_heading": "Execution Plan",
						"metadata_confidence": 0.95,
						"confidentiality_level": "internal",
						"provenance": {"loader_version": "2.0.0"},
					}
				],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"plan": [chunk_id], "safe": [chunk_id], "service": [chunk_id], "restart": [chunk_id], "rollout": [chunk_id], "validate": [chunk_id], "prerequisites": [chunk_id], "execute": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(
				json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"plan": 1.0, "safe": 1.0, "service": 1.0, "restart": 2.0, "rollout": 1.0, "validate": 2.0, "execute": 1.0}}}}),
				encoding="utf-8",
			)

			result = run_planning_workflow(
				goal="Plan a safe service restart rollout.",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=PlanningWorkflowConfig(top_k=3),
				llm_client=_FakePlannerClient(),
			)

			self.assertTrue(result.response.supported)
			self.assertTrue(result.guardrail_status["boundary_allowed"])
			self.assertTrue(result.guardrail_status["citation_ok"])
			self.assertGreaterEqual(len(result.response.citations), 1)
			for section in (
				"## Summary",
				"## Objectives",
				"## Ordered Tasks",
				"## Dependencies",
				"## Open Questions",
				"## Risks and Unknowns",
				"## Sources",
			):
				self.assertIn(section, result.response.answer)


if __name__ == "__main__":
	unittest.main()