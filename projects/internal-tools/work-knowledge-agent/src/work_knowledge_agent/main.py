"""Main entrypoint for the Work Knowledge Agent package."""

from pathlib import Path


def _required_bootstrap_files(project_root: Path) -> list[Path]:
    return [
        project_root / "config" / "settings.py",
        project_root / "config" / "logging.yaml",
        project_root / "docs" / "guardrails.md",
        project_root / "src" / "work_knowledge_agent" / "security" / "redaction.py",
    ]


def main() -> None:
    """Run bootstrap checks required by Phase 0 Gate 0."""
    project_root = Path(__file__).resolve().parents[2]
    missing = [path for path in _required_bootstrap_files(project_root) if not path.exists()]

    if missing:
        print("Work Knowledge Agent bootstrap check failed.")
        for path in missing:
            print(f"Missing required file: {path}")
        raise SystemExit(1)

    print("Work Knowledge Agent bootstrap is ready.")
    print("Gate 0 artifact checks passed.")


if __name__ == "__main__":
    main()
