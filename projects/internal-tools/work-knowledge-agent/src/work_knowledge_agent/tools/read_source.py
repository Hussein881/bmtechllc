"""Tool: read_source

Tag: reusable-asset

Purpose:
- Return source snippets by source identifier and optional section.

Status:
- Placeholder module. Implementation scheduled with tool contracts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


def read_source(source_file: str, chunks_path: Path, max_snippets: int = 5) -> List[str]:
	if not chunks_path.exists():
		return []

	snippets: List[str] = []
	with chunks_path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			row = json.loads(line)
			metadata = row.get("metadata", {})
			if str(metadata.get("source_file", "")) != source_file:
				continue
			content = str(row.get("content", "")).strip()
			if content:
				snippets.append(content)
			if len(snippets) >= max_snippets:
				break
	return snippets

