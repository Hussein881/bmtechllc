# Architecture

## Design Principles
- Ground outputs in retrieved evidence.
- Prefer deterministic workflows before autonomous behavior.
- Keep interfaces small and explicit.
- Make safety checks part of default execution paths.

## High-Level Flow
1. Ingest source documents.
2. Normalize and chunk with metadata.
3. Build semantic and keyword indexes.
4. Retrieve with hybrid strategy.
5. Synthesize response through task-specific agent workflow.
6. Verify citations and unsupported steps.
7. Return response (or safe fallback with unknowns).

## Core Components

### Preprocessing Layer
Responsibilities:
- Normalize encoding and line endings before hashing/loading.
- Apply extension-first routing with content fallback for ambiguous files.
- Run early secret/confidentiality checks and route failures to quarantine.

### Ingestion Layer
Responsibilities:
- Parse supported file types.
- Produce normalized chunk records.
- Attach metadata fields required for filtering and traceability.

### Identity and Manifest Layer
Responsibilities:
- Track file identity and processing state for incremental ingestion.
- Detect new/changed/deleted files with normalized content hashing.
- Preserve provenance and processing-version metadata for reproducibility.

### Indexing Layer
Responsibilities:
- Build vector index for semantic similarity.
- Build keyword index for lexical matching.
- Maintain metadata store for constrained retrieval.

### Retrieval Layer
Responsibilities:
- Rewrite/normalize queries where needed.
- Execute hybrid retrieval.
- Rerank candidates and return top context slices.

### Agent Layer
Roles:
- Orchestrator: routes request by intent.
- Q&A agent: concise cited answer.
- How-to agent: procedure format output.
- Planner agent: checklist and open questions.
- Curator agent: update proposals only.
- Verifier agent: citation and support checks.

### Guardrails Layer
Checks:
- Citation enforcement.
- Unsupported-step detection.
- Confidentiality filtering.
- Human approval on write-back paths.

### Quarantine and Quality Layer
Responsibilities:
- Store failed/invalid documents with error context instead of silent drop.
- Distinguish hard rejects from low-confidence flags.
- Feed remediation and retry workflows.

## Tool Contracts (Minimum)
- `search_docs(query, filters)` -> ranked candidates + source ids.
- `read_source(source_id, section)` -> canonical source snippet.
- `extract_commands(context)` -> command candidates with provenance.
- `extract_errors(context)` -> error signatures with provenance.
- `build_checklist(goal, context)` -> ordered tasks + dependencies + unknowns.

## Output Contracts
- All final outputs include citations.
- Any low-confidence or ungrouded step is labeled unsupported.
- If evidence is insufficient, return explicit unknowns and follow-up questions.

## Artifact Strategy
- Use manifest-backed incremental ingestion for day-to-day runs.
- Write artifacts via staging + atomic swap to avoid partial/corrupt outputs.
- Keep keyword and vector index artifacts in non-colliding output paths.
- Defer segment-based incremental index merge until rebuild-time trigger threshold is reached.

## Deferred Decisions (Intentional)
- Semantic chunking and OCR for scanned PDFs.
- Vector database migration.
- Embedding-based semantic deduplication.

## Data and Security Notes
- Keep confidential/raw docs out of tracked artifacts.
- Redact sensitive text before broad sharing.
- Keep audit trail for curation proposals and approvals.

## Architecture Decisions Log
Use this format for major decisions:
- Decision ID:
- Date:
- Status: proposed | accepted | superseded
- Context:
- Decision:
- Consequences:

### Decision ID: ADR-INGEST-001
- Date: 2026-07-04
- Status: accepted
- Context: Full rebuild ingestion was too slow and made change tracking opaque.
- Decision: Introduce SQLite manifest-backed identity tracking for new/changed/deleted file handling.
- Consequences: Ingestion became incremental and auditable; manifest maintenance is now a critical path dependency.

### Decision ID: ADR-INGEST-002
- Date: 2026-07-04
- Status: accepted
- Context: Unsupported or low-quality documents were previously either dropped or mixed with valid outputs.
- Decision: Add explicit quarantine lane with reason/stage/detail records in a dedicated artifact.
- Consequences: Better remediation workflows and safer downstream retrieval inputs at the cost of one extra artifact to monitor.

### Decision ID: ADR-INGEST-003
- Date: 2026-07-04
- Status: accepted
- Context: Direct artifact writes risked partial/corrupt outputs if interrupted.
- Decision: Use staging file writes plus atomic swap for chunk/metadata/quarantine artifacts.
- Consequences: Artifact integrity improved; slight write overhead is acceptable for reliability goals.

### Decision ID: ADR-GOV-001
- Date: 2026-07-04
- Status: accepted
- Context: Phase transitions could pass technical checks without explicit business-owner quality/performance acceptance.
- Decision: Make human-in-the-loop quality + performance sign-off mandatory at every phase gate and standardize evidence in `docs/performance.md`.
- Consequences: Stronger delivery control and stakeholder trust, with slightly higher review overhead per gate.

### Decision ID: ADR-RET-001
- Date: 2026-07-04
- Status: accepted
- Context: Raw term-frequency lexical scoring underweighted high-signal sparse query terms and hurt retrieval precision on operational prompts.
- Decision: Upgrade keyword index and scorer to BM25-lite payload and scoring while preserving backward compatibility with legacy postings artifacts.
- Consequences: Improved lexical relevance and stability with minimal migration risk; index payload now carries BM25 parameters and corpus stats.

### Decision ID: ADR-RET-002
- Date: 2026-07-04
- Status: accepted
- Context: Retrieval-only support checks could incorrectly mark unsupported entity-specific queries as supported when partial token overlap existed.
- Decision: Add query entity-anchor validation (tokens containing digits must be present in evidence) as an additional support gate in QA workflow.
- Consequences: Better refusal accuracy on out-of-corpus identifiers (for example project IDs), with stricter support threshold that may require further tuning on noisy corpora.

### Decision ID: ADR-LLM-001
- Date: 2026-07-04
- Status: accepted
- Context: Phase 3 and Phase 4 require generative synthesis, but the implementation plan previously did not define where model calls occur or how they are governed.
- Decision: Introduce the first explicit LLM boundary in Phase 3 (How-To) and the second in Phase 4 (Planner), while keeping Phase 2 retrieval/Q&A LLM-free by default.
- Consequences: Retrieval quality remains measurable without generation noise in Phase 2; Phase 3+ now require model-boundary security, provenance, and evaluation controls before implementation starts.

### Decision ID: ADR-LLM-002
- Date: 2026-07-04
- Status: accepted
- Context: Unstructured provider-specific model calls would fragment security, provenance, and observability across workflows.
- Decision: Require all future model calls to route through a single `llm_client` seam with prompt/model provenance logging and deterministic guardrails remaining the final non-bypassable gate.
- Consequences: Better swappability and traceability; Phase 3 implementation is now blocked on finalizing the client contract and LLM-boundary guardrail design.

### Decision ID: ADR-LLM-003
- Date: 2026-07-04
- Status: accepted
- Context: The user chose to leave local-model work as a placeholder and focus initial Phase 3 execution on an API-backed provider path using existing Watsonx credentials.
- Decision: Implement Watsonx as the first concrete provider behind the shared LLM client seam, while retaining the local-only client as a placeholder contract.
- Consequences: Phase 3 can proceed with real generation infrastructure now; shell/runtime configuration for Watsonx credentials becomes the immediate operational prerequisite for live checks and workflow testing.

### Decision ID: ADR-LLM-004
- Date: 2026-07-04
- Status: superseded
- Context: The initial Watsonx `/ml/v1/text/generation` path with `ibm/granite-3-8b-instruct` produced deprecation/withdrawal warnings and unstable eval behavior.
- Decision: Migrate the provider path to `/ml/v1/text/chat` and switch the default model to `ibm/granite-4-h-small`.
- Consequences: The live provider-path eval now succeeds cleanly with 100% success and expected-match on the starter cases; input token counts increased because chat formatting adds system/user message structure.

### Decision ID: ADR-LLM-005
- Date: 2026-07-04
- Status: accepted
- Context: The user requested that the repository-wide default Watsonx model be `ibm/granite-3-8b-instruct` while retaining chat-endpoint compatibility and provider seam controls.
- Decision: Keep the `/ml/v1/text/chat` provider path from ADR-LLM-004 but reset the default model selection in the shared client seam back to `ibm/granite-3-8b-instruct`.
- Consequences: Runtime behavior now follows explicit user preference while preserving boundary controls, retry/backoff behavior, and chat-response parsing contracts.

### Decision ID: ADR-EVAL-001
- Date: 2026-07-04
- Status: accepted
- Context: How-To evaluation quality could be unintentionally inflated when expected outputs were tuned in the same dataset used for gate decisions.
- Decision: Split How-To evaluation into golden (frozen) and exploratory (mutable) sets and enforce integrity via a golden metadata manifest with hash and review status.
- Consequences: Gate-style runs are traceable and resistant to contamination; gate progression now depends on explicit review status and hash checks.

### Decision ID: ADR-PLAN-001
- Date: 2026-07-04
- Status: accepted
- Context: Phase 4 needed measurable quality signals before broader interface expansion.
- Decision: Introduce a dedicated planner evaluation harness (`planning_eval.py` + `run_plan_eval.py`) with required-sections, citation, expected-task/source, and latency metrics.
- Consequences: Phase 4 now has baseline evidence and clear tuning targets; expected-task lexical matching currently requires rubric calibration before gate-readiness.

### Decision ID: ADR-EVAL-002
- Date: 2026-07-04
- Status: accepted
- Context: Permissive planner eval matching and pass-oriented defaults masked defects and encouraged smoke-test optimization over hole discovery.
- Decision: Make planner eval failure-seeking by default via strict all-source matching, token-overlap task matching, failure catalogs, coverage metrics, and gate-ready signals.
- Consequences: Phase 4 evaluation now fails when planning holes exist, which increases signal quality and prevents premature progression based on superficial pass rates.

### Decision ID: ADR-PLAN-002
- Date: 2026-07-04
- Status: accepted
- Context: After strict eval hardening, Phase 4 remained blocked by source-selection and task-intent mismatches despite strong citation/section pass rates.
- Decision: Add goal-aware retrieval candidate expansion and source-aligned reranking in planning workflow, plus eval-aligned task-intent normalization in planner output processing.
- Consequences: Strict Phase 4 eval now surfaces then closes real holes without lowering thresholds; task/source match rates can reach full compliance under the stricter gate.

### Decision ID: ADR-EVAL-003
- Date: 2026-07-04
- Status: accepted
- Context: Planner eval results could drift if tuning changes and gate decisions reuse mutable eval assets.
- Decision: Split planner eval assets into golden and exploratory sets and enforce golden integrity/review gating through a hash manifest and explicit gate-eligibility checks in `run_plan_eval.py`.
- Consequences: Gate-style Phase 4 runs are now reproducible and tamper-evident; unreviewed golden runs require explicit diagnostic override and cannot be mistaken for sign-off evidence.

### Decision ID: ADR-EVAL-004
- Date: 2026-07-04
- Status: accepted
- Context: Planner output normalization had evolved toward expected eval language, risking coupling between generator behavior and answer-key wording.
- Decision: Remove eval-targeted task-intent insertion from planner output normalization and keep eval as an independent verifier.
- Consequences: Phase 4 quality numbers may drop on harder cases, but resulting metrics are more trustworthy and failure signals are more actionable.

### Decision ID: ADR-EVAL-005
- Date: 2026-07-04
- Status: accepted
- Context: Structural planner metrics alone did not test ambiguity and insufficient-evidence behavior.
- Decision: Expand planner golden set with adversarial cases and add support/unknown/open-questions expectation metrics (`expected_support_match_rate_pct`, `unknown_signal_match_rate_pct`, `open_questions_presence_rate_pct`).
- Consequences: Gate criteria now measure planner honesty and clarification behavior in addition to structure/citations/task-source matching; Phase 4 gate readiness now depends on a harder and more realistic evaluation surface.

### Decision ID: ADR-EVAL-006
- Date: 2026-07-04
- Status: accepted
- Context: Phase 4 adversarial golden runs correctly produced unsupported outputs for out-of-corpus prompts, but gate math still required 100% global supported/citation rates, creating false failures.
- Decision: Evaluate support/citation gate metrics on support-expected runs and apply coverage-aware task pass logic (>=2/3 expected tasks matched) with concept-aware token normalization.
- Consequences: Gate signals now align with intended planner behavior on unsupported prompts while preserving strictness on required evidence-backed outputs; Phase 4 gate readiness reflects true quality instead of denominator artifacts.

### Decision ID: ADR-PH5-001
- Date: 2026-07-04
- Status: accepted
- Context: Phase 5 requires practical curation outputs quickly, but no curator runtime implementation existed yet.
- Decision: Start with a deterministic heuristic curator baseline that proposes `missing_knowledge`, `duplicate_content`, and `outdated_content` suggestions from retrieval evidence before adding model-assisted curation reasoning.
- Consequences: Phase 5 now has executable baseline behavior and testable outputs; proposal precision will require iterative calibration and optional reviewer UI improvements.

### Decision ID: ADR-PH5-002
- Date: 2026-07-04
- Status: accepted
- Context: Phase 5 needed objective quality visibility and backlog governance, not only raw proposal generation.
- Decision: Add a dedicated curation evaluation harness (`run_curation_eval.py`) and quarantine review reporter (`review_quarantine.py`) as default Phase 5 controls.
- Consequences: Phase 5 now tracks proposal-type match rates, proposal volume, and latency while providing measurable quarantine cadence signals; these controls become inputs to future Gate 5 sign-off evidence.

### Decision ID: ADR-PH5-003
- Date: 2026-07-04
- Status: accepted
- Context: Phase 5 needed auditable human-in-the-loop triage outcomes before any accepted proposal can progress toward write-back actions.
- Decision: Implement a dedicated triage workflow (`curation_triage_workflow.py`) and guardrail contracts (`human_approval.py`) that enforce explicit approval for `accepted` dispositions and persist triage artifacts.
- Consequences: Curator outputs now support operational disposition tracking (`accepted`, `deferred`, `rejected`) with approval evidence; write-back planning cannot proceed from accepted proposals without a reviewer-approved checkpoint.

### Decision ID: ADR-PH5-004
- Date: 2026-07-04
- Status: accepted
- Context: CLI triage validated control logic but reviewer adoption required an interactive interface with visible evidence and one-page decision flow.
- Decision: Add `scripts/curation_web.py` as a browser-native Phase 5 review surface that renders proposals/evidence and submits triage decisions through the same approval-enforced workflow contracts.
- Consequences: Human review is easier to execute and verify in demos/operations; UI and CLI now share the same triage enforcement path and output artifact contract.

### Decision ID: ADR-PH5-005
- Date: 2026-07-05
- Status: accepted
- Context: Phase 5 still lacked measurable reviewer-operability and corpus duplicate controls required for complete gate evidence.
- Decision: Add triage productivity telemetry (approval ratio, decision latency p50/p95) and a dedicated corpus quality control report (`report_corpus_quality.py`) with exact-hash and near-duplicate metrics.
- Consequences: Gate 5 evidence can now include reviewer throughput/latency and duplicate-control baselines, not only proposal-type quality metrics.

### Decision ID: ADR-UI-001
- Date: 2026-07-05
- Status: accepted
- Context: Separate browser interfaces for Ask/How-To/Planner/Triage made policy semantics inconsistent and increased user trust ambiguity, especially for blocked vs restricted vs unsupported states.
- Decision: Introduce a unified portal (`scripts/portal_web.py`) with route-level role separation (`user` vs `admin`) and explicit trust-state rendering (`verified`, `unsupported`, `blocked`, `restricted`, `unreviewed`) derived from existing workflow guardrail signals.
- Consequences: Policy interpretation is now centralized in one UI shell with clearer role boundaries; future interface work should extend this route shell instead of adding more disconnected web scripts.

### Decision ID: ADR-PH5-006
- Date: 2026-07-05
- Status: accepted
- Context: Evaluator review highlighted that approval telemetry without audit-grade per-decision provenance could mask enforcement drift between browser and CLI paths.
- Decision: Add explicit per-decision audit records (decision id, channel, actor, timestamps) and require parity checks between CLI and web triage semantics.
- Consequences: Phase 5 governance now has durable decision-level auditability and automated drift checks across triage entry paths.

### Decision ID: ADR-PH5-007
- Date: 2026-07-05
- Status: accepted
- Context: Evaluator review identified missing rollback capability as a critical risk if incorrect accepted decisions cannot be reversed with traceable audit continuity.
- Decision: Add rollback controls via `curation_rollback_workflow.py` and `rollback_curation.py`, plus append-only `curation_triage_history.jsonl` events from both CLI and browser triage paths.
- Consequences: Accepted decisions are now reversible with explicit reviewer attribution, refreshed summary metrics, and durable rollback/triage event history.

### Decision ID: ADR-PH6-001
- Date: 2026-07-05
- Status: accepted
- Context: Phase 6 requires a unified view of quality metrics, observability timings, and index-evolution decisions, but evidence was spread across separate report artifacts.
- Decision: Add `scripts/run_phase6_readiness.py` to aggregate existing eval artifacts, optionally run ingestion/index observability checks, and emit a consolidated readiness report with rebuild-vs-incremental recommendation.
- Consequences: Gate-readiness evidence is now generated from one script, reducing manual packet assembly drift and making phase transition checks repeatable.

### Decision ID: ADR-PH6-002
- Date: 2026-07-05
- Status: accepted
- Context: Operators needed a stable interface surface for running eval stacks and readiness actions without memorizing many script-specific command shapes.
- Decision: Implement unified CLI/API interfaces (`interfaces/cli.py`, `interfaces/api.py`) with lightweight wrappers (`scripts/interface_cli.py`, `scripts/interface_api.py`) as the default Phase 6 interaction layer.
- Consequences: Phase 6 now has a complete CLI interface and optional local API path with parity to readiness/reporting workflows, reducing operational complexity.

## Last Updated
2026-07-05
