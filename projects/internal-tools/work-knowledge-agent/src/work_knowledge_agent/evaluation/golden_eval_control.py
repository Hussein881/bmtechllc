"""Integrity helpers for frozen golden evaluation datasets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GoldenEvalManifest:
	dataset_path: str
	sha256: str
	review_status: str
	reviewer: str
	review_date: str
	notes: str


def compute_sha256(path: Path) -> str:
	return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> GoldenEvalManifest:
	payload = json.loads(path.read_text(encoding="utf-8"))
	if not isinstance(payload, dict):
		raise ValueError("Golden eval manifest must be a JSON object")
	return GoldenEvalManifest(
		dataset_path=str(payload.get("dataset_path", "")),
		sha256=str(payload.get("sha256", "")),
		review_status=str(payload.get("review_status", "unreviewed")),
		reviewer=str(payload.get("reviewer", "")),
		review_date=str(payload.get("review_date", "")),
		notes=str(payload.get("notes", "")),
	)


def verify_golden_dataset(dataset_path: Path, manifest_path: Path) -> dict[str, Any]:
	manifest = load_manifest(manifest_path)
	actual_sha = compute_sha256(dataset_path)
	matched = actual_sha == manifest.sha256
	gate_eligible = matched and manifest.review_status.lower() == "reviewed"
	return {
		"dataset_path": str(dataset_path),
		"manifest_path": str(manifest_path),
		"expected_sha256": manifest.sha256,
		"actual_sha256": actual_sha,
		"hash_match": matched,
		"gate_eligible": gate_eligible,
		"review_status": manifest.review_status,
		"reviewer": manifest.reviewer,
		"review_date": manifest.review_date,
		"notes": manifest.notes,
	}