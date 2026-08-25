# Work Knowledge Agent - Implementation Plan

## 1. Objective
Build a local-first, agentic engineering knowledge system that:
- indexes unstructured technical notes and docs,
- answers with citations,
- generates step-by-step how-to procedures,
- decomposes vague goals into actionable task checklists,
- proposes curated knowledge-base updates.

This plan prioritizes reliability and enterprise safety over autonomy:
- RAG + deterministic workflow + limited agents + human approval.
- Q&A remains retrieval-first; LLM synthesis is introduced explicitly and only where the task requires generation.

## 2. Scope and Non-Goals
### In Scope (MVP -> V1)
- Document ingestion for markdown/text/pdf/log/code/readme files.
- Hybrid retrieval (semantic + keyword + metadata filters).
- Cited Q&A.
- How-to procedure generation.
- Task breakdown/planning output.
- Knowledge curation suggestions (no auto-write by default).
- Evaluation harness and score reporting.

### Out of Scope (initially)
- Autonomous shell execution.
- Multi-agent debate/self-modifying behavior.
- Browser automation.
- Fine-tuning/custom model training.

## 3. Architecture (Practical)
1. Ingestion pipeline parses files and produces normalized chunks + metadata.
2. Indexing builds:
- semantic vector index,
- keyword index,
- metadata store.
3. Orchestrator routes requests to tools/agents.
4. Agents synthesize outputs from retrieved context only.
5. Phase 2 Q&A may remain fully extractive and LLM-free to preserve deterministic retrieval evaluation.
6. Phase 3+ generative workflows call models only through a single LLM client seam after retrieval/filtering.
7. Deterministic guardrails remain the final non-bypassable gate; any verifier agent is additive only.
8. Guardrails block unsafe/uncertain output paths.

## 4. Folder Structure (Recommended)
Use this as the target project structure under this folder.

```text
work-knowledge-agent/
  README.md
  IMPLEMENTATION_PLAN.md
  pyproject.toml
  .env.example
  .gitignore

  config/
    settings.py
    prompts.yaml
    logging.yaml

  docs/
    architecture.md
    retrieval_design.md
    guardrails.md
    llm_strategy.md
    eval_strategy.md

  data/
    raw/                  # input docs (synthetic or approved)
    processed/
      chunks.jsonl
      metadata.parquet
    indexes/
      vector/
      keyword/
    eval/
      eval_questions.json
      expected_sources.json

  src/
    work_knowledge_agent/
      __init__.py
      main.py

      ingestion/
        __init__.py
        loaders/
          markdown_loader.py
          text_loader.py
          pdf_loader.py
          log_loader.py
          code_loader.py
        chunking.py
        metadata_extractor.py
        pipeline.py

      retrieval/
        __init__.py
        embeddings.py
        vector_index.py
        keyword_index.py
        hybrid_retriever.py
        reranker.py
        query_rewriter.py

      models/
        __init__.py
        llm_client.py

      tools/
        __init__.py
        search_docs.py
        read_source.py
        extract_commands.py
        extract_errors.py
        compare_procedures.py
        summarize_project.py

      agents/
        __init__.py
        orchestrator.py
        qa_agent.py
        howto_agent.py
        planner_agent.py
        debug_agent.py
        curator_agent.py
        verifier_agent.py

      workflows/
        __init__.py
        qa_workflow.py
        howto_workflow.py
        planning_workflow.py
        curation_workflow.py

      guardrails/
        __init__.py
        citation_guardrail.py
        confidentiality_guardrail.py
        llm_boundary_guardrail.py
        unsupported_step_guardrail.py
        human_approval.py

      evaluation/
        __init__.py
        run_eval.py
        metrics.py
        reports.py

      interfaces/
        cli.py
        api.py

      security/
        redaction.py
        data_classification.py

  tests/
    unit/
    integration/
    e2e/
    fixtures/

  scripts/
    ingest_docs.py
    build_indexes.py
    ask.py
    generate_howto.py
    generate_plan.py
    run_eval.py
```

## 5. Metadata Schema (Must-Have)
Each chunk should include:
- source_file
- section_heading
- project
- machine
- component
- mode (pf/vf/etc)
- doc_type (runbook/log/meeting/readme/script)
- date
- owner
- tags
- confidentiality_level
- extracted_commands
- extracted_errors

Without this schema, engineering retrieval quality will degrade quickly.

## 6. Core Agent/Tool Contracts
### Orchestrator
- Routes intent to `qa_agent`, `howto_agent`, `planner_agent`, or `curator_agent`.
- Routes generative requests through the approved LLM boundary defined in `docs/llm_strategy.md`.

### Minimum tools
- `search_docs(query, filters)`
- `read_source(source_id, section)`
- `extract_commands(context)`
- `extract_errors(context)`
- `build_checklist(goal, context)`
- `llm_client.generate(prompt, context, metadata)`

### Verifier rules
- No final answer without citations.
- Mark steps as `supported` or `unsupported`.
- If support is insufficient, respond with explicit unknowns.
- Deterministic guardrails remain mandatory even when a verifier agent or LLM-based reviewer is added later.

## 7. Security and Data Policy
- Default to synthetic/redacted documents for public demos.
- Keep real work docs out of git and local public artifacts.
- Apply confidentiality filter before response generation.
- Human approval required for any write-back/proposed document update.
- Before any LLM call, run confidentiality/classification and redaction checks at the LLM boundary.
- Prefer local model runtimes; any API-based model path must be explicitly approved, documented, and gated by boundary controls.

## 7.1 LLM Boundary Strategy
- Phase 2 stays LLM-free by default so retrieval quality can be measured without generation noise.
- Phase 3 (How-To) is the first approved LLM boundary because procedure assembly is structurally generative.
- Phase 4 (Planner) is the second approved LLM boundary because task decomposition is structurally generative.
- Phase 5 may use a mixed model: deterministic duplicate detection plus optional model-assisted curator reasoning.
- All model calls must flow through a single client seam (`models/llm_client.py`) with prompt/model provenance logging.
- `docs/llm_strategy.md` is the detailed design contract for provider choice, prompt versioning, provenance, and LLM-boundary security.

## 8. Phased Execution Plan
## Phase 0: Bootstrap (1-2 days)
Deliverables:
- Project scaffolding from folder structure.
- Base config and logging.
- Data policy doc and redaction utilities.

Exit criteria:
- Repo runs with `python -m work_knowledge_agent.main`.

## Phase 1: Ingestion + Indexing (Week 1)
Deliverables:
- Preprocessing baseline (encoding/line-ending normalization + extension-first routing with content fallback for ambiguous files).
- Loader normalization contract (`LoadedDocument`) and PDF text-layer support with quarantine for empty/failed extraction.
- Structure-aware chunking (heading-first split, size fallback, command/code block integrity).
- Metadata confidence + provenance fields and strict reject vs flag validation outcomes.
- Manifest-backed incremental ingestion (new/changed/deleted handling) with deterministic chunk IDs.
- Artifact write safety (staging + atomic swap), plus collision-free index artifact names.

Exit criteria:
- `scripts/ingest_docs.py` supports incremental no-op runs on unchanged corpus.
- `scripts/build_indexes.py` runs successfully with non-colliding output artifacts.
- Quarantine lane is functional and failed files are auditable.
- Ingestion and index build emit stage timing metrics.

## Phase 2: Retrieval + Cited Q&A (Week 2)
Deliverables:
- Hybrid retriever and reranker.
- Basic Q&A agent with citations.
- Retrieval uses metadata filters including confidence, confidentiality tier, and section path.
- Chunk-parent context and provenance-backed citation formatting.
- Lexical retrieval upgraded to BM25-style scoring baseline.
- Citation integrity checks include claim grounding and command/code exact-match validation.
- Defense-in-depth confidentiality check at output assembly stage.
- Evaluation harness (`scripts/run_eval.py`) with fixed question set and report artifact.

Exit criteria:
- Answers include source references consistently.
- Retrieval quality is benchmarked against fixed eval questions with confidence-aware filtering.
- Refusal accuracy on unanswerable eval questions reaches target threshold.
- Citation guardrail metrics and latency p50/p95 are captured in eval report.

## Phase 3: How-To Agent (Week 3)
Deliverables:
- LLM boundary implementation with a single client seam and model/prompt provenance capture.
- Procedure generation workflow.
- Output sections: summary, assumptions, prerequisites, steps, commands, validation, failure modes, sources.
- LLM-boundary security guardrail enforcing confidentiality/redaction before model calls.
- Workflow enforces command/code-block integrity and section-path-aware citations.
- Grounding checks for synthesized procedural text, not only extracted snippets.

Exit criteria:
- How-to answers reproducibly grounded in sources.
- Generated procedural steps respect unsupported-step guardrails and confidence thresholds.
- Procedure outputs record prompt version, model version, and retrieval evidence provenance.
- Local model path or approved API path is documented and validated against security constraints.

## Phase 4: Planner Agent (Week 4)
Deliverables:
- Planner workflow reuses the shared LLM client seam and prompt/version provenance.
- Task decomposition workflow from vague goals.
- Missing-context question generation.
- Planner explicitly surfaces low-confidence evidence and quarantined-source gaps.

Exit criteria:
- Planner outputs actionable checklists and open questions.
- Plan output includes dependencies + confidence/unknown markers tied to source evidence.
- Planner outputs record prompt/model provenance and cite evidence for generated dependencies when available.

## Phase 5: Curator Agent + Guardrails (Week 5)
Deliverables:
- Curator suggestions (duplicates/outdated/missing prereqs), with duplicate detection remaining deterministic by default.
- Citation and unsupported-step guardrails.
- Quarantine review and remediation workflow with retry policy.
- Corpus quality controls (exact hash dedupe baseline; near-duplicate strategy documented).
- Any verifier-agent logic is additive only and may not replace deterministic guardrails.

Exit criteria:
- No uncited final output; curator emits review proposals only.
- Quarantine backlog is measurable and actionable with review cadence.
- Curator outputs remain suggestions-only even if model-assisted reasoning is enabled.

## Phase 6: Evaluation + Interface (Week 6)
Deliverables:
- Evaluation harness and report generation.
- CLI complete; optional API endpoint.
- Performance and ingestion observability dashboard/report (discovery, ingest, artifact write, index build).
- Trigger-based recommendation for full rebuild vs incremental index evolution.
- Generation-quality reporting for How-To and Planner workflows, including provenance and optional token/cost telemetry.

Exit criteria:
- Baseline quality metrics tracked over fixed eval set.
- Performance baseline and scaling trigger thresholds are recorded and monitored.

## 9. Suggested Metrics
- Retrieval hit rate (top-k source match).
- Citation precision.
- Unsupported-step rate.
- Hallucination rate.
- Procedure completeness score.
- Task-plan actionability score.
- Refusal accuracy for unanswerable prompts.
- Command/code exact-match verification rate.
- Grounded-step precision for generated procedures.
- Prompt/model provenance capture rate.

## 10. Immediate Next Actions (This Repo)
1. Close current Gate 2 conditions by expanding eval prompts and adding grounding-threshold regression coverage.
2. Finalize `docs/llm_strategy.md` and the `models/llm_client.py` contract before Phase 3 implementation starts.
3. Design the LLM-boundary security guardrail and prompt/version provenance schema.
4. Implement How-To workflow only after the LLM boundary and evaluation rubric are locked.
5. Keep unscheduled scaffold components explicitly deferred until they are assigned to a gated phase.

## 11. Definition of Done (DoD) and Phase Gates
This section makes each phase pass/fail with measurable checks.

### DoD Rules (Apply to Every Phase)
- Functional: planned deliverables are implemented and runnable.
- Tests: required tests pass in CI/local with no known blocker.
- Observability: logs include request_id, component, and error classification.
- Safety: no uncited final outputs and no confidentiality bypass in default path.
- Documentation: design and operational docs updated for changed behavior.
- Human validation: a human reviewer runs quality/performance gate checks and signs off in `project_memory/04_EXECUTION.md` before phase transition.

### Human-In-The-Loop Gate Sign-Off (Mandatory)
Before any phase can be marked complete and before work starts on the next phase:
- Present a gate test packet to the human reviewer (owner) containing:
  - Quality checks run and observed outcomes.
  - Performance checks run and observed outcomes versus target.
  - Open risks, caveats, and proposed follow-up.
- Record explicit sign-off in `project_memory/04_EXECUTION.md` using:
  - Reviewer name,
  - Date,
  - Gate ID,
  - Decision: approved | approved-with-conditions | rejected,
  - Notes and required follow-up.
- If sign-off is not approved, keep the gate status as failing and do not advance phase.

### Phase Gate Checklist

#### Gate 0 (Bootstrap)
- `python -m work_knowledge_agent.main` runs successfully.
- `config/settings.py` and `config/logging.yaml` contain non-placeholder defaults.
- `docs/guardrails.md` and `security/redaction.py` include enforceable baseline policy and helper logic.
- Human quality/performance sign-off: confirms startup behavior, config safety defaults, and baseline startup timing are acceptable.

#### Gate 1 (Ingestion + Indexing)
- Ingestion supports all declared file types or explicitly records unsupported types.
- Metadata schema validation rejects malformed chunks with clear errors.
- Incremental ingest manifest tracks new/changed/deleted files.
- Failed parsing/validation routes to quarantine with error detail.
- `scripts/ingest_docs.py` and `scripts/build_indexes.py` pass smoke tests.
- Index artifact naming does not collide between keyword/vector outputs.
- Human quality/performance sign-off: reviews ingest/index output quality sample, quarantine auditability, and stage timing metrics.

#### Gate 2 (Retrieval + Cited Q&A)
- Hybrid retrieval returns ranked results with source identifiers.
- Q&A output includes citations for every factual claim.
- Unsupported claims are marked explicitly, never silently inferred.
- Retrieval source hit rate / recall@5 meets or exceeds 80% on the fixed eval set.
- Citation precision meets or exceeds 95% on the fixed eval set.
- Refusal accuracy on unanswerable prompts meets or exceeds 90%.
- Human quality/performance sign-off: reviews citation correctness on sample prompts and latency against Phase 2 targets.

#### Gate 3 (How-To)
- How-to output follows fixed section template.
- Commands and validation steps are source-grounded and cited.
- Failure modes include fallback guidance with explicit assumptions.
- All model calls flow through the shared LLM client seam.
- Prompt version and model version are captured in output provenance/logs.
- Deterministic guardrails still gate final output after generation.
- Grounded-step precision meets or exceeds 95% on the fixed procedure eval set.
- Gate decisions use a frozen golden eval set, not exploratory tuning prompts.
- Golden How-To eval is rerun for at least 5 trials per case and reported as a distribution, not a single-run score.
- The golden eval file must pass an integrity-manifest check and report its human review status in the gate packet.
- Human quality/performance sign-off: reviews procedure correctness/reproducibility and response-time stability.

#### Gate 4 (Planner)
- Planner outputs ordered tasks with dependencies and unknowns.
- Missing-context questions are generated when evidence is insufficient.
- Plan format is deterministic and test-assertable.
- All model calls flow through the shared LLM client seam with provenance logging.
- Task-plan actionability reaches a mean rubric score of at least 4.0/5.0 on the fixed planner review set.
- Human quality/performance sign-off: reviews plan actionability quality and generation latency consistency.

#### Gate 5 (Curator + Guardrails)
- Curator outputs suggestions only, never direct write-back.
- Citation and unsupported-step guardrails are enforced in the final path.
- Human approval checkpoint is required for all write proposals.
- Deterministic guardrails remain the release gate even if verifier-agent logic is enabled.
- Human quality/performance sign-off: reviews guardrail effectiveness and latency overhead from guardrail checks.

#### Gate 6 (Evaluation + Interface)
- Fixed eval set runs end-to-end and produces versioned reports.
- CLI path is stable; API optional path has equivalent guardrails.
- Baseline quality metrics are recorded and compared to prior runs.
- Human quality/performance sign-off: reviews evaluation trend quality and release-readiness performance profile.

## 12. Dependency Map (Execution Order)

### Hard Dependencies
- Phase 1 depends on Phase 0 config/logging and policy baselines.
- Phase 2 depends on validated chunk schema, provenance metadata, and incremental artifacts from Phase 1.
- Phase 3 and Phase 4 depend on retrieval quality and citation coverage from Phase 2.
- Phase 5 depends on stable outputs from Phase 2-4 plus quarantine/quality telemetry from Phase 1.
- Phase 6 depends on all prior phases and ingestion/index instrumentation to avoid evaluating incomplete system behavior.

### Re-Baselining Rule
If a hard dependency changes (schema, output format, guardrail contract), reopen affected gates and rerun impacted tests before proceeding.

## 13. Module Contract Template (Apply to New Files)
Each implementation module should define:
- Inputs: typed inputs and required metadata fields.
- Outputs: schema and deterministic structure.
- Errors: explicit error classes and user-safe messages.
- Logging: info/warn/error events and required context fields.
- Side effects: file writes, index mutations, network/model calls.
- Guardrail hooks: where citation/confidentiality checks are executed.

Use this template in component docs before expanding module complexity.

## 14. Test Strategy by Phase

### Minimum Required Test Types
- Unit tests for parsing, chunking, schema validation, ranking, and guardrail checks.
- Integration tests for ingestion-to-retrieval and retrieval-to-agent output chains.
- End-to-end tests for Q&A, how-to, planner, and curator workflows.
- Regression tests for citation coverage and unsupported-step detection.
- Frozen golden evals for gate decisions; exploratory evals are allowed for tuning but cannot substitute for the golden packet.

### Test Milestones
- End of Phase 0: startup smoke test + config load test.
- End of Phase 1: incremental ingest tests, quarantine tests, ingestion/index smoke + schema validation tests.
- End of Phase 2: retrieval relevance checks + citation regression tests.
- End of Phase 2: refusal accuracy checks + command exact-match guardrail tests.
- End of Phase 3-5: workflow output contract tests + guardrail enforcement tests.
- End of Phase 6: fixed eval suite + report generation validation.

## 15. Non-Functional Requirements (Baseline Targets)
Set initial targets early to prevent late redesign.

- Reliability:
  - No uncited final output in default path.
  - Fatal workflow error rate under 2% on eval set.
- Quality:
  - Retrieval source hit rate / recall@5 at or above 80% on fixed Phase 2 eval set.
  - Citation precision at or above 95% on fixed Phase 2 eval set.
  - Refusal accuracy at or above 90% on unanswerable eval prompts.
  - Grounded-step precision at or above 95% on fixed How-To eval set.
  - Planner actionability mean score at or above 4.0/5.0 on fixed review prompts.
- Performance:
  - P50 retrieval latency less than 1.5 seconds on local benchmark corpus.
  - P95 end-to-end Q&A latency less than 6 seconds (excluding model cold start).
  - P95 How-To latency less than 12 seconds on approved model path.
  - P95 Planner latency less than 12 seconds on approved model path.
  - Incremental ingest of unchanged corpus should skip processing work after discovery.
  - Full index rebuild warning threshold: sustained rebuild time > 2 minutes or corpus > 50k chunks.
- Scalability:
  - Ingestion pipeline handles at least 10k chunks without schema drift.
  - Manifest-backed ingest path handles file add/change/delete without full reprocessing.
- Observability:
  - Structured logs for each workflow stage with traceable request_id.
- Security:
  - Confidentiality filter applied before response synthesis in all workflows.
  - No content crosses the LLM boundary without passing classification/confidentiality checks.

Targets can be tuned after first benchmark run but must be explicit before Phase 2 completion.

## 16. Risk Register and Triggered Mitigations

### High-Priority Risks
- Metadata quality drift reduces retrieval precision.
- Citation formatting drift causes verifier false negatives.
- Over-automation introduces unsupported procedural steps.
- Sensitive content leakage through unredacted documents.

### Trigger Rules
- Retrieval hit rate drops >10% from baseline -> freeze feature expansion and audit metadata pipeline.
- Citation precision drops below threshold -> block release gate and rerun verifier tests.
- Unsupported-step rate rises sprint-over-sprint -> tighten planner/how-to prompts and verifier constraints.
- Confidentiality incident or near miss -> immediate incident review and policy hardening before merge.
- Refusal accuracy on unanswerable eval set drops below threshold -> block phase advance until support checks are tuned.

## 17. Change Control and ADR Process

### ADR Requirement
Architecture-affecting changes require an ADR entry with:
- context,
- decision,
- alternatives considered,
- consequences,
- rollback path.

### Approval Threshold
- Major changes (schema, output contracts, guardrail flow) require explicit approval before implementation.
- Minor internal refactors can proceed if tests remain green and contracts unchanged.

## 18. Rollout and Operational Readiness

### Pre-Release Checklist
- Runbook exists for ingest, index rebuild, eval execution, and rollback.
- Failure-mode documentation includes operator actions and safe defaults.
- Guardrails verified in both CLI and API pathways.
- Human approval points are testable and visible in logs.

### Release Rule
No public/demo release when any gate is failing, any critical risk is open without mitigation, or citation guardrails are bypassable.

## 19. Updated Immediate Execution Sequence
Use this sequence to reduce rework from current scaffold state.

1. Add manifest-backed incremental ingest identity layer (hashing + status + versioned processing metadata).
2. Add preprocessing normalization + loader contract + PDF text-layer support with quarantine fallback.
3. Upgrade chunking to heading-aware splitting and preserve command/code block integrity.
4. Extend metadata with confidence + provenance; split validation into reject vs flag outcomes.
5. Implement safe artifact writes (staging + atomic swap) and fix index naming collisions.
6. Add ingestion/index stage timing instrumentation and scaling trigger logs.
7. Implement hybrid retrieval + citation-first Q&A using new metadata filters.
8. Add eval harness and baseline golden-question report for retrieval/citation/refusal metrics.
9. Continue downstream workflow phases with confidence-aware guardrails and eval-gated releases.

## 20. Expert Review Adoption Decisions

### Adopted Now
- Manifest identity layer and incremental ingestion.
- Preprocessing normalization and loader contract standardization.
- Structure-aware chunking improvements.
- Metadata confidence and provenance fields.
- Quarantine lane for malformed/failed inputs.
- Artifact write safety + non-colliding index output names.
- Stage-level performance instrumentation.
- Explicit LLM boundary beginning in Phase 3, while Phase 2 remains LLM-free by default.
- Single LLM client seam with prompt/model provenance requirements.
- Deterministic-final guardrails; verifier-agent logic is additive only.
- Numeric quality thresholds for retrieval, citation precision, and refusal accuracy.
- Explicit LLM-boundary security checkpoint with local-first model preference.
- Explicit deferral of unscheduled scaffold components from current gated scope.

### Deferred (Explicitly)
- Full semantic chunking.
- OCR pipeline for image-only PDFs.
- Segment-based incremental index merge/compaction.
- Vector database migration.
- Embedding-based semantic deduplication.
- `debug_agent.py` as a gated workflow until a post-V1 phase is defined.
- `compare_procedures.py` and `summarize_project.py` until a gated workflow depends on them.
- Final provider choice between local model runtime and approved API fallback until pre-Phase 3 architecture sign-off.

### Deferral Triggers
- Revisit incremental index merge when rebuild time is consistently above threshold.
- Revisit OCR when real scanned PDFs are present in core corpus.
- Revisit vector DB when retrieval stack adopts embedding-first serving path.
- Revisit provider choice when the local model path fails Gate 3 quality or latency thresholds.
