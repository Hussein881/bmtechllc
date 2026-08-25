"""CLI for idempotent local-source ingestion into the pgvector chunk store."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import ChunkMetadata
from ..paths import DOCUMENTS_DIR
from ..providers.openai import embed_texts
from ..storage.postgres import (
    create_indexes,
    delete_source,
    existing_hashes,
    initialize_database,
    upsert_chunks,
)
from .chunk import Chunk, chunk_units
from .clean import RawUnit, parse_by_type

DEFAULT_SOURCE_DIR = DOCUMENTS_DIR


def source_type_for(path: Path) -> str:
    lowered = path.name.casefold()
    if "discord" in lowered or path.parent.name.casefold() == "discord":
        return "discord"
    if "transcript" in lowered or path.parent.name.casefold() in {"transcripts", "meetings"}:
        return "transcript"
    return "policy_doc"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _date_range(units: Iterable[RawUnit]) -> tuple[str | None, str | None]:
    values = [unit.timestamp for unit in units if unit.timestamp]
    if not values:
        return None, None
    return min(values).date().isoformat(), max(values).date().isoformat()


def _source_date(path: Path) -> str:
    """Choose a stable source date for policy documents without timestamps."""
    try:
        year = re.search(r"\b20\d{2}\b", path.read_text(encoding="utf-8"))
    except OSError:
        year = None
    return year.group(0) if year else datetime.fromtimestamp(path.stat().st_mtime, UTC).date().isoformat()


def _speakers_in_order(units: Iterable[RawUnit]) -> list[str]:
    seen: set[str] = set()
    speakers: list[str] = []
    for unit in units:
        if unit.speaker and unit.speaker not in seen:
            speakers.append(unit.speaker)
            seen.add(unit.speaker)
    return speakers


def metadata_for(chunk: Chunk, path: Path, source_type: str) -> ChunkMetadata:
    first = chunk.units[0]
    start, end = _date_range(chunk.units)
    common: dict[str, Any] = {
        "source_type": source_type,
        "date": start or _source_date(path),
        "ingested_at": datetime.now(UTC).isoformat(),
        "message_count": len(chunk.units),
        "split_unit": chunk.split_unit,
        "embed_prefix": "",
    }
    if source_type == "discord":
        common.update(
            channel=str(first.extra.get("channel", path.stem)),
            date_start=start or datetime.now(UTC).date().isoformat(),
            date_end=end or start or datetime.now(UTC).date().isoformat(),
            speakers=_speakers_in_order(chunk.units),
        )
    elif source_type == "transcript":
        common.update(
            meeting=str(first.extra.get("meeting", path.stem)),
            speakers=_speakers_in_order(chunk.units),
        )
        if first.extra.get("section"):
            common["section"] = str(first.extra["section"])
    else:
        common.update(section=str(first.extra.get("section", path.stem)))
    return ChunkMetadata.model_validate(common)


def embedding_input(chunk: Chunk, metadata: ChunkMetadata, source_filename: str) -> str:
    """Create the provenance header supplied to the embedding model."""
    return f"{embedding_prefix(metadata, source_filename)}\n\n{chunk.text}"


def embedding_prefix(metadata: ChunkMetadata, source_filename: str) -> str:
    """Return the provenance header used only at embedding time."""
    if metadata.source_type == "policy_doc":
        header = f"Policy document: {source_filename}; section: {metadata.section}."
    elif metadata.source_type == "discord":
        header = f"Discord channel: {metadata.channel}; dates: {metadata.date_start} to {metadata.date_end}."
    else:
        header = f"Meeting transcript: {metadata.meeting}; date: {metadata.date or 'unknown'}; section: {metadata.section or 'general'}."
    return header


def discover_sources(source_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_dir.rglob("*")
        if path.is_file() and path.suffix.casefold() in {".txt", ".json", ".md"}
    )


def ingest_source(path: Path, *, dry_run: bool, force: bool, batch_size: int = 128) -> dict[str, Any]:
    source_type = source_type_for(path)
    chunks = chunk_units(parse_by_type(path))
    prepared = [
        (chunk, metadata_for(chunk, path, source_type))
        for chunk in chunks
        if chunk.text.strip()
    ]
    prepared = [
        (chunk, metadata.model_copy(update={"embed_prefix": embedding_prefix(metadata, path.name)}))
        for chunk, metadata in prepared
    ]
    hashes = {content_hash(chunk.text) for chunk, _ in prepared}
    result: dict[str, Any] = {
        "source": str(path),
        "source_type": source_type,
        "chunks": len(prepared),
        "tokens": sum(chunk.token_count for chunk, _ in prepared),
        "inserted": 0,
        "skipped": 0,
        "dry_run": dry_run,
    }
    if dry_run:
        return result

    initialize_database()
    source_filename = path.name
    if force:
        delete_source(source_filename)
        known_hashes: set[str] = set()
    else:
        known_hashes = existing_hashes(hashes)
    pending = [(chunk, metadata) for chunk, metadata in prepared if content_hash(chunk.text) not in known_hashes]
    result["skipped"] = len(prepared) - len(pending)
    if not pending:
        return result

    inputs = [embedding_input(chunk, metadata, path.name) for chunk, metadata in pending]
    vectors: list[list[float]] = []
    for start in range(0, len(inputs), batch_size):
        batch = inputs[start : start + batch_size]
        for attempt in range(3):
            try:
                vectors.extend(
                    embed_texts(batch)
                )
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
    rows = [
        {
            "source_file": source_filename,
            "chunk_index": index,
            "chunk_text": chunk.text,
            "content_sha256": content_hash(chunk.text),
            "token_count": chunk.token_count,
            "metadata": metadata.model_dump(mode="json"),
            "embedding": vector,
        }
        for index, ((chunk, metadata), vector) in enumerate(zip(pending, vectors, strict=True))
    ]
    upsert_chunks(rows)
    result["inserted"] = len(rows)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--only", help="Glob pattern selecting source files (for example '*discord*.json').")
    parser.add_argument("--batch-size", type=int, default=128, help="Embedding inputs per request (1-128).")
    parser.add_argument("--dry-run", action="store_true", help="Parse/chunk and estimate cost without API or database writes.")
    parser.add_argument("--force", action="store_true", help="Replace existing chunks for each supplied source.")
    parser.add_argument("--create-indexes", action="store_true", help="Create HNSW/metadata indexes after ingestion.")
    args = parser.parse_args()
    if not args.source_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {args.source_dir}")
    if not 1 <= args.batch_size <= 128:
        raise SystemExit("--batch-size must be between 1 and 128.")
    sources = discover_sources(args.source_dir)
    if args.only:
        sources = [path for path in sources if path.match(args.only)]
    reports = [
        ingest_source(path, dry_run=args.dry_run, force=args.force, batch_size=args.batch_size)
        for path in sources
    ]
    if args.create_indexes and not args.dry_run:
        create_indexes()
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
