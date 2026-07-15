# Reusable Assets Registry

Purpose: track components that can be extracted and reused in future projects.

How to update:
- Add a row when a reusable utility, script, module, template, or workflow appears.
- Update maturity and extraction notes as implementation quality improves.
- Keep entries practical: what it does, when to reuse it, and what to change first.

## Asset Table

| Asset | Type | Location | Current Maturity | Reuse Notes |
|---|---|---|---|---|
| Chunking utility | Module | `src/work_knowledge_agent/ingestion/chunking.py` | upgraded | Heading-aware chunking with fenced-code preservation; tune confidence thresholds by corpus. |
| Metadata schema + validation | Module | `src/work_knowledge_agent/ingestion/metadata_extractor.py` | upgraded | Includes confidence/provenance plus pass/flag/reject evaluation; adapt thresholds and required fields per domain. |
| Ingestion orchestrator | Module | `src/work_knowledge_agent/ingestion/pipeline.py` | upgraded | Reuse manifest-backed incremental flow with quarantine lane and atomic writes. |
| Manifest store | Module | `src/work_knowledge_agent/ingestion/manifest.py` | baseline | Reuse SQLite identity tracking for incremental ingest and deletion detection. |
| Preprocessing helpers | Module | `src/work_knowledge_agent/ingestion/preprocessing.py` | baseline | Reuse normalization + content hashing + fallback loader sniffing for mixed corpora. |
| Shared ingestion models | Module | `src/work_knowledge_agent/ingestion/models.py` | baseline | Reuse typed document/quarantine contracts between loaders and pipeline. |
| Ingestion CLI | Script | `scripts/ingest_docs.py` | upgraded | Reuse as batch/incremental entrypoint with manifest + quarantine outputs and stage timing metrics. |
| Index build CLI | Script | `scripts/build_indexes.py` | upgraded | Reuse for lightweight indexing with stage timing instrumentation; swap TF-IDF-lite with vector DB later. |
| Hybrid retriever baseline | Module | `src/work_knowledge_agent/retrieval/hybrid_retriever.py` | upgraded | Reuse lexical+vector weighted retrieval with metadata-aware reranking and confidence filtering. |
| Retrieval scoring primitives | Modules | `src/work_knowledge_agent/retrieval/{keyword_index.py,vector_index.py,reranker.py,query_rewriter.py}` | upgraded | Reuse token rewrite and index scoring modules (including BM25-lite lexical scoring) across CLI/API paths. |
| Citation-first QA workflow | Modules | `src/work_knowledge_agent/{agents/qa_agent.py,workflows/qa_workflow.py}` | upgraded | Reuse for grounded Q&A orchestration with support thresholds, entity-anchor checks, telemetry, and defense-in-depth confidentiality checks. |
| LLM client seam | Module | `src/work_knowledge_agent/models/llm_client.py` | upgraded | Reuse as the single model access contract for future generative workflows; includes chat-endpoint parsing, retry/backoff handling, and generation provenance metadata. |
| Watsonx credentials loader | Module | `src/work_knowledge_agent/models/watsonx_credentials.py` | baseline | Reuse to load Watsonx project/url/apikey settings consistently across scripts and provider-backed clients. |
| LLM boundary guardrail | Module | `src/work_knowledge_agent/guardrails/llm_boundary_guardrail.py` | baseline | Reuse to enforce provider-mode, confidentiality, and redaction checks before any model call. |
| How-To generation workflow | Modules/Script | `src/work_knowledge_agent/{agents/howto_agent.py,workflows/howto_workflow.py}` + `scripts/generate_howto.py` | baseline | Reuse as the first structured generative workflow that turns retrieved evidence into sectioned procedures with deterministic post-checks. |
| Planning generation workflow | Modules/Script | `src/work_knowledge_agent/{agents/planner_agent.py,workflows/planning_workflow.py}` + `scripts/generate_plan.py` | upgraded | Reuse as the Phase 4 workflow that turns vague goals into structured plans with goal-relevance prompt controls, goal-aware retrieval candidate expansion, and source-alignment reranking while avoiding eval-keyword shaping in output normalization. |
| Planning evaluation harness | Script/Module | `scripts/run_plan_eval.py` + `src/work_knowledge_agent/evaluation/planning_eval.py` | upgraded | Reuse as a strict Phase 4 scorecard with all-source matching, concept-aware token-overlap task checks, support/unknown/open-question expectation metrics, support-expected denominator handling for support/citation gates, coverage metrics, run-error rate, failure catalog, gate-ready signals, and golden integrity/review gating. |
| Phase 4 one-command test runner | Script | `scripts/test_phase4.py` | upgraded | Reuse as a failure-seeking verification entrypoint with stricter default thresholds so gaps are surfaced instead of hidden by permissive pass criteria. |
| Curation generation workflow | Modules/Script | `src/work_knowledge_agent/{agents/curator_agent.py,workflows/curation_workflow.py}` + `scripts/generate_curation.py` | baseline | Reuse as a Phase 5 deterministic curation baseline that produces missing/duplicate/outdated knowledge proposals with evidence-backed rationale and action suggestions. |
| Curation evaluation harness | Script/Module | `scripts/run_curation_eval.py` + `src/work_knowledge_agent/evaluation/curation_eval.py` | baseline | Reuse as a Phase 5 scorecard for expected proposal-type match, non-empty proposal rate, proposal volume, and latency metrics. |
| Quarantine review reporter | Script | `scripts/review_quarantine.py` | baseline | Reuse to summarize quarantine backlog by reason/stage/extension and suggest review cadence with retryable-count visibility. |
| Curation triage workflow | Modules/Script | `src/work_knowledge_agent/{workflows/curation_triage_workflow.py,guardrails/human_approval.py}` + `scripts/triage_curation.py` | baseline | Reuse to apply reviewer dispositions (`accepted`, `deferred`, `rejected`) with explicit human-approval checkpoints before any accepted write-back path. |
| Curation rollback control | Modules/Script | `src/work_knowledge_agent/workflows/curation_rollback_workflow.py` + `scripts/rollback_curation.py` | baseline | Reuse to reverse accepted triage decisions, recompute triage summary metrics, and append rollback events in audit history. |
| Phase 6 readiness aggregator | Script | `scripts/run_phase6_readiness.py` | baseline | Reuse to consolidate eval metrics, run optional ingestion/index observability checks, and emit index-evolution recommendations for gate packets. |
| Unified interface CLI | Module/Script | `src/work_knowledge_agent/interfaces/cli.py` + `scripts/interface_cli.py` | baseline | Reuse as a single command surface for QA/How-To/Planner/Curation/LLM eval runs and Phase 6 readiness generation. |
| Optional readiness API | Module/Script | `src/work_knowledge_agent/interfaces/api.py` + `scripts/interface_api.py` | baseline | Reuse for lightweight local endpoint access to readiness artifacts and triggerable readiness regeneration. |
| Curator Web Console | Script | `scripts/curation_web.py` | baseline | Reuse as a browser-native Phase 5 review surface that generates proposals, captures triage decisions, enforces approval checks, and persists audit artifacts. |
| Corpus quality report | Script/Doc | `scripts/report_corpus_quality.py` + `docs/corpus_quality.md` | baseline | Reuse to measure exact-hash duplicate rate and near-duplicate candidates, then drive source-level dedupe remediation with a documented strategy. |
| Golden eval integrity control | Module/Data Contract | `src/work_knowledge_agent/evaluation/golden_eval_control.py` + `data/eval/*_golden.meta.json` | upgraded | Reuse to enforce frozen-dataset hash verification, review status tracking, and gate-eligibility checks across How-To and Planner gate-style eval workflows. |
| Ask CLI | Script | `scripts/ask.py` | baseline | Reuse as a minimal Phase 2 user interface for cited answers and guardrail status inspection. |
| Ask Web Console | Script | `scripts/ask_web.py` | baseline | Reuse as a lightweight browser-based Q&A tester with prompt box, answer rendering, citations, guardrail status, and latency metrics. |
| How-To Web Console | Script | `scripts/howto_web.py` | baseline | Reuse as a separate browser-based Phase 3 tester for structured procedures, generation metadata, and citation diagnostics without changing the Phase 2 UI. |
| Planner Web Console | Script | `scripts/planner_web.py` | baseline | Reuse as a browser-based Phase 4 tester that runs the planning workflow directly and surfaces planner output, guardrail status, citations, generation metadata, and timing diagnostics. |
| Unified Client/Admin Portal | Script | `scripts/portal_web.py` | baseline | Reuse as a single web shell for Ask/How-To/Planner/Triage/Readiness with role-based route access and explicit trust-state semantics (`verified`, `unsupported`, `blocked`, `restricted`, `unreviewed`). |
| LLM live check | Script | `scripts/check_llm.py` | baseline | Reuse as a real connectivity/provenance check for the approved LLM path; useful before Phase 3 workflow debugging. |
| LLM evaluation harness | Script/Module | `scripts/run_llm_eval.py` + `src/work_knowledge_agent/evaluation/llm_eval.py` | baseline | Reuse as a provider-path scorecard for success rate, expected-output match, token usage, and latency before full workflow integration. |
| How-To evaluation harness | Script/Module | `scripts/run_howto_eval.py` + `src/work_knowledge_agent/evaluation/howto_eval.py` | baseline | Reuse as a Gate 3-style scorecard for supported rate, citation status, required sections, expected commands, source matching, and latency. |
| Evaluation harness | Script | `scripts/run_eval.py` | baseline | Reuse for fixed-question retrieval/citation/refusal evaluation with report artifact outputs for phase gates. |
| Guardrails baseline policy | Doc | `docs/guardrails.md` | baseline | Reuse as starter governance policy for citation/confidentiality controls. |
| LLM strategy policy | Doc | `docs/llm_strategy.md` | baseline | Reuse to define where model synthesis is allowed, how it is governed, and what provenance/security controls are mandatory. |
| Redaction helpers | Module | `src/work_knowledge_agent/security/redaction.py` | baseline | Reuse default masking rules; add org-specific secret and PII patterns. |
| Agent operating rules | Doc | `AGENTS.md` | baseline | Reuse workflow governance in new repos; adjust phase gates and policy priorities. |
| Concepts and methods catalog | Doc | `docs/concepts_methods.md` | baseline | Reuse as a living implementation-method registry to accelerate onboarding and evaluator reviews. |
| Project learning template | Doc | `project_memory/PROJECT_LEARNING.md` | baseline | Reuse for teaching-friendly session handoff and student onboarding. |

## Extraction Candidates
- Promote ingestion and indexing scripts into a shared `automation_toolkit` package after tests are added.
- Promote metadata schema into a versioned contract file once retrieval stack is stable.

## Teacher Notes
- A reusable asset is not just code; it includes assumptions, contracts, and safe defaults.
- If an asset cannot be reused without tribal knowledge, improve docs before extraction.

## Last Updated
2026-07-05
