"""Tool: interface_cli

Tag: reusable-asset

What this tool does:
- Exposes the unified interface CLI from `work_knowledge_agent.interfaces.cli`.
- Provides one command surface for evaluation harnesses and Phase 6 readiness generation.
"""

from __future__ import annotations

from work_knowledge_agent.interfaces.cli import main


if __name__ == "__main__":
	raise SystemExit(main())
