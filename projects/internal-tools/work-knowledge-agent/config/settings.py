"""Runtime settings for Work Knowledge Agent.

This module intentionally avoids third-party dependencies so bootstrap remains
portable in clean environments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _to_bool(value: str, default: bool = False) -> bool:
	if not value:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class RetrievalSettings:
	top_k: int = 8
	rerank_top_k: int = 20


@dataclass(frozen=True)
class SecuritySettings:
	default_confidentiality: str = "internal"
	block_external_when_confidential: bool = True
	require_citations: bool = True


@dataclass(frozen=True)
class RuntimeSettings:
	log_level: str = "INFO"
	enable_debug: bool = False


@dataclass(frozen=True)
class AppSettings:
	project_root: Path
	data_dir: Path
	raw_data_dir: Path
	processed_data_dir: Path
	index_dir: Path
	eval_dir: Path
	retrieval: RetrievalSettings
	security: SecuritySettings
	runtime: RuntimeSettings


def load_settings(project_root: Path | None = None) -> AppSettings:
	"""Load application settings from environment with safe defaults."""
	root = project_root or Path(__file__).resolve().parents[1]

	retrieval = RetrievalSettings(
		top_k=int(os.getenv("WKA_RETRIEVAL_TOP_K", "8")),
		rerank_top_k=int(os.getenv("WKA_RETRIEVAL_RERANK_TOP_K", "20")),
	)
	security = SecuritySettings(
		default_confidentiality=os.getenv("WKA_DEFAULT_CONFIDENTIALITY", "internal"),
		block_external_when_confidential=_to_bool(
			os.getenv("WKA_BLOCK_EXTERNAL_WHEN_CONFIDENTIAL", "true"),
			default=True,
		),
		require_citations=_to_bool(
			os.getenv("WKA_REQUIRE_CITATIONS", "true"),
			default=True,
		),
	)
	runtime = RuntimeSettings(
		log_level=os.getenv("WKA_LOG_LEVEL", "INFO").upper(),
		enable_debug=_to_bool(os.getenv("WKA_ENABLE_DEBUG", "false"), default=False),
	)

	data_dir = root / "data"
	return AppSettings(
		project_root=root,
		data_dir=data_dir,
		raw_data_dir=data_dir / "raw",
		processed_data_dir=data_dir / "processed",
		index_dir=data_dir / "indexes",
		eval_dir=data_dir / "eval",
		retrieval=retrieval,
		security=security,
		runtime=runtime,
	)

