# Performance and Quality Scorecard

Purpose:
- Define the performance and quality metrics used for phase-gate decisions.
- Standardize human-in-the-loop sign-off before phase transitions.

## 1) Measurement Principles
- Always report both quality and performance for gate review.
- Use the same representative dataset/profile when comparing runs.
- Report p50 and p95 for latency metrics when possible.
- Record caveats and known limitations explicitly.
- Keep gate eval datasets frozen while implementation changes are underway.
- Separate frozen `golden` evals used for gate decisions from `exploratory` evals used for local tuning.
- For non-deterministic model paths, report repeated-trial distributions, not a single run only.
- Verify frozen golden evals against a checked-in integrity manifest before running gate packets.
- Surface golden review status explicitly in reports so an unreviewed answer key cannot masquerade as approved gate evidence.

## 2) Core Metrics

### Quality Metrics
- Retrieval hit rate (top-k source match).
- Citation precision (factual claims with valid citation / total factual claims).
- Citation guardrail pass rate (presence + grounding + command/code evidence match).
- Unsupported-step rate.
- Refusal accuracy on unanswerable prompts.
- Grounded-step precision for generated procedures.
- Planner actionability rubric score.
- Hallucination rate.
- Procedure completeness score (How-To phase onward).
- Plan actionability score (Planner phase onward).
- Curator expected-type match rate (Phase 5 onward).
- Curator approval ratio and triage latency p50/p95 (Phase 5 onward).
- Exact duplicate rate and near-duplicate candidate count (Phase 5 onward).

### Performance Metrics
- Ingestion stage timings (discovery, manifest, ingestion, artifact_write, total).
- Index build stage timings (load, keyword, vector, write, total).
- Retrieval latency p50 and p95.
- End-to-end Q&A latency p50 and p95.
- End-to-end How-To latency p50 and p95.
- End-to-end Planner latency p50 and p95.
- End-to-end Curator workflow latency p50 and p95.
- Reviewer decision latency p50 and p95 for triage operations.
- Model-call latency/token telemetry when an LLM path exists.
- Error rate by workflow stage.

## 3) Gate-Oriented Human Test Packet
For every gate, prepare and present:
- Quality evidence:
  - command/test outputs,
  - sampled outputs and citation checks,
  - failures and remediation status.
  - frozen golden eval report path,
  - repeated-trial summary for generative workflows.
- Performance evidence:
  - measured values,
  - comparison to target,
  - regression delta from last accepted gate run.
- Risk summary:
  - open risks,
  - severity,
  - impact if accepted.

## 4) Minimum Human Sign-Off Template
Record this in `project_memory/04_EXECUTION.md`:
- Gate:
- Reviewer:
- Date:
- Quality verdict: pass | conditional | fail
- Performance verdict: pass | conditional | fail
- Decision: approved | approved-with-conditions | rejected
- Conditions (if any):
- Notes:

## 5) Current Target Baselines
These map to the implementation plan and should be tuned after benchmark learning:
- Retrieval source hit rate / recall@5 >= 80%.
- Citation precision >= 95%.
- Refusal accuracy >= 90%.
- Grounded-step precision >= 95%.
- Planner actionability mean rubric >= 4.0/5.0.
- Curator expected-type match rate >= 90% on fixed eval set.
- Curator non-empty proposal rate >= 90% on fixed eval set.
- Reviewer approval ratio and disposition mix must be reported for every gate packet.
- Reviewer decision latency p95 <= 5 minutes for sampled review workflows.
- Rollback success rate should be 100% on tested rollback scenarios before Gate 5 sign-off.
- Exact duplicate rate trend should be non-increasing across successive corpus quality reports.
- P50 retrieval latency < 1.5s (local benchmark corpus).
- P95 end-to-end Q&A latency < 6s (excluding model cold start).
- P95 How-To latency < 12s on approved model path.
- P95 Planner latency < 12s on approved model path.
- P95 Curator workflow latency < 2s on current local corpus baseline.
- Incremental ingest unchanged corpus should skip processing work after discovery.
- Full index rebuild warning threshold: sustained rebuild time > 2 minutes or corpus > 50k chunks.

## 6) Suggested Evidence Commands
- Gate 0 startup check:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 -m work_knowledge_agent.main`
- Gate 1 ingestion/index checks:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/ingest_docs.py --raw-dir data/raw --chunks-output data/processed/chunks.jsonl --metadata-output data/processed/metadata.parquet --quarantine-output data/processed/quarantine.jsonl --manifest-path data/processed/manifest.sqlite`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/build_indexes.py --chunks data/processed/chunks.jsonl --keyword-dir data/indexes/keyword --vector-dir data/indexes/vector`
- Gate 2 retrieval/QA checks:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 -m unittest tests.unit.test_phase2_qa_workflow tests.unit.test_citation_guardrail -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/run_eval.py --eval-questions data/eval/eval_questions.json --expected-sources data/eval/expected_sources.json --chunks data/processed/chunks.jsonl --metadata data/processed/metadata.parquet --keyword-index data/indexes/keyword/index.json --vector-index data/indexes/vector/index.json --report-out data/eval/report_latest.json`
- Gate 3 how-to checks:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 -m unittest tests.unit.test_phase3_howto_eval tests.unit.test_phase3_howto_workflow tests.unit.test_llm_client tests.unit.test_llm_eval tests.unit.test_llm_boundary_guardrail -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/run_howto_eval.py --eval-cases data/eval/howto_eval_cases_golden.json --trials 5 --report-out data/eval/howto_report_latest.json`
- Gate 5 curation checks:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 -m unittest tests.unit.test_phase5_curation_workflow tests.unit.test_phase5_curation_eval tests.unit.test_phase5_curation_triage_workflow -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/run_curation_eval.py --report-out data/eval/curation_report_latest.json`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/report_corpus_quality.py --report-out data/eval/corpus_quality_report_latest.json`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/rollback_curation.py --decision-id <id> --reviewer <name> --reason <reason> --triage data/eval/curation_triage_latest.json --history data/eval/curation_triage_history.jsonl`
- Gate 6 readiness aggregation:
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/run_phase6_readiness.py --run-observability --report-out data/eval/phase6_readiness_latest.json --markdown-out data/eval/phase6_readiness_packet.md`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/interface_cli.py all-evals --with-observability`
  - `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/interface_api.py --port 8770` (optional API-path smoke check)

## 7) Governance Rule
No gate is considered complete until a human reviewer has signed off quality and performance together.
