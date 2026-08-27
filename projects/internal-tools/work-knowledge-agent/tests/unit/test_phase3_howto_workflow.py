"""Unit tests for the Phase 3 How-To workflow baseline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.models.llm_client import GenerationMetadata, GenerationRequest, GenerationResult, LLMClient
from work_knowledge_agent.workflows.howto_workflow import HowToWorkflowConfig, run_howto_workflow


class _FakeHowToClient(LLMClient):
	def generate(self, request: GenerationRequest) -> GenerationResult:
		return GenerationResult(
			text=(
				"## Summary\nUse the retrieved service procedure.\n\n"
				"## Assumptions\nSystemd is available.\n\n"
				"## Prerequisites\nAccess to the host.\n\n"
				"## Steps\n1. Restart the service.\n2. Check status.\n\n"
				"## Commands\n$ systemctl restart my-service\n$ systemctl status my-service\n\n"
				"## Validation\nConfirm the service is active.\n\n"
				"## Failure Modes\nService does not return to active state.\n\n"
				"## Sources\nUse the retrieved service procedure evidence."
			),
			metadata=GenerationMetadata(
				provider="watsonx-api",
				model_name="ibm/granite-3-8b-instruct",
				prompt_version="phase3-watsonx-v1",
				request_id="req-howto-1",
				input_token_count=40,
				output_token_count=32,
				latency_ms=150.0,
				extra={},
			),
		)


class _FakeUngroundedCommandClient(LLMClient):
	def generate(self, request: GenerationRequest) -> GenerationResult:
		return GenerationResult(
			text=(
				"## Summary\nUse the procedure.\n\n"
				"## Assumptions\nSystem access is available.\n\n"
				"## Prerequisites\nUser can run commands.\n\n"
				"## Steps\n1. List timers.\n\n"
				"## Commands\n$ sudo systemctl list-units --type=timer\n\n"
				"## Validation\nConfirm timers are listed.\n\n"
				"## Failure Modes\nCommand may fail.\n\n"
				"## Sources\nProcedure evidence."
			),
			metadata=GenerationMetadata(
				provider="watsonx-api",
				model_name="ibm/granite-3-8b-instruct",
				prompt_version="phase3-watsonx-v1",
				request_id="req-howto-2",
				input_token_count=20,
				output_token_count=18,
				latency_ms=150.0,
				extra={},
			),
		)


class HowToWorkflowTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_supported_howto_includes_required_sections_and_citations(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc1::chunk-0001"
			content = (
				"Restart the service with systemctl restart my-service and verify status with "
				"systemctl status my-service until it reports active."
			)
			self._write_jsonl(
				chunks_path,
				[
					{
						"chunk_id": chunk_id,
						"content": content,
						"metadata": {"source_file": "doc1.md", "section_heading": "Restart Service"},
					}
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{
						"chunk_id": chunk_id,
						"source_file": "doc1.md",
						"section_heading": "Restart Service",
						"metadata_confidence": 0.95,
						"confidentiality_level": "internal",
						"provenance": {"loader_version": "2.0.0"},
					}
				],
			)
			keyword_index_path.write_text(
				json.dumps({"postings": {"restart": [chunk_id], "service": [chunk_id], "status": [chunk_id]}}),
				encoding="utf-8",
			)
			vector_index_path.write_text(
				json.dumps(
					{"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"restart": 2.0, "service": 1.5, "status": 1.0}}}}
				),
				encoding="utf-8",
			)

			result = run_howto_workflow(
				task="How do I restart my-service and verify it is healthy?",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=HowToWorkflowConfig(top_k=3),
				llm_client=_FakeHowToClient(),
			)

			self.assertTrue(result.response.supported)
			self.assertTrue(result.guardrail_status["boundary_allowed"])
			self.assertTrue(result.guardrail_status["citation_ok"])
			self.assertGreaterEqual(len(result.response.citations), 1)
			for section in (
				"## Summary",
				"## Assumptions",
				"## Prerequisites",
				"## Steps",
				"## Commands",
				"## Validation",
				"## Failure Modes",
				"## Sources",
			):
				self.assertIn(section, result.response.answer)

	def test_boundary_blocks_internal_content_for_generic_api_mode(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc2::chunk-0001"
			self._write_jsonl(
				chunks_path,
				[
					{
						"chunk_id": chunk_id,
						"content": "Internal procedure for service restart.",
						"metadata": {"source_file": "doc2.md", "section_heading": "Procedure"},
					}
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{
						"chunk_id": chunk_id,
						"source_file": "doc2.md",
						"section_heading": "Procedure",
						"metadata_confidence": 0.95,
						"confidentiality_level": "internal",
						"provenance": {"loader_version": "2.0.0"},
					}
				],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"procedure": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(
				json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"procedure": 1.0}}}}),
				encoding="utf-8",
			)

			result = run_howto_workflow(
				task="Show the procedure",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=HowToWorkflowConfig(provider_mode="api"),
				llm_client=_FakeHowToClient(),
			)

			self.assertFalse(result.response.supported)
			self.assertFalse(result.guardrail_status["boundary_allowed"])
			self.assertEqual(result.guardrail_status["boundary_reason"], "api_confidentiality_blocked")

	def test_guardrail_preserves_answer_with_review_note_for_command_mismatch(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc3::chunk-0001"
			content = "Restart service using systemctl restart my-service and verify with systemctl status my-service."
			self._write_jsonl(
				chunks_path,
				[
					{
						"chunk_id": chunk_id,
						"content": content,
						"metadata": {"source_file": "doc3.md", "section_heading": "Restart Service"},
					}
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{
						"chunk_id": chunk_id,
						"source_file": "doc3.md",
						"section_heading": "Restart Service",
						"metadata_confidence": 0.95,
						"confidentiality_level": "internal",
						"provenance": {"loader_version": "2.0.0"},
					}
				],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"restart": [chunk_id], "service": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(
				json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"restart": 2.0, "service": 1.0}}}}),
				encoding="utf-8",
			)

			result = run_howto_workflow(
				task="How do I restart a service safely?",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=HowToWorkflowConfig(top_k=3),
				llm_client=_FakeUngroundedCommandClient(),
			)

			self.assertFalse(result.response.supported)
			self.assertFalse(result.guardrail_status["citation_ok"])
			self.assertIn("## Commands", result.response.answer)
			self.assertIn("sudo systemctl list-units --type=timer", result.response.answer)
			self.assertIn("## Guardrail Review", result.response.answer)

	def test_commands_injected_from_backtick_command_reference(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_id = "doc4::chunk-0001"
			content = "## Command Reference\n- `df -h`: Show disk usage.\n- `du -sh /var/log/*`: Show largest directories."
			self._write_jsonl(
				chunks_path,
				[
					{
						"chunk_id": chunk_id,
						"content": content,
						"metadata": {"source_file": "doc4.md", "section_heading": "Command Reference"},
					}
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{
						"chunk_id": chunk_id,
						"source_file": "doc4.md",
						"section_heading": "Command Reference",
						"metadata_confidence": 0.95,
						"confidentiality_level": "internal",
						"provenance": {"loader_version": "2.0.0"},
					}
				],
			)
			keyword_index_path.write_text(
				json.dumps({"postings": {"disk": [chunk_id], "usage": [chunk_id], "directories": [chunk_id]}}),
				encoding="utf-8",
			)
			vector_index_path.write_text(
				json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"disk": 2.0, "usage": 1.0}}}}),
				encoding="utf-8",
			)

			result = run_howto_workflow(
				task="How do I check disk usage?",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=HowToWorkflowConfig(top_k=3),
				llm_client=_FakeHowToClient(),
			)

			self.assertIn("df -h", result.response.answer)
			self.assertIn("du -sh /var/log/*", result.response.answer)


if __name__ == "__main__":
	unittest.main()