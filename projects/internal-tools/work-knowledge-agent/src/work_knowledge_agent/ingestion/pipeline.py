"""Ingestion pipeline: load -> chunk -> metadata -> artifact write."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

from work_knowledge_agent.ingestion.chunking import CHUNKER_VERSION, chunk_text
from work_knowledge_agent.ingestion.loaders import code_loader, log_loader, markdown_loader, pdf_loader, text_loader
from work_knowledge_agent.ingestion.manifest import IngestionManifest, ManifestEntry
from work_knowledge_agent.ingestion.metadata_extractor import (
	EXTRACTOR_VERSION,
	MetadataDefaults,
	base_metadata,
	evaluate_metadata,
	extract_commands,
	extract_errors,
	extract_section_heading,
	merge_tags,
)
from work_knowledge_agent.ingestion.models import LoadedDocument, QuarantineRecord
from work_knowledge_agent.ingestion.preprocessing import normalize_text, normalized_content_hash, sniff_loader_key

LOADER_VERSION = "2.0.0"

LoaderFn = Callable[[Path], LoadedDocument]

SUPPORTED_LOADERS: Dict[str, LoaderFn] = {
	".md": markdown_loader.load,
	".txt": text_loader.load,
	".rst": text_loader.load,
	".log": log_loader.load,
	".py": code_loader.load,
	".sh": code_loader.load,
	".yaml": code_loader.load,
	".yml": code_loader.load,
	".json": code_loader.load,
	".toml": code_loader.load,
	".pdf": pdf_loader.load,
}

FALLBACK_LOADERS: Dict[str, LoaderFn] = {
	"markdown": markdown_loader.load,
	"text": text_loader.load,
	"log": log_loader.load,
	"code": code_loader.load,
}


@dataclass(frozen=True)
class PipelineChunk:
	chunk_id: str
	content: str
	metadata: dict


@dataclass(frozen=True)
class IngestionReport:
	files_seen: int
	files_processed: int
	files_skipped: int
	chunks_written: int
	unsupported_files: List[str]
	failed_files: List[str]
	quarantined_files: List[str]
	deleted_files: List[str]
	chunks_path: str
	metadata_path: str
	quarantine_path: str
	manifest_path: str
	stage_times_ms: dict


def discover_files(raw_dir: Path) -> List[Path]:
	paths = [p for p in raw_dir.rglob("*") if p.is_file()]
	return sorted(paths)


def _select_loader(path: Path, sample_text: str) -> Tuple[LoaderFn | None, str]:
	loader = SUPPORTED_LOADERS.get(path.suffix.lower())
	if loader is not None:
		return loader, path.suffix.lower() or "known"

	fallback_key = sniff_loader_key(path=path, sample_text=sample_text)
	if fallback_key is None:
		return None, "unsupported"
	return FALLBACK_LOADERS.get(fallback_key), f"fallback:{fallback_key}"


def _read_sample_text(path: Path, max_bytes: int = 4096) -> str:
	try:
		with path.open("rb") as handle:
			blob = handle.read(max_bytes)
		return blob.decode("utf-8", errors="replace")
	except Exception:
		return ""


def _deterministic_chunk_id(source_file: str, chunk_index: int) -> str:
	raw = f"{source_file}|{chunk_index}|{CHUNKER_VERSION}"
	digest = sha256(raw.encode("utf-8")).hexdigest()[:16]
	return f"{source_file}::chunk-{chunk_index:04d}-{digest}"


def _build_chunk_records(
	source_file: str,
	text: str,
	defaults: MetadataDefaults,
	content_hash: str,
	loader_route: str,
	chunk_size: int,
	overlap: int,
	quarantine: List[QuarantineRecord],
) -> Tuple[List[PipelineChunk], bool]:
	chunks = chunk_text(text=text, chunk_size=chunk_size, overlap=overlap)
	records: List[PipelineChunk] = []
	has_flag = False
	for idx, content in enumerate(chunks):
		metadata = base_metadata(path=Path(source_file), defaults=defaults)
		metadata["section_heading"] = extract_section_heading(content)
		metadata["section_heading_confidence"] = 0.9 if metadata["section_heading"] != "untitled-section" else 0.3
		metadata["extracted_commands"] = extract_commands(content)
		metadata["extracted_errors"] = extract_errors(content)
		ext = Path(source_file).suffix.lower().lstrip(".")
		metadata["tags"] = merge_tags(metadata.get("tags", []), [ext or "unknown"])
		metadata["doc_type_confidence"] = 0.9
		metadata["metadata_confidence"] = min(
			metadata["doc_type_confidence"],
			metadata["section_heading_confidence"],
		)
		metadata["provenance"] = {
			"loader_version": LOADER_VERSION,
			"chunker_version": CHUNKER_VERSION,
			"extractor_version": EXTRACTOR_VERSION,
			"ingested_at": datetime.now(tz=timezone.utc).isoformat(),
			"content_hash": content_hash,
			"loader_route": loader_route,
		}

		evaluation = evaluate_metadata(metadata)
		if evaluation.status == "reject":
			quarantine.append(
				QuarantineRecord(
					source_file=source_file,
					reason="metadata_reject",
					detail=";".join(evaluation.reasons),
					stage="metadata_validation",
					content_hash=content_hash,
				)
			)
			return [], has_flag
		if evaluation.status == "flag":
			has_flag = True
			metadata["metadata_validation_flags"] = list(evaluation.reasons)

		chunk_id = _deterministic_chunk_id(source_file=source_file, chunk_index=idx)
		records.append(PipelineChunk(chunk_id=chunk_id, content=content, metadata=metadata))
	return records, has_flag


def _read_existing_chunks(chunks_path: Path) -> List[PipelineChunk]:
	if not chunks_path.exists():
		return []
	records: List[PipelineChunk] = []
	with chunks_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			payload = json.loads(line)
			records.append(
				PipelineChunk(
					chunk_id=payload.get("chunk_id", ""),
					content=payload.get("content", ""),
					metadata=payload.get("metadata", {}),
				)
			)
	return records


def _safe_atomic_write_jsonl(output_path: Path, rows: Iterable[dict]) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	tmp_name = f".{output_path.name}.{uuid.uuid4().hex}.tmp"
	tmp_path = output_path.parent / tmp_name
	with tmp_path.open("w", encoding="utf-8") as handle:
		for row in rows:
			handle.write(json.dumps(row, ensure_ascii=True) + "\n")
	tmp_path.replace(output_path)


def _build_quarantine_rows(records: Iterable[QuarantineRecord]) -> List[dict]:
	rows: List[dict] = []
	for record in records:
		rows.append(
			{
				"source_file": record.source_file,
				"reason": record.reason,
				"detail": record.detail,
				"stage": record.stage,
				"content_hash": record.content_hash,
				"timestamp": datetime.now(tz=timezone.utc).isoformat(),
			}
		)
	return rows


def ingest_directory(
	raw_dir: Path,
	chunks_output: Path,
	metadata_output: Path,
	manifest_path: Path,
	quarantine_output: Path,
	defaults: MetadataDefaults | None = None,
	chunk_size: int = 1200,
	overlap: int = 150,
) -> IngestionReport:
	defaults_cfg = defaults or MetadataDefaults()
	raw = raw_dir.resolve()
	chunks_output.parent.mkdir(parents=True, exist_ok=True)
	metadata_output.parent.mkdir(parents=True, exist_ok=True)
	quarantine_output.parent.mkdir(parents=True, exist_ok=True)
	manifest = IngestionManifest(manifest_path)

	start_total = time.perf_counter()
	start_discovery = time.perf_counter()
	files = discover_files(raw)
	discovery_ms = (time.perf_counter() - start_discovery) * 1000.0

	start_manifest = time.perf_counter()
	existing_manifest = manifest.fetch_all()
	existing_paths = [str(path.resolve()) for path in files]
	manifest.mark_deleted_missing(existing_paths)
	current_manifest = manifest.fetch_all()
	deleted_files = sorted([path for path, entry in current_manifest.items() if entry.status == "deleted"])
	manifest_ms = (time.perf_counter() - start_manifest) * 1000.0

	start_ingest = time.perf_counter()
	all_records = _read_existing_chunks(chunks_output)
	if deleted_files:
		all_records = [r for r in all_records if str(r.metadata.get("source_file", "")) not in set(deleted_files)]
	retained_records = list(all_records)
	rebuilt_records: List[PipelineChunk] = []

	replace_sources: set[str] = set()
	quarantine_records: List[QuarantineRecord] = []
	unsupported_files: List[str] = []
	failed_files: List[str] = []
	quarantined_files: List[str] = []
	skipped = 0
	processed = 0

	for path in files:
		source_file = str(path.resolve())
		entry = existing_manifest.get(source_file)
		mtime = path.stat().st_mtime

		if (
			entry is not None
			and entry.status in {"active", "flagged", "quarantined"}
			and entry.mtime == mtime
			and entry.loader_version == LOADER_VERSION
			and entry.chunker_version == CHUNKER_VERSION
			and entry.extractor_version == EXTRACTOR_VERSION
		):
			skipped += 1
			continue

		sample = _read_sample_text(path)
		loader, loader_route = _select_loader(path, sample)
		if loader is None:
			unsupported_files.append(source_file)
			replace_sources.add(source_file)
			quarantine_records.append(
				QuarantineRecord(
					source_file=source_file,
					reason="unsupported_file_type",
					detail="No loader route matched",
					stage="loader_selection",
				)
			)
			manifest.upsert(
				ManifestEntry(
					file_path=source_file,
					content_hash="",
					size_bytes=path.stat().st_size,
					mtime=mtime,
					last_ingested_at=datetime.now(tz=timezone.utc).isoformat(),
					loader_version=LOADER_VERSION,
					chunker_version=CHUNKER_VERSION,
					extractor_version=EXTRACTOR_VERSION,
					chunk_count=0,
					status="quarantined",
					error_detail="unsupported_file_type",
				)
			)
			continue

		try:
			loaded = loader(path)
			normalized_text = normalize_text(loaded.text)
			content_hash = normalized_content_hash(normalized_text)

			if (
				entry is not None
				and entry.status == "active"
				and entry.content_hash == content_hash
				and entry.loader_version == LOADER_VERSION
				and entry.chunker_version == CHUNKER_VERSION
				and entry.extractor_version == EXTRACTOR_VERSION
			):
				manifest.upsert(
					ManifestEntry(
						file_path=source_file,
						content_hash=content_hash,
						size_bytes=loaded.size_bytes,
						mtime=mtime,
						last_ingested_at=entry.last_ingested_at,
						loader_version=LOADER_VERSION,
						chunker_version=CHUNKER_VERSION,
						extractor_version=EXTRACTOR_VERSION,
						chunk_count=entry.chunk_count,
						status="active",
						error_detail="",
					)
				)
				skipped += 1
				continue

			if loaded.media_type == "application/pdf" and ("pdf_low_text_extraction" in loaded.warnings or len(normalized_text) < 25):
				quarantined_files.append(source_file)
				quarantine_records.append(
					QuarantineRecord(
						source_file=source_file,
						reason="pdf_low_text_extraction",
						detail="PDF has low extractable text content",
						stage="loader",
						content_hash=content_hash,
					)
				)
				replace_sources.add(source_file)
				manifest.upsert(
					ManifestEntry(
						file_path=source_file,
						content_hash=content_hash,
						size_bytes=loaded.size_bytes,
						mtime=mtime,
						last_ingested_at=datetime.now(tz=timezone.utc).isoformat(),
						loader_version=LOADER_VERSION,
						chunker_version=CHUNKER_VERSION,
						extractor_version=EXTRACTOR_VERSION,
						chunk_count=0,
						status="quarantined",
						error_detail="pdf_low_text_extraction",
					)
				)
				continue

			records, has_flag = _build_chunk_records(
				source_file=source_file,
				text=normalized_text,
				defaults=defaults_cfg,
				content_hash=content_hash,
				loader_route=loader_route,
				chunk_size=chunk_size,
				overlap=overlap,
				quarantine=quarantine_records,
			)
			metadata_rejected = any(
				rec.source_file == source_file and rec.reason == "metadata_reject"
				for rec in quarantine_records
			)
			if metadata_rejected:
				replace_sources.add(source_file)
				manifest.upsert(
					ManifestEntry(
						file_path=source_file,
						content_hash=content_hash,
						size_bytes=loaded.size_bytes,
						mtime=mtime,
						last_ingested_at=datetime.now(tz=timezone.utc).isoformat(),
						loader_version=LOADER_VERSION,
						chunker_version=CHUNKER_VERSION,
						extractor_version=EXTRACTOR_VERSION,
						chunk_count=0,
						status="quarantined",
						error_detail="metadata_reject",
					)
				)
				quarantined_files.append(source_file)
				continue

			replace_sources.add(source_file)
			if records:
				rebuilt_records.extend(records)
			processed += 1
			status = "active" if not has_flag else "flagged"
			error_detail = "" if not has_flag else "metadata_flag"
			manifest.upsert(
				ManifestEntry(
					file_path=source_file,
					content_hash=content_hash,
					size_bytes=loaded.size_bytes,
					mtime=mtime,
					last_ingested_at=datetime.now(tz=timezone.utc).isoformat(),
					loader_version=LOADER_VERSION,
					chunker_version=CHUNKER_VERSION,
					extractor_version=EXTRACTOR_VERSION,
					chunk_count=len(records),
					status=status,
					error_detail=error_detail,
				)
			)
			if has_flag:
				quarantined_files.append(source_file)
		except Exception as exc:
			failed_files.append(source_file)
			replace_sources.add(source_file)
			manifest.upsert(
				ManifestEntry(
					file_path=source_file,
					content_hash="",
					size_bytes=path.stat().st_size,
					mtime=mtime,
					last_ingested_at=datetime.now(tz=timezone.utc).isoformat(),
					loader_version=LOADER_VERSION,
					chunker_version=CHUNKER_VERSION,
					extractor_version=EXTRACTOR_VERSION,
					chunk_count=0,
					status="quarantined",
					error_detail=str(exc),
				)
			)
			quarantine_records.append(
				QuarantineRecord(
					source_file=source_file,
					reason="loader_or_processing_failure",
					detail=str(exc),
					stage="ingestion",
				)
			)

	if replace_sources:
		retained_records = [
			r for r in retained_records if str(r.metadata.get("source_file", "")) not in replace_sources
		]
	all_records = retained_records + rebuilt_records

	ingest_ms = (time.perf_counter() - start_ingest) * 1000.0

	start_write = time.perf_counter()
	chunk_rows = [{"chunk_id": r.chunk_id, "content": r.content, "metadata": r.metadata} for r in all_records]
	metadata_rows = [{"chunk_id": r.chunk_id, **r.metadata} for r in all_records]
	quarantine_rows = _build_quarantine_rows(quarantine_records)

	_safe_atomic_write_jsonl(chunks_output, chunk_rows)
	_safe_atomic_write_jsonl(metadata_output, metadata_rows)
	_safe_atomic_write_jsonl(quarantine_output, quarantine_rows)
	write_ms = (time.perf_counter() - start_write) * 1000.0
	total_ms = (time.perf_counter() - start_total) * 1000.0

	stage_times_ms = {
		"discovery": round(discovery_ms, 3),
		"manifest": round(manifest_ms, 3),
		"ingestion": round(ingest_ms, 3),
		"artifact_write": round(write_ms, 3),
		"total": round(total_ms, 3),
	}

	return IngestionReport(
		files_seen=len(files),
		files_processed=processed,
		files_skipped=skipped,
		chunks_written=len(all_records),
		unsupported_files=unsupported_files,
		failed_files=failed_files,
		quarantined_files=sorted(set(quarantined_files + [q.source_file for q in quarantine_records])),
		deleted_files=deleted_files,
		chunks_path=str(chunks_output),
		metadata_path=str(metadata_output),
		quarantine_path=str(quarantine_output),
		manifest_path=str(manifest_path),
		stage_times_ms=stage_times_ms,
	)

