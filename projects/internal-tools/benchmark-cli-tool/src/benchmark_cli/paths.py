"""Central filesystem locations for application data and generated artifacts."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("BENCHMARK_DATA_DIR", PROJECT_ROOT / "data"))
DOCUMENTS_DIR = Path(os.getenv("BENCHMARK_DOCUMENTS_DIR", DATA_DIR / "documents"))
ARTIFACTS_DIR = Path(os.getenv("BENCHMARK_ARTIFACTS_DIR", PROJECT_ROOT / "artifacts"))


def artifact_path(*parts: str) -> Path:
    """Return an artifact destination, creating its parent directory on demand."""
    path = ARTIFACTS_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
