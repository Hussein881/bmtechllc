"""Unit tests for the Phase 5 curation workflow baseline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig, run_curation_workflow


class CurationWorkflowTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_curation_workflow_surfaces_duplicate_or_missing_proposals(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"

			chunk_a = "doc1::chunk-0001"
			chunk_b = "doc1::chunk-0002"
			duplicate_content = "Restart my-service safely and verify status using systemctl and journalctl."
			self._write_jsonl(
				chunks_path,
				[
					{"chunk_id": chunk_a, "content": duplicate_content, "metadata": {"source_file": "sample_runbook.md", "section_heading": "Restart Service"}},
					{"chunk_id": chunk_b, "content": duplicate_content, "metadata": {"source_file": "sample_runbook.md", "section_heading": "Restart Service"}},
				],
			)
			self._write_jsonl(
				metadata_path,
				[
					{"chunk_id": chunk_a, "source_file": "sample_runbook.md", "section_heading": "Restart Service", "metadata_confidence": 0.95, "confidentiality_level": "internal", "provenance": {}},
					{"chunk_id": chunk_b, "source_file": "sample_runbook.md", "section_heading": "Restart Service", "metadata_confidence": 0.95, "confidentiality_level": "internal", "provenance": {}},
				],
			)
			keyword_index_path.write_text(
				json.dumps(
					{
						"postings": {
							"restart": [chunk_a, chunk_b],
							"service": [chunk_a, chunk_b],
							"systemctl": [chunk_a, chunk_b],
						}
					}
				),
				encoding="utf-8",
			)
			vector_index_path.write_text(
				json.dumps(
					{
						"model": "tfidf-lite",
						"vectors": {
							chunk_a: {"weights": {"restart": 1.0, "service": 1.0}},
							chunk_b: {"weights": {"restart": 1.0, "service": 1.0}},
						},
					}
				),
				encoding="utf-8",
			)

			result = run_curation_workflow(
				topic="restart service reliability",
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=CurationWorkflowConfig(top_k=8),
			)

			self.assertGreaterEqual(len(result.retrieval_hits), 1)
			self.assertGreaterEqual(len(result.proposals), 1)
			proposal_types = {proposal.proposal_type for proposal in result.proposals}
			self.assertTrue("duplicate_content" in proposal_types or "missing_knowledge" in proposal_types)


if __name__ == "__main__":
	unittest.main()
