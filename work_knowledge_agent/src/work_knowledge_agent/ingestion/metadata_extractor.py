"""Metadata extraction and validation for ingestion chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

EXTRACTOR_VERSION = "2.0.0"

REQUIRED_FIELDS = (
	"source_file",
	"section_heading",
	"project",
	"machine",
	"component",
	"mode",
	"doc_type",
	"date",
	"owner",
	"tags",
	"confidentiality_level",
	"extracted_commands",
	"extracted_errors",
)

COMMAND_RE = re.compile(r"(?m)^\s*(?:\$|sudo\s+|kubectl\s+|docker\s+|python\s+|pip\s+)\S.*$")
ERROR_RE = re.compile(r"(?im)\b(error|exception|traceback|failed|failure|fatal)\b")
HEADING_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$")


class MetadataValidationError(ValueError):
	"""Raised when chunk metadata does not satisfy required schema."""


@dataclass(frozen=True)
class MetadataEvaluation:
	status: str  # pass | flag | reject
	reasons: List[str]


@dataclass(frozen=True)
class MetadataDefaults:
	project: str = "work_knowledge_agent"
	machine: str = "unknown"
	component: str = "unknown"
	mode: str = "unknown"
	owner: str = "unknown"
	confidentiality_level: str = "internal"
	tags: tuple[str, ...] = ("ingested",)


def infer_doc_type(path: Path) -> str:
	suffix = path.suffix.lower()
	if suffix == ".md":
		return "readme"
	if suffix in {".txt", ".rst"}:
		return "note"
	if suffix == ".log":
		return "log"
	if suffix == ".pdf":
		return "runbook"
	if suffix in {".py", ".sh", ".yaml", ".yml", ".json", ".toml"}:
		return "script"
	return "document"


def extract_section_heading(chunk_text: str) -> str:
	match = HEADING_RE.search(chunk_text or "")
	if match:
		return match.group(1).strip()
	return "untitled-section"


def extract_commands(text: str) -> List[str]:
	return [line.strip() for line in COMMAND_RE.findall(text or "")]


def extract_errors(text: str) -> List[str]:
	errors: List[str] = []
	for line in (text or "").splitlines():
		if ERROR_RE.search(line):
			trimmed = line.strip()
			if trimmed:
				errors.append(trimmed)
	return errors


def base_metadata(path: Path, defaults: MetadataDefaults | None = None) -> Dict[str, object]:
	cfg = defaults or MetadataDefaults()
	now_iso = datetime.now(tz=timezone.utc).date().isoformat()
	return {
		"source_file": str(path),
		"section_heading": "untitled-section",
		"project": cfg.project,
		"machine": cfg.machine,
		"component": cfg.component,
		"mode": cfg.mode,
		"doc_type": infer_doc_type(path),
		"date": now_iso,
		"owner": cfg.owner,
		"tags": list(cfg.tags),
		"confidentiality_level": cfg.confidentiality_level,
		"extracted_commands": [],
		"extracted_errors": [],
		"doc_type_confidence": 0.9,
		"section_heading_confidence": 0.2,
		"metadata_confidence": 0.6,
		"provenance": {
			"loader_version": "2.0.0",
			"chunker_version": "2.0.0",
			"extractor_version": EXTRACTOR_VERSION,
			"ingested_at": datetime.now(tz=timezone.utc).isoformat(),
		},
	}


def validate_metadata(metadata: Dict[str, object]) -> None:
	missing = [field for field in REQUIRED_FIELDS if field not in metadata]
	if missing:
		raise MetadataValidationError(f"Missing required metadata fields: {', '.join(missing)}")

	if not isinstance(metadata["tags"], list):
		raise MetadataValidationError("metadata.tags must be a list")
	if not isinstance(metadata["extracted_commands"], list):
		raise MetadataValidationError("metadata.extracted_commands must be a list")
	if not isinstance(metadata["extracted_errors"], list):
		raise MetadataValidationError("metadata.extracted_errors must be a list")

	for key in (
		"source_file",
		"section_heading",
		"project",
		"machine",
		"component",
		"mode",
		"doc_type",
		"date",
		"owner",
		"confidentiality_level",
	):
		value = metadata.get(key)
		if not isinstance(value, str) or not value.strip():
			raise MetadataValidationError(f"metadata.{key} must be a non-empty string")

	for key in ("doc_type_confidence", "section_heading_confidence", "metadata_confidence"):
		value = metadata.get(key)
		if not isinstance(value, (int, float)):
			raise MetadataValidationError(f"metadata.{key} must be numeric")
		if value < 0.0 or value > 1.0:
			raise MetadataValidationError(f"metadata.{key} must be in range [0,1]")

	provenance = metadata.get("provenance")
	if not isinstance(provenance, dict):
		raise MetadataValidationError("metadata.provenance must be a dictionary")
	for key in ("loader_version", "chunker_version", "extractor_version", "ingested_at"):
		value = provenance.get(key)
		if not isinstance(value, str) or not value.strip():
			raise MetadataValidationError(f"metadata.provenance.{key} must be a non-empty string")


def evaluate_metadata(metadata: Dict[str, object]) -> MetadataEvaluation:
	"""Evaluate metadata as pass, flag, or reject with reasons."""
	try:
		validate_metadata(metadata)
	except MetadataValidationError as exc:
		return MetadataEvaluation(status="reject", reasons=[str(exc)])

	reasons: List[str] = []
	if float(metadata.get("metadata_confidence", 0.0)) < 0.6:
		reasons.append("metadata_confidence_below_threshold")
	if str(metadata.get("section_heading", "")).strip().lower() == "untitled-section":
		reasons.append("missing_section_heading")

	if reasons:
		return MetadataEvaluation(status="flag", reasons=reasons)
	return MetadataEvaluation(status="pass", reasons=[])


def merge_tags(base: Iterable[str], extra: Iterable[str]) -> List[str]:
	seen = set()
	merged: List[str] = []
	for item in list(base) + list(extra):
		clean = str(item).strip()
		if clean and clean not in seen:
			seen.add(clean)
			merged.append(clean)
	return merged

