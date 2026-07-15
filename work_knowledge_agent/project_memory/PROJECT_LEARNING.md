# Project Learning

Purpose: teach what has been implemented in a way a student can learn from and reuse.

How to use this file:
- Read this after `04_EXECUTION.md` to understand not only what changed, but why it matters.
- Update this file at each phase milestone using teacher-style explanations:
  - concept,
  - what was implemented,
  - why it matters,
  - common mistakes,
  - what to learn next.

## Learning Log

### Phase 0 - Foundation and Control (Completed)
Concept:
A reliable agentic system starts with control, safety, and repeatability before advanced autonomy.

What was implemented:
- Operational rules and discipline in `AGENTS.md`.
- Persistent project memory in `project_memory/`.
- Runtime settings baseline in `config/settings.py`.
- Logging baseline in `config/logging.yaml`.
- Safety/data policy baseline in `docs/guardrails.md`.
- Redaction helper utilities in `src/work_knowledge_agent/security/redaction.py`.
- Startup artifact checks in `src/work_knowledge_agent/main.py`.

Why it matters:
Without these controls, advanced agents drift, hide risk, and are hard to debug or trust.

Common mistakes:
- Building agent logic before defining guardrails.
- Treating memory as optional documentation instead of execution state.
- Skipping startup checks and discovering missing dependencies late.

What to learn next:
- How phase gates prevent implementation drift.
- How to design observability fields (`request_id`, component, decision reason).

### Phase 1 - Ingestion and Indexing Upgrade (Completed)
Concept:
Scalable retrieval pipelines require identity, provenance, and safe failure lanes in addition to good chunk quality.

What was implemented:
- Manifest-backed incremental ingestion state in `ingestion/manifest.py`.
- Preprocessing normalization and hash/fallback routing in `ingestion/preprocessing.py`.
- Shared loader/pipeline contract via `ingestion/models.py`.
- Heading-aware chunking with fenced code preservation in `ingestion/chunking.py`.
- Metadata confidence/provenance and pass/flag/reject evaluation in `ingestion/metadata_extractor.py`.
- Incremental ingestion orchestration with quarantine artifacts and atomic writes in `ingestion/pipeline.py`.
- PDF text-layer extraction in `ingestion/loaders/pdf_loader.py` with quarantine behavior when extraction is weak.
- CLI scripts for ingestion and index build:
  - `scripts/ingest_docs.py`
  - `scripts/build_indexes.py`
- Stage timing instrumentation in both ingest and index scripts.
- Smoke-tested first full run and second-run no-op behavior over `data/raw` corpus.
- Added unit tests for incremental no-op behavior, deterministic IDs, and quarantine routing.

Why it matters:
Identity and provenance let you trust what changed, what was skipped, and why a document was quarantined. That is essential for reliable enterprise operation and auditable citations.

Common mistakes:
- Rebuilding everything every run (slow and noisy) instead of using manifests.
- Dropping bad docs silently instead of quarantining with reason codes.
- Writing artifacts directly without atomic swap, risking partial corruption on interruption.

What to learn next:
- Targeted test design for incremental/no-op correctness and deterministic IDs.
- Retrieval filtering strategies using confidence/confidentiality/provenance metadata.

### Phase 2 - Retrieval and Cited Q&A (Completed: Gate 2 approved-with-conditions)
Concept:
Retrieval quality and citation discipline define whether an assistant feels trustworthy or risky in production.

What was implemented:
- Query rewrite + keyword/vector scoring primitives in `retrieval/` modules.
- Metadata-aware hybrid retrieval and reranking in `retrieval/hybrid_retriever.py`.
- BM25-lite lexical index/scoring upgrade with backward compatibility for legacy index payloads.
- Citation-first QA answer assembly in `agents/qa_agent.py`.
- Q&A workflow orchestration with confidentiality/citation/unsupported guardrails, support thresholds, entity-anchor checks, and per-stage telemetry in `workflows/qa_workflow.py`.
- Runnable Q&A CLI in `scripts/ask.py`.
- Evaluation harness and starter golden-question datasets in `scripts/run_eval.py` and `data/eval/`.
- Unit tests for supported/unsupported QA paths and citation integrity checks in `tests/unit/test_phase2_qa_workflow.py` and `tests/unit/test_citation_guardrail.py`.

Why it matters:
This turns ingestion artifacts into user-facing value while preserving explicit evidence boundaries. The added eval harness and refusal checks make quality measurable and auditable for phase-gate decisions.

Common mistakes:
- Returning fluent answers without citations for each claim.
- Ignoring confidentiality filters when combining retrieval sources.
- Treating retrieval scores as final truth without support/entity checks.

What to learn next:
- Expand eval sets with harder ambiguous and no-evidence prompts.
- Tune reranking/query rewrite settings against domain-specific query sets and error taxonomies.
- Define the LLM boundary, prompt provenance, and deterministic-post-generation guardrails before starting How-To generation.
- Connect the abstract client seam to one real provider path first (Watsonx here), then validate with a live generation check before building higher-level workflows.

### Phase 3 - How-To Agent and LLM Boundary Hardening (Ready for sign-off: reviewed-golden quality pass achieved)
Concept:
Generative workflows should be allowed only inside explicit boundaries, then forced back through deterministic guardrails before final output.

What was implemented:
- Shared model seam in `models/llm_client.py` with Watsonx chat-path support, retry/backoff, and generation provenance metadata.
- LLM boundary enforcement in `guardrails/llm_boundary_guardrail.py` so provider mode and confidentiality controls are checked before any model call.
- First full How-To workflow in `agents/howto_agent.py`, `workflows/howto_workflow.py`, and `scripts/generate_howto.py`.
- Separate browser test surface in `scripts/howto_web.py` so Phase 2 and Phase 3 manual testing stay cleanly separated.
- How-To eval governance hardening:
  - golden vs exploratory datasets,
  - frozen golden hash manifest,
  - review-status and gate-eligibility checks,
  - multi-trial reporting with per-trial failures retained.

Why it matters:
This prevents hidden quality inflation, preserves auditability, and makes Phase 3 readiness measurable instead of subjective.

Common mistakes:
- Treating model output quality as enough without deterministic citation/support checks.
- Tuning expected outputs directly in a gate dataset and then reporting those scores as unbiased.
- Running single-trial evaluations and assuming the result is stable under provider variance or rate limits.

What to learn next:
- Gate-packet preparation with quality and performance evidence that supports explicit human sign-off.
- Better command-level matching metrics that are robust to phrasing variance but still strict on safety-critical steps.
- Evidence-selection tuning techniques that prioritize command-anchor chunks (`journalctl`, `find`, `du`, `df`) for operational runbook prompts.

### Phase 4 - Planner Baseline and Evaluation (In Progress)
Concept:
Planning quality requires both structure correctness and intent correctness; section compliance alone is not enough.

What was implemented:
- Planner generation path in `agents/planner_agent.py`, `workflows/planning_workflow.py`, and `scripts/generate_plan.py`.
- Planner evaluation harness in `evaluation/planning_eval.py` and `scripts/run_plan_eval.py` with metrics for support, citations, sections, expected tasks, expected sources, and latency.
- First live baseline report generated at `data/eval/plan_report_latest.json`.
- Planner golden/exploratory split with hash/review integrity gating and reviewed-manifest gate checks.
- Adversarial planner eval cases for ambiguity/insufficient evidence with explicit support/unknown/open-question expectations.
- Decoupled planner generation from eval-keyword shaping so evaluation remains an independent quality gate.

Why it matters:
The project now has objective evidence for Phase 4 behavior and a clear tuning target where intent extraction is weaker (`expected_task_match_rate_pct`).

Common mistakes:
- Declaring planner quality “good” from formatting and citation metrics while missing task-intent mismatches.
- Using strict string matching only, which can hide true intent overlap and create false negatives.

What to learn next:
- Improve planner behavior on adversarial golden cases without weakening thresholds.
- Add ordering/dependency correctness checks so planning quality goes beyond task-set overlap.
- Build Gate 4 sign-off packet discipline: pair quality evidence with latency evidence and explicit reviewer decision logging.

### Phase 5 - Curator Baseline (Started)
Concept:
Curation should begin with deterministic, explainable proposal logic before adding model-assisted reasoning.

What was implemented:
- Baseline curator proposal engine for `missing_knowledge`, `duplicate_content`, and `outdated_content` suggestions.
- Phase 5 curation workflow orchestration with retrieval, confidentiality filtering, proposal aggregation, and timing telemetry.
- Curation CLI (`generate_curation.py`) and unit coverage (`test_phase5_curation_workflow.py`).
- Phase 5 curation evaluation harness (`run_curation_eval.py`) with case set + metrics for expected proposal-type match and latency.
- Quarantine backlog reporter (`review_quarantine.py`) with review-cadence recommendation and retryable-count visibility.
- Entity-anchor-aware missing-knowledge detection to improve out-of-corpus proposal precision.
- Curator triage workflow (`curation_triage_workflow.py`) and CLI (`triage_curation.py`) for disposition tracking (`accepted`/`deferred`/`rejected`) with persisted audit output.
- Human-approval guardrail contracts in `human_approval.py` that block accepted write-back paths unless reviewer approval is explicit.
- Browser-native curator review console (`curation_web.py`) that visualizes proposals/evidence and executes triage decisions through the same approval-enforced workflow.
- Calibrated duplicate/outdated confidence scoring so proposal confidence reflects observed similarity/age strength instead of fixed constants.
- Triage productivity telemetry (`approval_ratio_pct`, decision latency p50/p95) for reviewer-operability evidence.
- Corpus quality control report (`report_corpus_quality.py`) with exact-hash dedupe baseline and near-duplicate candidate strategy.
- Rollback controls (`curation_rollback_workflow.py`, `rollback_curation.py`) to reverse incorrect accepted decisions with append-only audit events.

Why it matters:
The system now produces actionable knowledge-maintenance suggestions instead of only generation outputs, creating a practical bridge from RAG usage to knowledge-base quality improvement.

Common mistakes:
- Treating early heuristic confidence as final truth instead of triage guidance.
- Shipping curation proposals without evidence-backed rationale and reviewer action suggestions.

What to learn next:
- Improve confidence calibration and duplicate/outdated detection precision.
- Add reviewer triage UX and human-approval flow for proposal disposition.
- Add browser-native curator review screen that displays proposal evidence and recorded disposition history.
- Add triage productivity telemetry (time-to-decision and approval ratio) to support Gate 5 reviewer-operability evidence.
- Package Gate 5 review evidence and obtain explicit human sign-off.
- Add spot-audit disagreement checks so approval ratio is paired with an independent review-quality signal.
- Define Gate 5 score thresholds and reviewer packet format using curation-eval and quarantine metrics.

### Phase 6 - Evaluation and Interface Readiness (Started)
Concept:
A system is release-ready only when quality, performance, and operational observability are reviewed together in one repeatable gate packet.

What was implemented:
- Added `scripts/run_phase6_readiness.py` to aggregate QA/How-To/Planner/Curation/LLM report metrics.
- Added optional live observability execution in the same script to run ingestion and index build commands and capture parsed stage timings.
- Added rebuild-vs-incremental recommendation logic based on warning thresholds (`full_rebuild_warning_ms`, `full_rebuild_warning_chunks`).
- Generated first consolidated readiness artifact at `data/eval/phase6_readiness_latest.json`.
- Extended readiness output to generate `data/eval/phase6_readiness_packet.md` as a reviewer-ready markdown gate packet.
- Added spot-audit disagreement metric from curation history (`rollback_events` over accepted decision events).

Why it matters:
This reduces manual reviewer assembly work, keeps gate evidence consistent across runs, and makes scaling decisions explicit instead of ad hoc.

Common mistakes:
- Reviewing quality metrics without ingest/index timing evidence.
- Making index strategy decisions from intuition instead of thresholded measurements.

What to learn next:
- Convert JSON readiness output into a markdown reviewer packet with explicit pass/fail gating language.
- Stabilize How-To generation quality runs under provider rate limits so cross-phase readiness is fully representative.

Latest status note:
- Markdown packet generation is complete and How-To metrics are now populated after explicit Watsonx project/url configuration.
- Unified interface layer is implemented (`interface_cli.py` and `interface_api.py`), so operators can run eval/readiness flows through stable CLI/API surfaces.
- Unified browser portal is implemented in `scripts/portal_web.py`, consolidating Ask/How-To/Planner/Triage/Readiness routes with explicit role gates and trust-state semantics.
- Ask definition intent handling is improved: definition-style prompts now elevate canonical definition evidence and present a direct-answer sentence before snippet evidence, reducing noisy first answers on tool-definition questions.
- Gate 3 golden manifest governance is closed, latest 5-trial reviewed-golden quality metrics pass (`expected_command_match_rate_pct=100.0` with all other quality metrics at `100.0`), and reviewer approval is now recorded (Phase 3 complete).

## Teacher-Style Update Template (Use at each phase)
### Phase X - <name> (<status>)
Concept:
<one principle a student should remember>

What was implemented:
- <concrete change 1>
- <concrete change 2>

Why it matters:
<impact on reliability, safety, or quality>

Common mistakes:
- <mistake 1>
- <mistake 2>

What to learn next:
- <next skill 1>
- <next skill 2>

## Last Updated
2026-07-05
