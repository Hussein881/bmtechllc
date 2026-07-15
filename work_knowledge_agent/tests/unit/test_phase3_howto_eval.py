"""Unit tests for the Phase 3 How-To evaluation harness."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.evaluation.howto_eval import evaluate_howto_cases, HowToEvalCase
from work_knowledge_agent.models.llm_client import GenerationMetadata, GenerationRequest, GenerationResult, LLMClient
from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig


class _FakeHowToEvalClient(LLMClient):
	def generate(self, request: GenerationRequest) -> GenerationResult:
		return GenerationResult(
			text=(
				"## Summary\nRun a safe service restart.\n\n"
				"## Assumptions\nSystemd is in use.\n\n"
				"## Prerequisites\nHost access.\n\n"
				"## Steps\n1. Restart the service. 2. Check status.\n\n"
				"## Commands\n$ systemctl restart my-service\n$ systemctl status my-service\n\n"
				"## Validation\nConfirm the service is active.\n\n"
				"## Failure Modes\nRestart fails.\n\n"
				"## Sources\nlinux_commands"
			),
			metadata=GenerationMetadata(
				provider="watsonx-api",
				model_name="ibm/granite-3-8b-instruct",
				prompt_version="phase3-watsonx-v1",
				request_id="req-eval-1",
				input_token_count=20,
				output_token_count=18,
				latency_ms=200.0,
				extra={},
			),
		)


class HowToEvalTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_evaluate_howto_cases_reports_metrics(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc1::chunk-0001"
			content = "Restart with systemctl restart my-service and verify with systemctl status my-service."
			self._write_jsonl(
				chunks_path,
				[{"chunk_id": chunk_id, "content": content, "metadata": {"source_file": "linux_commands.md", "section_heading": "Restart"}}],
			)
			self._write_jsonl(
				metadata_path,
				[{"chunk_id": chunk_id, "source_file": "linux_commands.md", "section_heading": "Restart", "metadata_confidence": 0.9, "confidentiality_level": "internal", "provenance": {}}],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"restart": [chunk_id], "status": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"restart": 2.0, "status": 1.0}}}}), encoding="utf-8")

			cases = [
				HowToEvalCase(
					id="case-1",
					task="How do I restart a service safely and verify it is healthy?",
					expected_commands=("systemctl restart", "systemctl status"),
					expected_sources=("linux_commands",),
				)
			]

			report = evaluate_howto_cases(
				cases,
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=HowToWorkflowConfig(),
				llm_client=_FakeHowToEvalClient(),
				trials_per_case=2,
			)

			self.assertEqual(report["total_cases"], 1)
			self.assertEqual(report["trials_per_case"], 2)
			self.assertEqual(report["total_runs"], 2)
			self.assertEqual(report["metrics"]["supported_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["required_sections_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["expected_command_match_rate_pct"], 100.0)
			self.assertEqual(len(report["per_case"][0]["trials"]), 2)


if __name__ == "__main__":
	unittest.main()