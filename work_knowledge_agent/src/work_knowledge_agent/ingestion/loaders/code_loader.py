"""Source code loader."""

from __future__ import annotations

from pathlib import Path

from work_knowledge_agent.ingestion.models import LoadedDocument


def load(path: Path) -> LoadedDocument:
	text = path.read_text(encoding="utf-8", errors="replace")
	return LoadedDocument(
		source_path=path,
		text=text,
		size_bytes=path.stat().st_size,
		media_type="text/code",
		structural_hints=["code"],
	)

