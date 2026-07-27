# Context

## Project Identity
- Name: Work Knowledge Agent
- Mission: Build a local-first engineering knowledge system that retrieves operational knowledge and produces grounded, cited outputs.
- Repository location: `projects/internal-tools/work-knowledge-agent/` within the BMTech workspace.

## Problem Statement
Engineering teams lose time due to fragmented notes, logs, scripts, and runbooks. Knowledge is hard to retrieve and often uncited, which creates operational and compliance risk.

## Target Outcomes
- Fast retrieval of relevant technical knowledge.
- Citation-first answers for trust and auditability.
- Structured how-to procedures from source documents.
- Actionable task plans from vague engineering goals.
- Safe curation suggestions for improving the knowledge base.

## In Scope (MVP -> V1)
- Ingestion of markdown, text, pdf, log, code, and README sources.
- Hybrid retrieval (semantic + keyword + metadata).
- Cited Q&A.
- How-to generation.
- Planning/checklist generation.
- Curation suggestions with human review.

## Out of Scope (Current)
- Autonomous shell execution.
- Unbounded multi-agent self-modification.
- Browser automation.
- Fine-tuning and custom model training.

## Constraints and Policies
- Reliability over autonomy.
- Local-first and enterprise-safe defaults.
- No final response without citations.
- Mark unsupported steps explicitly.
- Human approval required for write-back changes.
- Use synthetic/redacted artifacts for demos.

## Shared Vocabulary
- Chunk: smallest retrievable text segment with metadata.
- Citation: source reference attached to generated output claims.
- Unsupported step: generated action not grounded in retrieved sources.
- Curation proposal: suggested knowledge update requiring human review.

## Metadata Baseline (Required)
Each chunk should carry:
- source_file
- section_heading
- project
- machine
- component
- mode
- doc_type
- date
- owner
- tags
- confidentiality_level
- extracted_commands
- extracted_errors

## Success Signals
- Retrieval hit rate improves over baseline.
- Citation precision stays high.
- Hallucination and unsupported-step rates trend down.
- How-to and planning outputs are rated actionable.

## Current Baseline State
- Implementation strategy is defined in root plan documents.
- Section 4 target filesystem structure is scaffolded.
- Phase 0 baseline artifacts are complete (settings, logging, guardrails policy, redaction utility).
- Phase 1 upgraded ingestion implementation is in place:
	- manifest-backed incremental identity,
	- preprocessing normalization and content hashing,
	- quarantine artifacts,
	- confidence/provenance metadata,
	- stage timing instrumentation.
- Phase 1 targeted unit tests are implemented and passing.
- Phase 2 retrieval/citation implementation is in place with quality hardening:
	- BM25-lite lexical scoring,
	- citation grounding + command evidence guardrail checks,
	- support thresholds including entity-anchor validation,
	- query-time telemetry and eval harness reporting.
- Gate 2 is signed off as approved-with-conditions based on current validation packet.
- The implementation plan now defines an explicit LLM boundary starting in Phase 3, with Phase 2 remaining LLM-free by default.
- Phase 3 scaffolding has started with the shared LLM client seam and LLM-boundary guardrail now implemented as validated contracts.
- The initial API-backed provider path is now implemented against Watsonx, with a live generation check script that reaches credential loading.
- The Watsonx live path is now confirmed working using sibling-project configuration, and the initial provider-path eval report has been generated.
- The Watsonx runtime path now uses the chat endpoint, and the current repository default model has been reset to `ibm/granite-3-8b-instruct` per user direction.
- Phase 3 gate-style How-To evals now require a frozen golden dataset hash check and explicitly report whether the golden answer key has been human-reviewed.
- Phase 4 implementation now includes planner agent/workflow/CLI, strict planner eval harness, and golden/exploratory planner dataset governance with hash/review gating.
- Planner generation was decoupled from eval-targeted task-intent insertion so eval remains an independent check.
- Phase 4 golden eval now includes adversarial ambiguity/insufficient-evidence cases with explicit support/unknown/open-questions expectations.
- Phase 4 evaluator now scores support/citation success over support-expected runs, preventing false gate failures when unsupported output is intentionally expected.
- Phase 4 task-match scoring now uses coverage-aware pass logic (>=2/3 expected tasks matched) plus concept-aware token normalization to reduce brittle lexical false negatives.
- Gate 4 is now signed off (`approved`) after strict reviewed-golden multi-trial validation and browser-path adversarial/answerable behavior checks.
- Phase 5 baseline now includes curation evaluation metrics and quarantine backlog reporting (`run_curation_eval.py`, `review_quarantine.py`).
- Curator missing-knowledge detection now uses entity-anchor checks for out-of-corpus identifiers to reduce false negatives.
- Phase 5 now includes curator triage outputs (`accepted`, `deferred`, `rejected`) with persisted audit artifacts and enforced human-approval checks for accepted write-back paths.
- Phase 5 now includes a browser-native curator review console (`curation_web.py`) with interactive triage and approval enforcement.
- Phase 5 now includes calibrated duplicate/outdated confidence scoring and triage productivity metrics (approval ratio, decision latency p50/p95).
- Phase 5 now includes explicit corpus quality controls (exact-hash dedupe baseline and near-duplicate candidate reporting).
- Phase 5 now includes rollback controls for reversing accepted triage decisions with append-only audit history continuity.
- Gate 5 has been approved by reviewer and Phase 6 execution has started.
- Phase 6 now includes consolidated readiness artifacts in both JSON and markdown packet format.
- Phase 6 now includes unified interface surfaces: single-command CLI and optional local API endpoints for readiness operations.
- Phase 6 now includes a unified browser portal (`scripts/portal_web.py`) with route split for Ask/How-To/Planner/Triage/Readiness, explicit role-gated admin routes, and trust-state rendering from guardrail signals.
- How-To quality metrics are now populated in the latest readiness report after explicit Watsonx project/url configuration.
- Latest evaluator-aligned packet now explicitly reports `Gate 6 ready: no` with carried open conditions and provenance labels.
- Interface parity evidence is now included and passing in the latest packet (`status=ok`).
- Gate 2 carried conditions are now closed with expanded eval coverage and grounding-threshold regression tests.
- Gate 6 sign-off is now recorded as approved.
- Gate 3 golden-review governance is now closed (`review_status=reviewed`, `gate_eligible=true` in latest How-To report).
- Gate 3 now has decision-grade live evidence via Anthropic provider path (`claude-sonnet-5`), so Watsonx quota is no longer a blocking dependency for gate verification.
- Gate 3 reviewed-golden revalidation now passes all tracked quality metrics (`supported/citation/sections/expected commands/expected sources = 100.0`) with latency within target (`latency_p95_ms=9208.126` < 12s target).
- Gate 3 sign-off is now approved and Phase 3 is complete.
- Immediate focus: validate unified portal UX against evaluator/governance expectations and run targeted smoke checks for each route.

## Last Updated
2026-07-27
