"""Central filesystem locations for locally supplied source documents."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("BENCHMARK_DATA_DIR", PROJECT_ROOT / "data"))
DOCUMENTS_DIR = Path(os.getenv("BENCHMARK_DOCUMENTS_DIR", DATA_DIR / "documents"))
