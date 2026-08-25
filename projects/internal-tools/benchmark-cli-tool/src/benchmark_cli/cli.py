"""Ask a question about one supplied company document.

Usage:
    python main.py --doc document.txt --question "What does this document say?"
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .config import get_model_config
from .models import QAResponse
from .paths import DOCUMENTS_DIR
from .providers.openai import call_llm_structured
from .router import classify_query

SYSTEM_PROMPT = (
    "You are a helpful Q&A assistant. Answer the user's question using ONLY "
    "the provided document. If the answer cannot be found in the document, "
    "explicitly state that."
)
def document_text(document_name: str) -> str:
    """Load a document by filename from the project's ``documents`` directory."""
    from pathlib import Path

    requested_path = Path(document_name)
    if requested_path.name != document_name:
        raise ValueError("--doc must be a filename located in the documents directory.")

    candidate = DOCUMENTS_DIR / requested_path
    if not candidate.is_file():
        available = ", ".join(sorted(path.name for path in DOCUMENTS_DIR.glob("*.txt")))
        suffix = f" Available documents: {available}." if available else ""
        raise FileNotFoundError(f"Document {document_name!r} was not found.{suffix}")
    try:
        return candidate.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Could not read document {document_name!r}: {exc}") from exc


def answer_question(document: str, question: str, tier: str) -> QAResponse:
    """Request a validated document-grounded response from the selected tier."""
    return call_llm_structured(
        tier=tier,
        system_prompt=SYSTEM_PROMPT,
        prompt=f"Document:\n{document}\n\nQuestion:\n{question}",
        response_schema=QAResponse,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse named or positional document and question arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", nargs="?", help="Filename from the documents directory.")
    parser.add_argument("question", nargs="?", help="Question about the document.")
    parser.add_argument("--doc", dest="document_option", help="Filename from the documents directory.")
    parser.add_argument("--question", dest="question_option", help="Question about the document.")
    args = parser.parse_args(argv)

    document = args.document_option if args.document_option is not None else args.document
    question = args.question_option if args.question_option is not None else args.question
    if not document or not question:
        parser.error("provide both a document and question, using named or positional arguments")
    args.document = document
    args.question = question
    return args


def main(argv: Sequence[str] | None = None) -> None:
    """Run the single-document Q&A command."""
    args = parse_args(argv)
    tier = classify_query(args.question)
    print(f"Selected tier: {tier} ({get_model_config(tier).model})", file=sys.stderr)
    response = answer_question(document_text(args.document), args.question, tier)
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
