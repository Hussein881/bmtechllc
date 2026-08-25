# Agent Operating Rules

This file defines mandatory execution rules for any coding agent working in this repository.

## 1) Source of Truth and Priority
When rules conflict, use this order:
1. Safety and data policy from docs/guardrails.md.
2. Scope, phases, and gates from IMPLEMENTATION_PLAN.md.
3. Current execution state from project_memory/04_EXECUTION.md.
4. Other project docs and comments.

Do not bypass gate requirements for speed.

## 2) Plan Discipline
- Implement only in-scope tasks for the active phase.
- Do not add out-of-phase features unless explicitly approved.
- If a dependency is not satisfied, stop and close the dependency first.
- If a change affects contracts/schemas/guardrails, update the plan and reopen impacted gates.

## 3) Memory Update Rules (Mandatory)
Update project memory after every meaningful implementation step.

Required updates:
- project_memory/04_EXECUTION.md:
  - move tasks between Todo/In Progress/Done,
  - append dated session-log entries,
  - record commands run and outcomes.
- project_memory/REUSABLE_ASSETS.md:
  - add or refresh reusable components created in the session,
  - record maturity and extraction notes,
  - keep script/tool tags aligned with the registry.
- project_memory/PROJECT_STRUCTURE.md:
  - update when folders, scripts, or module responsibilities change,
  - keep one-line tool/module purposes accurate,
  - keep the structure map aligned with the repository.
- project_memory/PROJECT_LEARNING.md:
  - update at each phase milestone,
  - explain implementation in teacher style,
  - include concept, why it matters, common mistakes, and next learning steps.
- project_memory/01_CONTEXT.md:
  - update baseline state when project status materially changes.
- project_memory/02_PLANNING.md:
  - update priority queue and sequencing when priorities shift.
- project_memory/03_ARCHITECTURE.md:
  - record architecture decisions and contract changes.

## 4) Ask Questions When Uncertain
Ask concise clarifying questions before coding when any of the following are true:
- Requirement is ambiguous or could be interpreted in multiple valid ways.
- Implementation may introduce security, confidentiality, or policy risk.
- Proposed change may break an existing contract or phase gate.
- Missing acceptance criteria prevents objective completion.

If uncertainty is low and reversible, proceed with a safe default and document assumptions.

## 5) Safety and Guardrails
- No final output path without citations.
- Mark unsupported steps explicitly.
- Apply confidentiality and redaction controls by default.
- Require human approval for write-back or publish actions.

## 6) Validation Before Completion
Before marking work done:
1. Run relevant smoke tests and/or targeted checks.
2. Confirm no new diagnostics/errors in changed files.
3. Verify expected behavior with at least one concrete execution path.
4. Record verification evidence in project_memory/04_EXECUTION.md.

## 7) Change Control
Create or update an ADR entry (in project docs) for major changes to:
- metadata schema,
- output contracts,
- guardrail flow,
- retrieval/indexing architecture.

Major changes require explicit approval before implementation.

## 8) Definition of Done Enforcement
A task is complete only when:
- implementation is merged in working code,
- tests/checks pass,
- memory files are updated,
- any required docs are updated,
- applicable phase gate criteria remain satisfied.

## 8.1) Human-In-The-Loop Gate Sign-Off (Mandatory)
- Before moving from one phase to the next, prepare a human review packet with both:
  - quality evidence (test results, sampled outputs, correctness checks),
  - performance evidence (latency/timing metrics and target comparison).
- Present this packet to the human owner and obtain explicit sign-off.
- Record sign-off in `project_memory/04_EXECUTION.md` with:
  - gate id,
  - reviewer,
  - date,
  - quality verdict,
  - performance verdict,
  - final decision (`approved`, `approved-with-conditions`, or `rejected`).
- If sign-off is not approved, do not advance phases.

## 9) Session Handoff Standard
At the end of a session, update project_memory/04_EXECUTION.md with:
- summary of completed work,
- files changed,
- commands run and results,
- blockers/open risks,
- next best task.

## 10) Anti-Drift Rule
When in doubt, optimize for reliability, traceability, and plan compliance over speed.

## 11) Reusability Rule
- Add `Tag: reusable-asset` in script/tool module headers when designed for reuse.
- Reflect every reusable script/tool in `project_memory/REUSABLE_ASSETS.md`.
- Prefer reusable abstractions when they do not violate current phase scope.

## 12) Performance Scorecard Rule
- Keep `docs/performance.md` current with active quality/performance metrics and thresholds.
- Use this scorecard during every gate review and include key numbers in execution logs.

## 13) Concepts and Methods Catalog Rule
- Keep `docs/concepts_methods.md` current as implementation evolves.
- Update this catalog whenever a technique is added, removed, or materially changed in ingestion, retrieval, guardrails, workflows, or evaluation.
- Every new method entry must include:
  - short description,
  - rationale (why it matters),
  - implementation locations,
  - effectiveness signal(s) when available.
- Before phase-gate sign-off, verify the catalog reflects all techniques shipped in that phase.

## 14) Evaluation Integrity Rule
- Do not modify eval cases, expected outputs, or thresholds for the purpose of forcing a passing smoke test.
- Use evaluations to expose holes; prefer stricter diagnostic defaults that increase defect discovery.
- For gate-style evals, require source-coverage checks and review failure catalogs/per-case trial details in addition to headline pass rates.
- If eval assets change, document why the change improves diagnostic validity (not apparent score gain) and record evidence in `project_memory/04_EXECUTION.md`.
