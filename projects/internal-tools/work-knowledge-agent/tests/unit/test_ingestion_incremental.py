"""Unit tests for incremental ingestion behavior."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from work_knowledge_agent.ingestion.metadata_extractor import MetadataDefaults
from work_knowledge_agent.ingestion.pipeline import ingest_directory


class IngestionIncrementalTests(unittest.TestCase):
    def test_incremental_second_run_is_noop_and_chunk_ids_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw = root / "raw"
            processed = root / "processed"
            raw.mkdir(parents=True, exist_ok=True)
            processed.mkdir(parents=True, exist_ok=True)

            source = raw / "runbook.md"
            source.write_text(
                "# Restart Procedure\n\n"
                "Run service restart.\n\n"
                "```bash\nsystemctl restart app\n```\n",
                encoding="utf-8",
            )

            chunks_path = processed / "chunks.jsonl"
            metadata_path = processed / "metadata.parquet"
            quarantine_path = processed / "quarantine.jsonl"
            manifest_path = processed / "manifest.sqlite"

            first = ingest_directory(
                raw_dir=raw,
                chunks_output=chunks_path,
                metadata_output=metadata_path,
                quarantine_output=quarantine_path,
                manifest_path=manifest_path,
                defaults=MetadataDefaults(project="test"),
            )

            self.assertEqual(first.files_seen, 1)
            self.assertEqual(first.files_processed, 1)
            self.assertEqual(first.files_skipped, 0)
            self.assertGreaterEqual(first.chunks_written, 1)

            first_chunk_ids = [
                json.loads(line)["chunk_id"]
                for line in chunks_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertTrue(first_chunk_ids)

            second = ingest_directory(
                raw_dir=raw,
                chunks_output=chunks_path,
                metadata_output=metadata_path,
                quarantine_output=quarantine_path,
                manifest_path=manifest_path,
                defaults=MetadataDefaults(project="test"),
            )

            self.assertEqual(second.files_seen, 1)
            self.assertEqual(second.files_processed, 0)
            self.assertEqual(second.files_skipped, 1)
            self.assertEqual(second.chunks_written, first.chunks_written)

            second_chunk_ids = [
                json.loads(line)["chunk_id"]
                for line in chunks_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(first_chunk_ids, second_chunk_ids)

    def test_unsupported_file_routes_to_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw = root / "raw"
            processed = root / "processed"
            raw.mkdir(parents=True, exist_ok=True)
            processed.mkdir(parents=True, exist_ok=True)

            unsupported = raw / "capture.bin"
            unsupported.write_bytes(b"\x00\x01\x02\x03")

            chunks_path = processed / "chunks.jsonl"
            metadata_path = processed / "metadata.parquet"
            quarantine_path = processed / "quarantine.jsonl"
            manifest_path = processed / "manifest.sqlite"

            report = ingest_directory(
                raw_dir=raw,
                chunks_output=chunks_path,
                metadata_output=metadata_path,
                quarantine_output=quarantine_path,
                manifest_path=manifest_path,
                defaults=MetadataDefaults(project="test"),
            )

            self.assertEqual(report.files_seen, 1)
            self.assertEqual(report.files_processed, 0)
            self.assertEqual(len(report.unsupported_files), 1)
            self.assertGreaterEqual(len(report.quarantined_files), 1)

            rows = [
                json.loads(line)
                for line in quarantine_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["reason"], "unsupported_file_type")
            self.assertEqual(rows[0]["stage"], "loader_selection")


if __name__ == "__main__":
    unittest.main()
