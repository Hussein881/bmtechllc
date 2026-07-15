# Project Memory System

This folder is the persistent working memory for coding agents.

## Files
- `01_CONTEXT.md`: Why this project exists, scope, constraints, and shared vocabulary.
- `02_PLANNING.md`: Milestones, phase goals, deliverables, and sequencing.
- `03_ARCHITECTURE.md`: System design, component boundaries, contracts, and guardrails.
- `04_EXECUTION.md`: Current sprint state, task board, runbook commands, and session handoff notes.
- `PROJECT_LEARNING.md`: Teacher-style learning log that explains what was implemented, why it matters, and what to learn next.
- `REUSABLE_ASSETS.md`: Registry of reusable scripts, modules, docs, and extraction candidates for future projects.
- `PROJECT_STRUCTURE.md`: Repository map with one-line descriptions for folders, scripts, and key modules.

## How Agents Should Use This
1. Read `01_CONTEXT.md` first.
2. Read `02_PLANNING.md` to pick the next milestone.
3. Read `03_ARCHITECTURE.md` before editing design-sensitive code.
4. Update `04_EXECUTION.md` after every meaningful implementation step.
5. Update `PROJECT_LEARNING.md` at each phase milestone using teacher-style explanations.
6. Update `REUSABLE_ASSETS.md` when a reusable asset is added, promoted, or changed.
7. Update `PROJECT_STRUCTURE.md` when folders, scripts, or module purposes change.

## Update Rules
- Keep entries factual and brief.
- Record decisions as explicit changes (what changed and why).
- Prefer append-only logs in `04_EXECUTION.md` for traceability.
- If scope changes, update `01_CONTEXT.md` and `02_PLANNING.md` together.
- When phase status changes, update all memory files in one synchronization pass to keep context, planning, architecture, and execution consistent.
- When a phase task is completed, add or refresh a matching section in `PROJECT_LEARNING.md` with: concept, implementation, why it matters, common mistakes, and next learning steps.
- When scripts/tools gain reusable value, tag them (`Tag: reusable-asset`) and add or refresh entries in `REUSABLE_ASSETS.md`.
- When repo structure changes or new tools are added, refresh `PROJECT_STRUCTURE.md` with the new path and one-line purpose.

## Last Updated
2026-07-05
