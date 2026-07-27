"""Tool: interface_api

Tag: reusable-asset

What this tool does:
- Runs the optional local API server from `work_knowledge_agent.interfaces.api`.
- Serves health/readiness endpoints for Phase 6 interface validation.
"""

from __future__ import annotations

from work_knowledge_agent.interfaces.api import main


if __name__ == "__main__":
	main()
