"""Unit tests for the Phase 5 curation evaluation helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.evaluation.curation_eval import evaluate_curation_cases, load_curation_eval_cases
from work_knowledge_agent.workflows.curation_workflow import CurationWorkflowConfig


class CurationEvalTests(unittest.TestCase):
	def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
		with path.open("w", encoding="utf-8") as handle:
			for row in rows:
				handle.write(json.dumps(row, ensure_ascii=True) + "\n")

	def test_evaluate_curation_cases_reports_metrics(self) -> None:
		with tempfile.TemporaryDirectory() as tmpdir:
			root = Path(tmpdir)
			chunks_path = root / "chunks.jsonl"
			metadata_path = root / "metadata.parquet"
			keyword_index_path = root / "keyword.json"
			vector_index_path = root / "vector.json"
			eval_cases_path = root / "curation_eval_cases.json"

			chunk_id = "doc1::chunk-0001"
			content = "Run service restart with systemctl and collect logs with journalctl."
			self._write_jsonl(
				chunks_path,
				[{"chunk_id": chunk_id, "content": content, "metadata": {"source_file": "sample_runbook.md", "section_heading": "Restart Service"}}],
			)
			self._write_jsonl(
				metadata_path,
				[{"chunk_id": chunk_id, "source_file": "sample_runbook.md", "section_heading": "Restart Service", "metadata_confidence": 0.9, "confidentiality_level": "internal", "provenance": {}}],
			)
			keyword_index_path.write_text(json.dumps({"postings": {"service": [chunk_id], "restart": [chunk_id], "systemctl": [chunk_id]}}), encoding="utf-8")
			vector_index_path.write_text(json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"service": 1.0, "restart": 1.0}}}}), encoding="utf-8")
			eval_cases_path.write_text(
				json.dumps(
					[
						{
							"id": "missing-case",
							"topic": "project x9 postgres failover architecture",
							"expected_types": ["missing_knowledge"],
						}
					],
					ensure_ascii=True,
					indent=2,
				),
				encoding="utf-8",
			)

			cases = load_curation_eval_cases(eval_cases_path)
			report = evaluate_curation_cases(
				cases,
				chunks_path=chunks_path,
				metadata_path=metadata_path,
				keyword_index_path=keyword_index_path,
				vector_index_path=vector_index_path,
				config=CurationWorkflowConfig(),
			)

			self.assertEqual(report["total_cases"], 1)
			self.assertEqual(report["total_runs"], 1)
			self.assertEqual(report["metrics"]["expected_type_match_rate_pct"], 100.0)
			self.assertEqual(report["metrics"]["non_empty_proposal_rate_pct"], 100.0)


if __name__ == "__main__":
	unittest.main()
