"""Unit tests for Phase 2 QA workflow baseline."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.workflows.qa_workflow import QAWorkflowConfig, run_qa_workflow


class QAWorkflowTests(unittest.TestCase):
    def _write_jsonl(self, path: Path, rows: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    def test_supported_answer_includes_citations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            chunks_path = root / "chunks.jsonl"
            metadata_path = root / "metadata.parquet"
            keyword_index_path = root / "keyword.json"
            vector_index_path = root / "vector.json"

            chunk_id = "doc1::chunk-0001"
            self._write_jsonl(
                chunks_path,
                [
                    {
                        "chunk_id": chunk_id,
                        "content": "Restart service with systemctl restart my-service and verify health check.",
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
                        "metadata_confidence": 0.9,
                        "confidentiality_level": "internal",
                        "provenance": {
                            "loader_version": "2.0.0",
                            "chunker_version": "2.0.0",
                            "extractor_version": "2.0.0",
                            "ingested_at": "2026-07-03T00:00:00Z",
                        },
                    }
                ],
            )
            keyword_index_path.write_text(
                json.dumps({"postings": {"restart": [chunk_id], "service": [chunk_id]}}),
                encoding="utf-8",
            )
            vector_index_path.write_text(
                json.dumps(
                    {
                        "model": "tfidf-lite",
                        "vectors": {
                            chunk_id: {
                                "weights": {"restart": 2.0, "service": 1.5, "systemctl": 1.0}
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = run_qa_workflow(
                question="How do I restart a service?",
                chunks_path=chunks_path,
                metadata_path=metadata_path,
                keyword_index_path=keyword_index_path,
                vector_index_path=vector_index_path,
                config=QAWorkflowConfig(top_k=3),
            )

            self.assertTrue(result.response.supported)
            self.assertGreaterEqual(len(result.response.citations), 1)
            self.assertTrue(result.guardrail_status["citation_ok"])

    def test_unsupported_when_no_hits_after_confidentiality_filter(self) -> None:
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
                        "content": "Confidential procedure text.",
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
                        "confidentiality_level": "confidential",
                        "provenance": {
                            "loader_version": "2.0.0",
                            "chunker_version": "2.0.0",
                            "extractor_version": "2.0.0",
                            "ingested_at": "2026-07-03T00:00:00Z",
                        },
                    }
                ],
            )
            keyword_index_path.write_text(
                json.dumps({"postings": {"procedure": [chunk_id]}}),
                encoding="utf-8",
            )
            vector_index_path.write_text(
                json.dumps({"model": "tfidf-lite", "vectors": {chunk_id: {"weights": {"procedure": 1.0}}}}),
                encoding="utf-8",
            )

            result = run_qa_workflow(
                question="Show procedure",
                chunks_path=chunks_path,
                metadata_path=metadata_path,
                keyword_index_path=keyword_index_path,
                vector_index_path=vector_index_path,
                config=QAWorkflowConfig(allowed_confidentiality=("public",)),
            )

            self.assertFalse(result.response.supported)
            self.assertEqual(result.response.citations, [])
            self.assertFalse(result.guardrail_status["supported"])


if __name__ == "__main__":
    unittest.main()
