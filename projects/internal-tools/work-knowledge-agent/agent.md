# Agent Governance Compatibility Note

This repository uses `AGENTS.md` as the primary coding-agent policy file.

To avoid ambiguity and ensure future implementations follow the same control model:
- Treat `AGENTS.md` as authoritative.
- Enforce mandatory human-in-the-loop quality and performance sign-off at every phase gate.
- Require sign-off evidence to be recorded in `project_memory/04_EXECUTION.md` before phase transitions.
- Keep `docs/performance.md` updated as the active gate scorecard reference.
- Keep `docs/concepts_methods.md` updated as the canonical registry of implemented techniques and methods.
- Enforce failure-seeking evaluation discipline: do not tune evals for pass messages; use stricter, diagnostic evals to surface holes and log those holes explicitly.

If this file and `AGENTS.md` ever conflict, `AGENTS.md` is the source of truth.
