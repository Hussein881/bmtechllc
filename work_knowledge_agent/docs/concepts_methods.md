# Concepts and Methods Catalog

Purpose:
- Maintain a single source of truth for implemented technical methods.
- Track how each method is used, why it exists, and how effectiveness is measured.

Update Rule:
- Update this file whenever a new implementation technique is added, removed, or materially changed.
- Keep methods mapped to the phase where they were introduced.
- Link each method to concrete code locations.

## 1) Ingestion and Indexing Methods

### 1.1 Manifest-backed incremental ingestion
- Description: Tracks file identity and state to process only new or changed files.
- Why it matters: Reduces no-op runtime and enables auditable corpus updates.
- Where implemented:
  - src/work_knowledge_agent/ingestion/manifest.py
  - src/work_knowledge_agent/ingestion/pipeline.py
- Effectiveness signals:
  - No-op run skips unchanged files.
  - Manifest state matches active corpus records.

### 1.2 Preprocessing normalization and content hashing
- Description: Normalizes inputs before hashing/loading and supports stable identity.
- Why it matters: Improves deterministic change detection and loader reliability.
- Where implemented:
  - src/work_knowledge_agent/ingestion/preprocessing.py
- Effectiveness signals:
  - Stable hashes for unchanged content.
  - Reduced false-positive change detection.

### 1.3 Fallback loader sniffing
- Description: Uses extension-first routing with content-aware fallback for ambiguous files.
- Why it matters: Prevents ingestion loss from weak extension fidelity.
- Where implemented:
  - src/work_knowledge_agent/ingestion/preprocessing.py
  - src/work_knowledge_agent/ingestion/loaders/
- Effectiveness signals:
  - Lower unsupported-file routing for valid text-like content.

### 1.4 Heading-aware chunking with fenced-code preservation
- Description: Produces chunks that respect document structure and keeps code blocks intact.
- Why it matters: Improves retrieval grounding for procedural and command-heavy content.
- Where implemented:
  - src/work_knowledge_agent/ingestion/chunking.py
- Effectiveness signals:
  - Better section-level retrieval relevance.
  - Higher citation usefulness in generated answers.

### 1.5 Metadata confidence and provenance evaluation
- Description: Extracts metadata and evaluates records as pass, flagged, or rejected.
- Why it matters: Enables confidence-aware retrieval and auditability.
- Where implemented:
  - src/work_knowledge_agent/ingestion/metadata_extractor.py
- Effectiveness signals:
  - Malformed records rejected with explicit reason.
  - Confidence/provenance fields available in retrieval path.

### 1.6 Quarantine lane
- Description: Routes unsupported or failed documents to a dedicated artifact with reason detail.
- Why it matters: Avoids silent loss and supports remediation workflow.
- Where implemented:
  - src/work_knowledge_agent/ingestion/pipeline.py
- Effectiveness signals:
  - Quarantine artifact contains stage and error detail.

### 1.7 Atomic artifact writes
- Description: Writes through staging and atomic swap to avoid partial/corrupt outputs.
- Why it matters: Increases artifact integrity under interruption.
- Where implemented:
  - src/work_knowledge_agent/ingestion/pipeline.py
- Effectiveness signals:
  - No partial artifact states observed in interrupted scenarios.

## 2) Retrieval and Ranking Methods

### 2.1 Query rewriting
- Description: Normalizes query text and token stream before retrieval.
- Why it matters: Improves lexical and vector matching consistency.
- Where implemented:
  - src/work_knowledge_agent/retrieval/query_rewriter.py

### 2.2 Lexical retrieval (BM25-lite)
- Description: Scores documents with BM25-style term weighting for sparse/high-signal terms.
- Why it matters: Improves precision for commands, IDs, and exact operational language.
- Where implemented:
  - scripts/build_indexes.py
  - src/work_knowledge_agent/retrieval/keyword_index.py

### 2.3 Vector retrieval (TF-IDF-lite)
- Description: Scores by term-vector similarity for semantic-like matching.
- Why it matters: Improves recall for paraphrased phrasing.
- Where implemented:
  - src/work_knowledge_agent/retrieval/vector_index.py

### 2.4 Hybrid fusion retrieval
- Description: Combines lexical and vector scores into a unified ranking.
- Why it matters: Balances exact-match precision with semantic recall.
- Where implemented:
  - src/work_knowledge_agent/retrieval/hybrid_retriever.py

### 2.5 Metadata-aware reranking
- Description: Reorders and filters hits using confidence and confidentiality signals.
- Why it matters: Promotes trustworthy evidence and enforces policy.
- Where implemented:
  - src/work_knowledge_agent/retrieval/reranker.py

## 3) Guardrail and QA Methods

### 3.1 Citation-first QA synthesis
- Description: Builds answers from retrieved evidence and emits structured citations.
- Why it matters: Maintains traceability and user trust.
- Where implemented:
  - src/work_knowledge_agent/agents/qa_agent.py
  - src/work_knowledge_agent/workflows/qa_workflow.py

### 3.2 Citation integrity guardrail
- Description: Validates citation presence, grounding ratio, and command/code evidence match.
- Why it matters: Blocks unsupported command claims and weakly grounded responses.
- Where implemented:
  - src/work_knowledge_agent/guardrails/citation_guardrail.py

### 3.3 Confidentiality filtering
- Description: Removes retrieval hits above allowed confidentiality level.
- Why it matters: Prevents sensitive leakage in output context.
- Where implemented:
  - src/work_knowledge_agent/guardrails/confidentiality_guardrail.py
  - src/work_knowledge_agent/workflows/qa_workflow.py

### 3.4 Unsupported-step detection with entity-anchor checks
- Description: Marks answers unsupported when support signals fail, including missing identifier anchors.
- Why it matters: Improves refusal behavior for out-of-corpus entity-specific questions.
- Where implemented:
  - src/work_knowledge_agent/guardrails/unsupported_step_guardrail.py
  - src/work_knowledge_agent/workflows/qa_workflow.py

### 3.5 Stage-level telemetry
- Description: Captures timings and retrieval/guardrail counters per request.
- Why it matters: Enables latency diagnostics and gate performance evidence.
- Where implemented:
  - src/work_knowledge_agent/workflows/qa_workflow.py

### 3.6 LLM-boundary security guardrail
- Description: Enforces provider-mode and confidentiality checks before content may cross the model boundary, while redacting sensitive data in allowed requests.
- Why it matters: Preserves enterprise-safe behavior once generative workflows are introduced.
- Where implemented:
  - src/work_knowledge_agent/guardrails/llm_boundary_guardrail.py
- Effectiveness signals:
  - Non-public content is blocked from API mode.
  - Allowed local-mode requests are redacted before generation.

## 4) Generative Workflow Methods

### 4.1 Shared LLM client seam
- Description: Defines the single contract through which all model-backed generation must flow.
- Why it matters: Centralizes provider choice, provenance, and observability for Phase 3+ workflows.
- Where implemented:
  - src/work_knowledge_agent/models/llm_client.py
- Effectiveness signals:
  - Generative workflows can depend on one stable interface instead of provider-specific SDK calls.

### 4.2 Watsonx API-backed generation client
- Description: Implements the approved API-backed provider path using IBM Watsonx IAM auth and text generation requests.
- Why it matters: Enables Phase 3 synthesis work to proceed now while preserving the single-client seam and provenance metadata.
- Where implemented:
  - src/work_knowledge_agent/models/llm_client.py
  - src/work_knowledge_agent/models/watsonx_credentials.py
- Effectiveness signals:
  - Unit tests validate generation metadata parsing without network access.
  - Live-check script can perform a real generation call when Watsonx env vars are present.

### 4.3 Live LLM connectivity check
- Description: Runs a real Watsonx generation request through the LLM-boundary guardrail and prints output plus provenance metadata.
- Why it matters: Provides a concrete operational check that the generative path is configured and reachable.
- Where implemented:
  - scripts/check_llm.py
- Effectiveness signals:
  - Produces real model output when credentials are configured.
  - Fails early with actionable configuration errors when Watsonx env vars are missing.

### 4.4 Structured How-To generation workflow
- Description: Converts retrieved evidence into a fixed-section procedural response using the shared LLM client seam, then applies deterministic post-generation checks.
- Why it matters: This is the first real Phase 3 user-facing generative workflow, bridging Phase 2 retrieval into task-ready procedures.
- Where implemented:
  - src/work_knowledge_agent/agents/howto_agent.py
  - src/work_knowledge_agent/workflows/howto_workflow.py
  - scripts/generate_howto.py
- Effectiveness signals:
  - Output always contains required procedural sections.
  - Generated commands must remain grounded in retrieved evidence.

## 5) Evaluation Methods

### 5.1 Fixed-question evaluation harness
- Description: Runs a stable question set and reports retrieval/citation/refusal metrics.
- Why it matters: Makes quality drift measurable across iterations.
- Where implemented:
  - scripts/run_eval.py
  - data/eval/eval_questions.json
  - data/eval/expected_sources.json

### 5.2 Phase 2 unit guardrail coverage
- Description: Tests supported/unsupported workflow paths and citation command-evidence checks.
- Why it matters: Prevents regressions in correctness and safety behavior.
- Where implemented:
  - tests/unit/test_phase2_qa_workflow.py
  - tests/unit/test_citation_guardrail.py

### 5.3 Interactive browser Q&A test console
- Description: Runs a lightweight local web UI with a prompt box and rendered answer/citation diagnostics.
- Why it matters: Enables fast user-quality validation without parsing CLI JSON output.
- Where implemented:
  - scripts/ask_web.py
- Effectiveness signals:
  - Users can submit ad-hoc prompts and inspect support/citation/latency outputs in one screen.

### 5.4 LLM provider-path evaluation harness
- Description: Runs a fixed prompt set against the Watsonx-backed Phase 3 generation path and reports success, expected-match, token, and latency metrics.
- Why it matters: Gives the generative agent path a repeatable performance and quality scorecard before full How-To workflow integration.
- Where implemented:
  - src/work_knowledge_agent/evaluation/llm_eval.py
  - scripts/run_llm_eval.py
  - data/eval/llm_eval_cases.json
- Effectiveness signals:
  - Emits p50/p95 latency and expected-output match rate.
  - Fails fast with actionable configuration guidance when Watsonx runtime settings are missing.

### 5.5 How-To workflow evaluation harness
- Description: Runs realistic operational prompts against the Phase 3 How-To workflow and measures section completeness, citation status, expected command presence, source matching, and latency.
- Why it matters: This is the first Gate 3-style quality packet for the actual user-facing generative workflow, not just the provider path.
- Where implemented:
  - src/work_knowledge_agent/evaluation/howto_eval.py
  - scripts/run_howto_eval.py
  - data/eval/howto_eval_cases_golden.json
  - data/eval/howto_eval_cases_exploratory.json
- Effectiveness signals:
  - Live Watsonx golden baseline report now exists in `data/eval/howto_report_latest.json`.
  - Reports repeated-trial distributions, answer text per trial, and separates frozen gate evals from exploratory tuning prompts.

## 5) Current Effectiveness Snapshot

Latest known signals:
- Retrieval source hit rate: 100.0%
- Citation source hit rate: 100.0%
- Refusal accuracy: 100.0%
- Citation guardrail pass rate: 80.0%
- Latency p50: about 251 ms
- Latency p95: about 274 ms

Source of metrics:
- data/eval/report_latest.json

## 6) Phase 5 Curation Hardening Methods

### 6.1 Calibrated duplicate/outdated confidence scoring
- Description: Computes duplicate and outdated proposal confidence using calibrated signals (similarity distance from threshold and content age relative to cutoff) instead of fixed constants.
- Why it matters: Reduces confidence inflation and gives reviewers more meaningful prioritization cues.
- Where implemented:
  - src/work_knowledge_agent/agents/curator_agent.py
  - src/work_knowledge_agent/workflows/curation_workflow.py
  - scripts/generate_curation.py
  - scripts/run_curation_eval.py
- Effectiveness signals:
  - Proposal confidence values vary with observed evidence strength.
  - Curation eval quality remains stable after calibration.

### 6.2 Triage productivity telemetry
- Description: Tracks triage operational metrics including approval ratio and decision latency p50/p95.
- Why it matters: Enables Gate 5 reviewer-operability evidence, not only proposal-quality evidence.
- Where implemented:
  - src/work_knowledge_agent/workflows/curation_triage_workflow.py
  - scripts/triage_curation.py
  - scripts/curation_web.py
- Effectiveness signals:
  - Triage artifact includes `approval_ratio_pct`, `decision_latency_ms_p50`, and `decision_latency_ms_p95`.
  - Browser and CLI paths produce consistent triage summaries.

### 6.3 Corpus duplicate quality controls
- Description: Produces exact-hash dedupe baseline metrics and near-duplicate candidate reports for remediation planning.
- Why it matters: Keeps corpus quality measurable and actionable as ingestion volume grows.
- Where implemented:
  - scripts/report_corpus_quality.py
  - docs/corpus_quality.md
- Effectiveness signals:
  - Report artifact captures duplicate rates, candidate counts, and top near-duplicate pairs.
  - Control thresholds can be tuned without changing workflow contracts.

### 6.4 Rollback governance control
- Description: Reverses accepted curation decisions by decision id and persists rollback events in append-only history.
- Why it matters: Enables reversible governance and protects against irreversible false-positive acceptance.
- Where implemented:
  - src/work_knowledge_agent/workflows/curation_rollback_workflow.py
  - scripts/rollback_curation.py
  - data/eval/curation_triage_history.jsonl
- Effectiveness signals:
  - Rolled-back decisions transition from accepted to deferred with rollback metadata.
  - History stream records both triage snapshots and rollback events.

## 7) Phase 6 Readiness Methods

### 7.1 Unified readiness aggregation and observability recommendation
- Description: Aggregates cross-phase evaluation metrics, optional ingest/index stage timings, and emits rebuild-vs-incremental recommendation from explicit thresholds.
- Why it matters: Makes Gate 6 evidence repeatable and reduces manual reviewer packet assembly drift.
- Where implemented:
  - scripts/run_phase6_readiness.py
  - data/eval/phase6_readiness_latest.json
  - data/eval/phase6_readiness_packet.md
- Effectiveness signals:
  - Single report includes QA/How-To/Planner/Curation/LLM quality metrics plus observability timings.
  - Recommendation clearly states whether warning thresholds trigger rebuild concern.
  - Markdown packet is generated with reviewer sign-off fields.

### 7.2 Curation spot-audit disagreement signal
- Description: Estimates review disagreement from triage history using rollback events relative to accepted decision volume.
- Why it matters: Pairs approval ratio with an independent correction signal to surface governance quality drift.
- Where implemented:
  - scripts/run_phase6_readiness.py
  - data/eval/curation_triage_history.jsonl
- Effectiveness signals:
  - Readiness report includes `spot_audit_disagreement_rate_pct` with accepted and rollback event counts.

### 7.3 Unified interface CLI routing
- Description: Provides one command surface to run phase eval harnesses and readiness generation instead of script-by-script invocation.
- Why it matters: Reduces operator error and makes repeatable gate execution simpler.
- Where implemented:
  - src/work_knowledge_agent/interfaces/cli.py
  - scripts/interface_cli.py
- Effectiveness signals:
  - `phase6-readiness` and `all-evals` commands execute multi-step reporting flows through one interface.

### 7.4 Optional readiness API surface
- Description: Exposes local HTTP endpoints for health, readiness artifact retrieval, and triggerable readiness regeneration.
- Why it matters: Adds API-path interface parity in Phase 6 without replacing deterministic workflows.
- Where implemented:
  - src/work_knowledge_agent/interfaces/api.py
  - scripts/interface_api.py
- Effectiveness signals:
  - `GET /health` and `GET /phase6/readiness` return live payloads.
  - `POST /phase6/readiness/run` executes readiness generation and returns command results.

## Last Updated
2026-07-05
