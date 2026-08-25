"""PDF loader using text-layer extraction.

Image-only or non-extractable PDFs should be quarantined by pipeline logic.
"""

from __future__ import annotations

from pathlib import Path

from work_knowledge_agent.ingestion.models import LoadedDocument

try:
	from pypdf import PdfReader
except Exception:  # pragma: no cover
	PdfReader = None


def load(path: Path) -> LoadedDocument:
	if PdfReader is None:
		raise RuntimeError("pypdf is not installed; cannot parse PDF files")

	reader = PdfReader(str(path))
	parts = []
	for page in reader.pages:
		parts.append(page.extract_text() or "")

	text = "\n\n".join(parts).strip()
	warnings = []
	if len(text) < 25:
		warnings.append("pdf_low_text_extraction")

	return LoadedDocument(
		source_path=path,
		text=text,
		size_bytes=path.stat().st_size,
		media_type="application/pdf",
		structural_hints=["pdf"],
		warnings=warnings,
	)

