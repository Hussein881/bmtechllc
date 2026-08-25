"""Tool: ingest_docs

Tag: reusable-asset

What this tool does:
- Scans raw documents.
- Runs ingestion ( .
- Writes processed artifacts for downstream retrieval/indexing.

Inputs:
- Raw document directory.
- Output paths for chunks and metadata.
- Default metadata values (project/owner/machine/component/mode/confidentiality).

Outputs:
- `data/processed/chunks.jsonl` (or user-provided path)
- `data/processed/metadata.parquet` (JSONL payload during bootstrap)
- `data/processed/quarantine.jsonl`
- `data/processed/manifest.sqlite`
- Console summary report with processed/unsupported/failed counts.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from work_knowledge_agent.ingestion.metadata_extractor import MetadataDefaults
from work_knowledge_agent.ingestion.pipeline import ingest_directory


def _format_duration_ms(milliseconds: float) -> str:
	if milliseconds < 1000.0:
		return f"{milliseconds:.3f}ms"
	seconds = milliseconds / 1000.0
	if seconds < 60.0:
		return f"{seconds:.3f}s"
	minutes = seconds / 60.0
	if minutes < 60.0:
		return f"{minutes:.3f}min"
	hours = minutes / 60.0
	return f"{hours:.3f}hr"


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Ingest documents into chunk and metadata artifacts.")
	parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"), help="Input document directory")
	parser.add_argument(
		"--chunks-output",
		type=Path,
		default=Path("data/processed/chunks.jsonl"),
		help="Output chunks JSONL path",
	)
	parser.add_argument(
		"--metadata-output",
		type=Path,
		default=Path("data/processed/metadata.parquet"),
		help="Output metadata artifact path",
	)
	parser.add_argument(
		"--quarantine-output",
		type=Path,
		default=Path("data/processed/quarantine.jsonl"),
		help="Output quarantine artifact path",
	)
	parser.add_argument(
		"--manifest-path",
		type=Path,
		default=Path("data/processed/manifest.sqlite"),
		help="SQLite manifest path for incremental ingestion",
	)
	parser.add_argument("--project", default="work_knowledge_agent", help="Project metadata value")
	parser.add_argument("--owner", default="unknown", help="Owner metadata value")
	parser.add_argument("--machine", default="unknown", help="Machine metadata value")
	parser.add_argument("--component", default="unknown", help="Component metadata value")
	parser.add_argument("--mode", default="unknown", help="Mode metadata value")
	parser.add_argument(
		"--confidentiality-level",
		default="internal",
		choices=["public", "internal", "confidential"],
		help="Default confidentiality level",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	defaults = MetadataDefaults(
		project=args.project,
		owner=args.owner,
		machine=args.machine,
		component=args.component,
		mode=args.mode,
		confidentiality_level=args.confidentiality_level,
	)

	report = ingest_directory(
		raw_dir=args.raw_dir,
		chunks_output=args.chunks_output,
		metadata_output=args.metadata_output,
		manifest_path=args.manifest_path,
		quarantine_output=args.quarantine_output,
		defaults=defaults,
	)

	print("Ingestion complete")
	print(f"files_seen={report.files_seen}")
	print(f"files_processed={report.files_processed}")
	print(f"files_skipped={report.files_skipped}")
	print(f"chunks_written={report.chunks_written}")
	print(f"unsupported_files={len(report.unsupported_files)}")
	print(f"failed_files={len(report.failed_files)}")
	print(f"quarantined_files={len(report.quarantined_files)}")
	print(f"deleted_files={len(report.deleted_files)}")
	print(f"chunks_path={report.chunks_path}")
	print(f"metadata_path={report.metadata_path}")
	print(f"quarantine_path={report.quarantine_path}")
	print(f"manifest_path={report.manifest_path}")
	for stage, ms in report.stage_times_ms.items():
		print(f"stage_{stage}={_format_duration_ms(ms)}")
		print(f"stage_{stage}_ms={ms}")


if __name__ == "__main__":
	main()

