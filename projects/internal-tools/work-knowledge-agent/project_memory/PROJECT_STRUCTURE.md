# Project Structure Reference

Purpose: provide a quick map of the repository and a one-line description of what each key tool or module is for.

```text
projects/internal-tools/work-knowledge-agent/      # Project folder within the BMTech workspace
|-- AGENTS.md                                      # Repository-wide agent operating rules
|-- agent.md                                       # Compatibility pointer enforcing AGENTS.md governance
|-- IMPLEMENTATION_PLAN.md                         # Phase plan, gates, and execution strategy
|-- pyproject.toml                                 # Python project metadata and packaging config
|-- config/                                        # Runtime settings, prompts, and logging config
|   |-- settings.py                                # Application settings loader and defaults
|   |-- prompts.yaml                               # Prompt/config placeholder for future workflows
|   `-- logging.yaml                               # Structured logging configuration
|-- data/                                          # Knowledge inputs, generated artifacts, and eval assets
|   |-- raw/                                       # Source documents to ingest
|   |   |-- sample_runbook.md                      # Synthetic ingestion fixture document
|   |   `-- work_IBM/                              # Local IBM work knowledge corpus
|   |-- processed/                                 # Generated chunk and metadata artifacts
|   |   |-- chunks.jsonl                           # Chunked text records for retrieval
|   |   |-- metadata.parquet                       # Bootstrap metadata artifact (JSONL content for now)
|   |   |-- quarantine.jsonl                       # Quarantined-document records with reason/stage/detail
|   |   `-- manifest.sqlite                        # Incremental ingestion identity/state tracking DB
|   |-- indexes/                                   # Retrieval indexes built from processed artifacts
|   |   |-- keyword/
|   |   |   `-- index.json                         # Keyword postings index
|   |   `-- vector/
|   |       `-- index.json                         # TF-IDF-lite vector-style index
|   `-- eval/                                      # Evaluation inputs and expected-source references
|       |-- eval_questions.json                    # Placeholder evaluation questions
|       |-- expected_sources.json                  # Placeholder expected citation sources
|       |-- howto_eval_cases.json                  # Canonical How-To eval set (aligned to golden baseline for compatibility)
|       |-- howto_eval_cases_golden.json           # Explicit golden How-To eval set for repeated-trial gate runs
|       |-- howto_eval_cases_exploratory.json      # Mutable How-To tuning prompts for local iteration only
|       |-- howto_eval_cases_golden.meta.json      # Golden How-To integrity manifest (hash + review metadata)
|       |-- plan_eval_cases.json                   # Compatibility planner eval set aligned to the golden baseline (includes adversarial checks)
|       |-- plan_eval_cases_golden.json            # Explicit golden planner eval set for gate-style runs
|       |-- plan_eval_cases_exploratory.json       # Mutable planner tuning prompts for local iteration only
|       |-- plan_eval_cases_golden.meta.json       # Golden planner integrity manifest (hash + review metadata)
|       |-- llm_eval_cases.json                    # Starter prompt set for Watsonx generation performance/quality evaluation
|       |-- howto_report_latest.json               # Latest How-To evaluation output report artifact
|       |-- llm_report_latest.json                 # Latest provider-path evaluation output report artifact
|       |-- plan_report_latest.json                # Latest planner evaluation output report artifact
|       |-- curation_eval_cases.json               # Phase 5 curation evaluation case set for proposal-type matching checks
|       |-- curation_report_latest.json            # Latest Phase 5 curation evaluation output report artifact
|       |-- curation_triage_latest.json            # Latest Phase 5 curator triage/approval output artifact
|       |-- curation_triage_history.jsonl          # Append-only Phase 5 triage/rollback audit history events
|       |-- corpus_quality_report_latest.json      # Latest Phase 5 corpus duplicate-quality control report artifact
|       |-- gate5_review_packet.md                 # Phase 5 human-review evidence packet and sign-off template
|       |-- phase6_readiness_latest.json           # Consolidated Phase 6 readiness report with quality/observability and rebuild recommendation
|       |-- phase6_readiness_packet.md             # Gate 6 markdown reviewer packet generated from consolidated readiness data
|       `-- report_latest.json                     # Latest Phase 2 retrieval/citation/refusal evaluation output report artifact
|-- docs/                                          # Design and guardrail documentation
|   |-- architecture.md                            # High-level system architecture notes
|   |-- retrieval_design.md                        # Retrieval design notes and future decisions
|   |-- guardrails.md                              # Citation, confidentiality, and approval policy
|   |-- concepts_methods.md                        # Canonical catalog of implemented techniques and methods
|   |-- llm_strategy.md                            # LLM boundary, provider, provenance, and security strategy for Phase 3+
|   |-- performance.md                             # Phase-gate quality/performance scorecard and HITL sign-off template
|   |-- corpus_quality.md                          # Phase 5 duplicate-control policy and remediation strategy
|   `-- eval_strategy.md                           # Evaluation strategy placeholder
|-- project_memory/                                # Long-term agent memory and project operating context
|   |-- 01_CONTEXT.md                              # Scope, constraints, vocabulary, and baseline state
|   |-- 02_PLANNING.md                             # Priority queue, sequencing, and phase planning
|   |-- 03_ARCHITECTURE.md                         # Design boundaries, contracts, and decisions
|   |-- 04_EXECUTION.md                            # Live execution board, session log, and verification trail
|   |-- NEXT_STEPS.md                              # Evidence-grounded pre-handoff gap register and prioritized action list
|   |-- agent.md                                   # Project-memory local agent rule addendum (strict evaluation discipline)
|   |-- PROJECT_LEARNING.md                        # Teacher-style learning notes by phase
|   |-- REUSABLE_ASSETS.md                         # Registry of reusable scripts, modules, and docs
|   `-- PROJECT_STRUCTURE.md                       # This folder-tree reference with one-line descriptions
|-- scripts/                                       # CLI entrypoints for ingestion, indexing, and future workflows
|   |-- ingest_docs.py                             # Ingest raw documents into chunk and metadata artifacts
|   |-- build_indexes.py                           # Build keyword and vector-like retrieval indexes
|   |-- ask.py                                     # Citation-first Q&A CLI using hybrid retrieval + guardrails
|   |-- ask_web.py                                 # Local browser Q&A test console with prompt box and rendered diagnostics
|   |-- check_llm.py                               # Live provider-backed generation check through the Phase 3 client seam and boundary guardrail
|   |-- generate_howto.py                          # Phase 3 CLI for structured how-to generation from retrieved evidence
|   |-- howto_web.py                               # Separate browser test console for Phase 3 How-To generation and diagnostics
|   |-- generate_plan.py                           # Phase 4 CLI for structured planning and checklist generation
|   |-- generate_curation.py                       # Phase 5 CLI for curation proposals (missing/duplicate/outdated knowledge suggestions)
|   |-- run_curation_eval.py                       # Phase 5 curation evaluation harness with proposal-type/latency metrics
|   |-- review_quarantine.py                       # Phase 5 quarantine backlog summarizer with review-cadence recommendation
|   |-- triage_curation.py                         # Phase 5 curator triage CLI with accepted/deferred/rejected dispositions and human-approval checks
|   |-- rollback_curation.py                       # Phase 5 rollback CLI for reversing accepted triage decisions with audit history events
|   |-- curation_web.py                            # Phase 5 browser console for curator proposal review and triage/approval persistence
|   |-- report_corpus_quality.py                   # Phase 5 corpus quality control report for exact and near-duplicate signals
|   |-- run_phase6_readiness.py                    # Phase 6 readiness aggregator for eval metrics, observability timings, and index-evolution recommendation
|   |-- interface_cli.py                           # Unified Phase 6 CLI interface wrapper for eval orchestration and readiness runs
|   |-- interface_api.py                           # Optional Phase 6 local API wrapper for health and readiness endpoints
|   |-- portal_web.py                              # Unified client/admin web portal with route-level role gating and trust-state rendering
|   |-- planner_web.py                             # Browser test console wired directly to Phase 4 planning workflow and diagnostics
|   |-- run_plan_eval.py                           # Phase 4 planner evaluation harness with strict scoring, support/unknown metrics, and golden hash/review gate controls
|   |-- test_phase4.py                             # One-command Phase 4 verifier with stricter defaults and true gate-style golden enforcement by default
|   |-- run_howto_eval.py                          # Phase 3 How-To evaluation harness with section/citation/latency metrics
|   |-- run_llm_eval.py                            # Watsonx generation evaluation harness with latency and expected-output metrics
|   `-- run_eval.py                                # Evaluation harness for retrieval/citation/refusal metrics and report output
|-- src/
|   `-- work_knowledge_agent/                      # Main package source code
|       |-- __init__.py                            # Package metadata
|       |-- main.py                                # Startup entrypoint and bootstrap artifact check
|       |-- ingestion/                             # Load, chunk, validate, and write source artifacts
|       |   |-- __init__.py                        # Ingestion package marker
|       |   |-- chunking.py                        # Heading-aware chunking with fenced-code preservation
|       |   |-- metadata_extractor.py              # Extract/validate metadata with confidence and provenance
|       |   |-- models.py                          # Shared ingestion data contracts (`LoadedDocument`, quarantine records)
|       |   |-- preprocessing.py                   # Text normalization, content hashing, fallback loader sniffing
|       |   |-- manifest.py                        # SQLite manifest adapter for incremental file identity/state
|       |   |-- pipeline.py                        # Incremental ingestion orchestration with quarantine + atomic writes
|       |   `-- loaders/                           # File-type-specific source readers
|       |       |-- __init__.py                    # Loader package marker
|       |       |-- markdown_loader.py             # Read Markdown files for ingestion
|       |       |-- text_loader.py                 # Read plain text files for ingestion
|       |       |-- log_loader.py                  # Read log files for ingestion
|       |       |-- code_loader.py                 # Read source and config files for ingestion
|       |       `-- pdf_loader.py                  # PDF text-layer extraction loader (quarantine fallback handled upstream)
|       |-- retrieval/                             # Implemented retrieval stack for Phase 2 baseline
|       |   |-- __init__.py                        # Retrieval package marker
|       |   |-- embeddings.py                      # Planned embeddings logic
|       |   |-- vector_index.py                    # TF-IDF-lite vector index loader and vector scoring
|       |   |-- keyword_index.py                   # Keyword postings loader and lexical scoring
|       |   |-- hybrid_retriever.py                # Hybrid retrieval combining lexical/vector scores with metadata filters
|       |   |-- reranker.py                        # Metadata-aware reranking and confidence filtering
|       |   `-- query_rewriter.py                  # Query normalization and token rewrite helpers
|       |-- models/                                # Shared model access contracts for Phase 3+ generative workflows
|       |   |-- __init__.py                        # Models package exports for approved client contracts
|       |   |-- llm_client.py                      # Single LLM client seam with Watsonx/Anthropic API-backed implementations and provenance-carrying request/result types
|       |   `-- watsonx_credentials.py             # Package-local Watsonx credential loader used by the provider-backed client and scripts
|       |-- tools/                                 # Reusable retrieval and synthesis tools
|       |   |-- __init__.py                        # Tools package marker
|       |   |-- search_docs.py                     # Hybrid-retrieval search tool with metadata filters
|       |   |-- read_source.py                     # Source snippet reader by canonical source id/path
|       |   |-- extract_commands.py                # Planned command extraction tool
|       |   |-- extract_errors.py                  # Planned error signature extraction tool
|       |   |-- compare_procedures.py              # Planned procedure comparison tool
|       |   `-- summarize_project.py               # Planned project summarization tool
|       |-- agents/                                # Task-specific agents
|       |   |-- __init__.py                        # Agents package marker
|       |   |-- orchestrator.py                    # Planned workflow/agent router
|       |   |-- qa_agent.py                        # Citation-first Q&A answer builder with provenance citations
|       |   |-- howto_agent.py                     # Structured how-to prompt/context builder and section-normalizing response formatter
|       |   |-- planner_agent.py                   # Structured planner prompt/context builder and section-normalizing plan formatter
|       |   |-- debug_agent.py                     # Planned troubleshooting-focused agent
|       |   |-- curator_agent.py                   # Phase 5 baseline curator proposal engine for missing/duplicate/outdated knowledge suggestions
|       |   `-- verifier_agent.py                  # Planned citation and guardrail verification agent
|       |-- workflows/                             # End-to-end task workflows
|       |   |-- __init__.py                        # Workflows package marker
|       |   |-- qa_workflow.py                     # Hybrid retrieval + guardrail-enforced Q&A orchestration
|       |   |-- howto_workflow.py                  # Phase 3 retrieval-to-generation orchestration with LLM-boundary and citation checks
|       |   |-- planning_workflow.py               # Phase 4 retrieval-to-generation orchestration with goal-aware retrieval candidate expansion and source-aligned hit prioritization
|       |   |-- curation_workflow.py               # Phase 5 baseline curation orchestration with retrieval/filtering, proposal generation, and telemetry
|       |   `-- curation_triage_workflow.py        # Phase 5 curator triage workflow with disposition persistence and approval checkpoint enforcement
|       |   `-- curation_rollback_workflow.py      # Phase 5 rollback helpers for reversing accepted decisions and recomputing triage summaries
|       |-- guardrails/                            # Response safety enforcement layer
|       |   |-- __init__.py                        # Guardrails package marker
|       |   |-- citation_guardrail.py              # Citation integrity checks (presence, grounding ratio, command/code evidence match)
|       |   |-- confidentiality_guardrail.py       # Retrieval-hit confidentiality filtering
|       |   |-- llm_boundary_guardrail.py          # Pre-generation confidentiality/provider-mode checkpoint with redaction support
|       |   |-- unsupported_step_guardrail.py      # Unsupported/no-evidence detection
|       |   `-- human_approval.py                  # Human-approval guardrail contracts for curator write-back checkpoints
|       |-- evaluation/                            # Implemented quality metrics and reporting helpers
|       |   |-- __init__.py                        # Evaluation package marker
|       |   |-- golden_eval_control.py             # Golden-dataset hash/review verification helpers and gate-eligibility checks
|       |   |-- howto_eval.py                      # Phase 3 How-To evaluation helpers and metric aggregation
|       |   |-- llm_eval.py                        # Watsonx provider-path evaluation helpers and metric aggregation
|       |   |-- planning_eval.py                   # Phase 4 planner evaluation helpers with strict source coverage, task-overlap scoring, support/unknown checks, and failure-catalog metrics
|       |   |-- curation_eval.py                   # Phase 5 curation evaluation helpers with expected proposal-type matching metrics
|       |   |-- run_eval.py                        # Shared evaluation runner utilities
|       |   |-- metrics.py                         # Shared metric calculations
|       |   `-- reports.py                         # Shared report generation helpers
|       |-- interfaces/                            # User-facing interface modules
|       |   |-- __init__.py                        # Interfaces package marker
|       |   |-- cli.py                             # Unified interface CLI that routes eval/readiness commands through a single entrypoint
|       |   `-- api.py                             # Optional local API server exposing health and Phase 6 readiness endpoints
|       `-- security/                              # Data protection and classification helpers
|           |-- __init__.py                        # Security package marker
|           |-- redaction.py                       # Redact common secrets and sensitive identifiers
|           `-- data_classification.py             # Planned data classification utilities
`-- tests/                                         # Unit, integration, e2e, and fixture coverage
    |-- unit/                                      # Unit tests for ingestion and retrieval behavior
    |   |-- test_ingestion_incremental.py          # Verifies no-op incremental runs and quarantine routing
    |   |-- test_phase2_qa_workflow.py             # Verifies citation-first QA support and unsupported guardrail path
    |   |-- test_citation_guardrail.py             # Verifies citation grounding and command-evidence mismatch detection
    |   |-- test_llm_boundary_guardrail.py         # Verifies local/API model-boundary gating and redaction behavior
    |   |-- test_llm_client.py                     # Verifies Watsonx and Anthropic client parsing/retry behavior and provider selection without network access
    |   |-- test_llm_eval.py                       # Verifies LLM evaluation metric aggregation and expected-match reporting
    |   |-- test_phase3_howto_workflow.py          # Verifies structured How-To generation, citations, and API-boundary behavior
    |   |-- test_phase3_howto_eval.py              # Verifies How-To evaluation metric aggregation without live Watsonx dependency
    |   |-- test_phase4_planning_workflow.py       # Verifies structured plan generation, citations, and planning sections
    |   |-- test_phase4_planning_eval.py           # Verifies planner evaluation metric aggregation without live Watsonx dependency
    |   |-- test_phase5_curation_workflow.py       # Verifies Phase 5 baseline curation proposal generation and telemetry behavior
    |   |-- test_phase5_curation_eval.py           # Verifies Phase 5 curation evaluation metric aggregation and expected-type matching
    |   |-- test_phase5_curation_triage_workflow.py # Verifies Phase 5 triage disposition handling and human-approval enforcement
    |   |-- test_phase5_human_approval_guardrail.py # Verifies triage approval guardrail rejects bypass attempts and invalid accepted decisions
    |   `-- test_phase5_curation_triage_parity.py  # Verifies CLI and browser triage paths keep identical disposition/approval semantics
    |   `-- test_phase5_curation_rollback.py       # Verifies rollback updates accepted decisions to deferred state and refreshes summary metrics
    |-- integration/                               # Planned integration tests
    |-- e2e/                                       # Planned end-to-end tests
    `-- fixtures/                                  # Planned test fixtures
```

## Update Rule

- Update this file whenever folder structure changes or when a script/module meaningfully changes purpose.

## Last Updated
2026-07-05
