## 1. Carried-forward open findings

Gate-by-gate review (0 through 6): no finding in the gate sign-off records is explicitly labeled `High` or `Critical` severity. The only explicit gate conditions tied to an `approved-with-conditions` decision are the two Gate 2 conditions below.

1. Gate 2 finding: Eval set too small for robust refusal/citation confidence (condition: expand evaluation prompts with harder unanswerable/ambiguous cases).
- Current status: resolved-with-evidence.
- Resolution evidence:
  - Closure recorded in `project_memory/04_EXECUTION.md` under "Closed remaining Gate 2 carry-forward conditions".
  - Expanded eval set documented as 12 prompts and mapped expected sources (`data/eval/eval_questions.json`, `data/eval/expected_sources.json`).
  - Verification commands recorded in `project_memory/04_EXECUTION.md`: `tests.unit.test_citation_guardrail` + `tests.unit.test_phase2_qa_workflow` pass and `scripts/run_eval.py` with `total_questions=12`, `refusal_accuracy_pct=100.0`.

2. Gate 2 finding: Grounding-threshold regression coverage was missing (condition: add explicit grounding-threshold regression test coverage).
- Current status: resolved-with-evidence.
- Resolution evidence:
  - Closure recorded in `project_memory/04_EXECUTION.md` under "Closed remaining Gate 2 carry-forward conditions".
  - Added tests documented in `project_memory/04_EXECUTION.md`: grounding-threshold regression paths in `tests/unit/test_citation_guardrail.py`.
  - Follow-up verification run recorded as passing in `project_memory/04_EXECUTION.md` (`Ran 6 tests`, `OK`).

Per-gate carry-forward status snapshot:
- Gate 0: no High/Critical findings and no approved-with-conditions conditions found in gate records.
- Gate 1: no High/Critical findings and no approved-with-conditions conditions found in gate records.
- Gate 2: two approved-with-conditions findings (both resolved-with-evidence above).
- Gate 3: rejected checkpoint condition existed historically (command-fidelity), then revalidation approved with no conditions; no High/Critical severity label found in gate records.
- Gate 4: no High/Critical findings and no approved-with-conditions conditions found in gate records.
- Gate 5: no High/Critical findings and no approved-with-conditions conditions found in gate records.
- Gate 6: no High/Critical findings and no approved-with-conditions conditions found in gate records.

## 2. Query routing (orchestrator)

Automatic query routing does not exist yet.
- Confirmed evidence: `src/work_knowledge_agent/agents/orchestrator.py` is empty.
- Confirmed evidence: `scripts/ask.py`, `scripts/generate_howto.py`, and `scripts/generate_plan.py` each require explicit user tool selection via positional arguments (`question`, `task`, `goal`) and directly call one workflow each.

Building this for real requires:
- Real router implementation that routes through the shared LLM client seam (`src/work_knowledge_agent/models/llm_client.py`), not standalone ad hoc model calls.
- An explicit low-confidence fallback rule (default to Q&A, not forced classification).
- A product decision on multi-tool queries: in-scope for v1 or explicitly deferred.
- A dedicated golden eval set of query-to-correct-tool pairs that is independently authored, hash-integrity checked, and multi-trial tested before any gate pass.

## 3. Client-readiness gaps not covered by any existing phase gate

1. Confidentiality/corpus-scope resolution: does not exist.
- Evidence: corpus sources are currently rooted in `data/raw/work_IBM/` and governance docs define confidentiality controls (`docs/guardrails.md`), but no explicit signed decision is recorded on whether handoff corpus is IBM-internal vs client-appropriate corpus.

2. API-vs-CLI guardrail parity: partially exists.
- Evidence: readiness parity checks exist for health/readiness payload shape in Phase 6 artifacts (`data/eval/phase6_readiness_packet.md`, `data/eval/phase6_readiness_latest.json`), but those artifacts do not show a confidentiality-restricted or citation-guardrail-triggering query executed through both API and CLI with identical outcomes asserted.

3. Rollback path for curator-accepted decisions: exists.
- Evidence: rollback workflow/tool and tests are present (`src/work_knowledge_agent/workflows/curation_rollback_workflow.py`, `scripts/rollback_curation.py`, `tests/unit/test_phase5_curation_rollback.py`).
- Exercised evidence: execution log records a seeded accepted decision followed by rollback and verification (`rollback_summary.rolled_back=true`) in `project_memory/04_EXECUTION.md`; history artifact `data/eval/curation_triage_history.jsonl` includes both triage and rollback events.

4. Spot-audit mechanism for curator approvals: partially exists.
- Evidence: `data/eval/phase6_readiness_latest.json` reports `accepted_decision_events=1`, `rollback_events=1`, `metric_non_vacuous=true`, and `spot_audit_disagreement_rate_pct=100.0`.
- Gap: only a single counted event path is evidenced; no broader recurring audit program evidence is recorded.

5. Operational runbook (ingest/index/eval/rollback for non-author operator): partially exists.
- Evidence: command coverage exists across `docs/performance.md` and `README.md`.
- Gap: no single operator-focused runbook document was found that stitches ingest, index, eval, rollback, and failure handling into one handoff-ready procedure.

6. Known-limitations document for client audience: does not exist.
- Evidence: no dedicated client-facing limitations file found in `docs/` or `project_memory/`.

7. Client-shaped adversarial test coverage: does not exist.
- Evidence: current evidence references project-owned golden/exploratory sets and gate packets; no artifact in repo records a client-provided or client-shaped adversarial evaluation suite.

8. Web interface status against design brief: built but unverified against brief.
- Evidence for built status: web interfaces and browser validation are recorded in `project_memory/04_EXECUTION.md` (`scripts/ask_web.py`, `scripts/howto_web.py`, `scripts/planner_web.py`, `scripts/curation_web.py`), and active local UI pages are in use.
- Verification gap: `WEB_INTERFACE_DESIGN_PROMPT.md` was not found in the repository at time of writing, so non-negotiable trust-signal compliance against that specific brief cannot be verified from repo evidence.

## 4. Prioritized action list

1. Resolve confidentiality/corpus-scope governance decision.
- Why it matters: without explicit data-classification sign-off on corpus scope, all downstream handoff work can be invalid from a policy standpoint.
- Effort estimate: medium.
- Done check: signed governance record added to `project_memory/04_EXECUTION.md` (or equivalent decision log) naming approved handoff corpus, classification authority, date, and allowed exposure boundaries.

2. Implement real query router + fallback policy.
- Why it matters: current UX requires manual tool selection, which is not client-robust and prevents intent-safe default behavior.
- Effort estimate: larger.
- Done check: non-empty orchestrator implementation routes through shared client seam, low-confidence defaults to Q&A, multi-tool policy documented, and dedicated router golden eval reports hash match + reviewed status + passing multi-trial metrics.

3. Add true API-vs-CLI guardrail parity tests for blocked/guardrailed cases.
- Why it matters: parity at health/readiness level does not prove parity of safety outcomes.
- Effort estimate: medium.
- Done check: at least one confidentiality-blocked query and one citation-guardrail-triggering query are executed through both surfaces with matching support/deny reason/citation status, and test evidence is captured in versioned test artifacts.

4. Create a single operator runbook for handoff operations.
- Why it matters: fragmented commands across docs are not sufficient for repeatable client operation by non-authors.
- Effort estimate: medium.
- Done check: one runbook document exists with step-by-step ingest, index, eval, rollback, failure handling, and expected artifact checks; dry-run executed by a second operator and logged.

5. Publish a client-facing known-limitations document.
- Why it matters: explicit boundaries reduce overtrust and contract risk.
- Effort estimate: quick win.
- Done check: dedicated limitations doc exists, linked from `README.md`, and referenced in handoff packet.

6. Add client-shaped adversarial evaluation set.
- Why it matters: internal golden sets may miss client-specific failure modes.
- Effort estimate: larger.
- Done check: independent client-shaped eval set added with manifest hash/review metadata and multi-trial run results included in gate-style packet.

7. Strengthen curator spot-audit coverage beyond one evidenced event path.
- Why it matters: single-event disagreement telemetry can be statistically misleading.
- Effort estimate: medium.
- Done check: multiple audited accepted decisions are logged, disagreement metric remains non-vacuous over a defined sample threshold, and trend is reviewed in readiness packet.

8. Verify web interfaces against trust-signal brief requirements.
- Why it matters: UI trust signals (unsupported-state visibility, blocked defaults, confidentiality tier display, golden-vs-exploratory labeling) are core to safe client use.
- Effort estimate: medium.
- Done check: `WEB_INTERFACE_DESIGN_PROMPT.md` is present (or officially superseded), each non-negotiable requirement is mapped to UI behavior with screenshot/test evidence, and gaps are either fixed or explicitly accepted by reviewer.

## 5. Explicit non-recommendation

This document intentionally does not provide a "ready for client handoff: yes/no" verdict; that decision must be made by a human reviewer using the action list above.
