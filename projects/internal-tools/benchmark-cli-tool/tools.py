"""Safe retrieval tools over the project's local document library."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

DOCUMENTS_DIR = Path(__file__).with_name("documents")
_SECTION_PATTERN = re.compile(r"^\s*(?:\d+[.)]\s*)?([^:]{2,100}):(?:\s|$)")
_NUMBERED_HEADING_PATTERN = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+(.{2,100})\s*$")
_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")


def _document_path(filename: str) -> Path | None:
    """Resolve a safe document filename, rejecting paths and traversal."""
    path = Path(filename)
    if path.name != filename:
        return None
    candidate = DOCUMENTS_DIR / path
    return candidate if candidate.is_file() else None


def _section_title(line: str, line_number: int) -> str | None:
    """Infer a section title from a Markdown or numbered policy line."""
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("#"):
        return stripped.lstrip("#").strip()
    match = _SECTION_PATTERN.match(stripped)
    if match:
        return match.group(1).strip()
    numbered_heading = _NUMBERED_HEADING_PATTERN.match(stripped)
    if numbered_heading:
        return numbered_heading.group(1).strip()
    if line_number == 1:
        return stripped.rstrip(":")
    return None


def _section_blocks(text: str) -> list[tuple[str, int, int]]:
    """Return ``(title, start_line, end_line)`` ranges for a document."""
    lines = text.splitlines()
    starts: list[tuple[str, int]] = []
    for number, line in enumerate(lines, start=1):
        title = _section_title(line, number)
        if title:
            starts.append((title, number))
    blocks: list[tuple[str, int, int]] = []
    for index, (title, start) in enumerate(starts):
        end = starts[index + 1][1] - 1 if index + 1 < len(starts) else len(lines)
        blocks.append((title, start, end))
    return blocks


def _normalise_section_name(value: str) -> str:
    """Normalise a section label for tolerant matching."""
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def list_docs() -> list[dict[str, str]]:
    """Return metadata for every text document in the local document library."""
    documents: list[dict[str, str]] = []
    for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8")
            stat = path.stat()
        except OSError:
            continue
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), path.stem)
        year = _YEAR_PATTERN.search(text)
        date = year.group(1) if year else datetime.fromtimestamp(stat.st_mtime).date().isoformat()
        documents.append(
            {"filename": path.name, "title": first_line, "type": "text", "date": date}
        )
    return documents


def search_docs(query: str) -> list[dict[str, str]]:
    """Find lines containing every keyword in *query* and return concise snippets."""
    terms = set(re.findall(r"[\w'-]+", query.casefold()))
    if not terms:
        return []

    matches: list[dict[str, str]] = []
    for metadata in list_docs():
        path = DOCUMENTS_DIR / metadata["filename"]
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        blocks = _section_blocks("\n".join(lines))
        for line_number, line in enumerate(lines, start=1):
            words = set(re.findall(r"[\w'-]+", line.casefold()))
            if not terms.issubset(words):
                continue
            section = next(
                (title for title, start, end in blocks if start <= line_number <= end),
                f"line {line_number}",
            )
            matches.append(
                {
                    "filename": metadata["filename"],
                    "location": f"{section} (line {line_number})",
                    "snippet": line.strip(),
                }
            )
    return matches


def read_doc(filename: str, section: str | None = None) -> str:
    """Read a complete document or one named section, returning safe error text."""
    path = _document_path(filename)
    if path is None:
        return "Error: Document or section not found."
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "Error: Document or section not found."
    if section is None:
        return text

    requested = _normalise_section_name(section)
    blocks = _section_blocks(text)
    exact_matches = [block for block in blocks if _normalise_section_name(block[0]) == requested]
    near_matches = [
        block
        for block in blocks
        if requested and (requested in _normalise_section_name(block[0]) or _normalise_section_name(block[0]) in requested)
    ]
    matches = exact_matches or near_matches
    if len(matches) == 1:
        _, start, end = matches[0]
        lines = text.splitlines()
        return "\n".join(lines[start - 1 : end]).strip()
    return "Error: Document or section not found."


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_docs",
            "description": "List available company documents and their metadata.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search document text for all keywords in a query.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search keywords."}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_doc",
            "description": "Read a document or named section; omit section to inspect the full document when no exact section title is available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Document filename."},
                    "section": {"type": "string", "description": "Optional section title."},
                },
                "required": ["filename"],
                "additionalProperties": False,
            },
        },
    },
]


_TOOL_FUNCTIONS = {"list_docs": list_docs, "search_docs": search_docs, "read_doc": read_doc}


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Execute a named tool with validated arguments and return a safe result."""
    function = _TOOL_FUNCTIONS.get(name)
    if function is None:
        return f"Error: Unknown tool '{name}'."
    try:
        return function(**arguments)
    except (TypeError, ValueError, OSError) as exc:
        return f"Error: Tool '{name}' could not be executed: {exc}"
