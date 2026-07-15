# Planning

## Planning Horizon
- Now: execute recurring cross-phase trust-audit cadence and keep Phase 4/5/6 regression checks active.
- Next: expand curator disagreement analysis and interface hardening for operational rollout.
- Later: Curator reasoning controls, broader routing/orchestration, and interface expansion.

## Phase Plan

### Phase 0 - Bootstrap (1-2 days)
Deliverables:
- Project scaffolding and package layout.
- Base config and logging.
- Data policy and redaction utilities.

Exit Criteria:
- Project runs through main entrypoint.

### Phase 1 - Ingestion and Indexing (Week 1)
Deliverables:
- Loaders and ingestion pipeline.
- Chunking and metadata extraction.
- Vector and keyword index builders.

Exit Criteria:
- Ingestion and index build scripts complete successfully.

### Phase 2 - Retrieval and Cited Q&A (Week 2)
Deliverables:
- Hybrid retriever and reranking.
- Citation-first Q&A workflow.

Exit Criteria:
- Answers consistently include usable citations.

### Phase 3 - How-To Agent (Week 3)
Deliverables:
- Procedure generation workflow with fixed output format.

Exit Criteria:
- Repeatable grounded procedures from same input context.

### Phase 4 - Planner Agent (Week 4)
Deliverables:
- Goal-to-checklist decomposition.
- Missing-context question generation.

Exit Criteria:
- Actionable plans with clear dependencies and open questions.

### Phase 5 - Curator and Guardrails (Week 5)
Deliverables:
- Curation proposals for outdated/duplicate/missing knowledge.
- Citation and unsupported-step guardrails in final path.

Exit Criteria:
- No uncited final output in normal execution path.

### Phase 6 - Evaluation and Interfaces (Week 6)
Deliverables:
- Evaluation harness and score reports.
- CLI complete, optional API.

Exit Criteria:
- Baseline quality metrics tracked over fixed evaluation set.

## Current Priority Queue
1. Run route-level smoke tests for unified portal (`/ask`, `/howto`, `/plan`, `/triage`, `/readiness`) with user/admin role checks and trust-state verification.
2. Define recurring trust-audit cadence for cross-phase evidence revalidation.
3. Keep Phase 4/5/6 regression checks in the active validation suite after Gate 6 sign-off.
4. Expand curation spot-audit disagreement analysis beyond rollback ratio (for example sampled second-review decisions).
5. Evaluate whether interface API should include authenticated mode before broader deployment.

## Decision Gates
- Gate A: Metadata quality is adequate before retrieval tuning.
- Gate B: Citation coverage and refusal accuracy are acceptable before expanding agents.
- Gate C: LLM-boundary architecture and security controls are defined before generative workflows begin.
- Gate D: Guardrails pass baseline before interface exposure.

## Risks to Track
- Weak metadata lowers retrieval quality.
- Citation formatting drift may reduce trust.
- Over-automation before guardrails can introduce unsafe outputs.
- Full corpus rebuild time may become a bottleneck without incremental index strategy.
- Quarantine backlog may grow if preprocessing/loader quality is weak.

## Last Updated
2026-07-05
