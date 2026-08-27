# Gate 5 Review Packet (Curator + Guardrails)

Date: 2026-07-05
Prepared by: GitHub Copilot

## Scope
This packet covers Phase 5 deliverables and exit criteria:
- Curator suggestions (missing/duplicate/outdated) with deterministic duplicate baseline.
- Citation and unsupported-step guardrails in output path.
- Quarantine review workflow with cadence recommendation.
- Corpus quality controls: exact-hash dedupe baseline and near-duplicate strategy.
- Triage/approval workflow with suggestions-only posture.

## Quality Evidence

### 1) Unit tests
Command:
- `PYTHONPATH=src /opt/homebrew/bin/python3 -m unittest tests.unit.test_phase5_curation_triage_workflow tests.unit.test_phase5_curation_workflow tests.unit.test_phase5_curation_eval -v`

Observed result:
- `Ran 4 tests` -> `OK`

### 2) Curation evaluation
Command:
- `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/run_curation_eval.py --report-out data/eval/curation_report_latest.json`

Observed result:
- `expected_type_match_rate_pct=100.0`
- `non_empty_proposal_rate_pct=100.0`
- `proposal_count_avg=1.0`

Artifact:
- `data/eval/curation_report_latest.json`

### 3) Triage approval enforcement + productivity metrics
Command:
- `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/triage_curation.py "project x9 postgres failover architecture" --decisions /tmp/curation_triage_decisions_productivity.json --json --output data/eval/curation_triage_latest.json`

Observed result:
- `accepted_with_human_approval_count=1`
- `approval_ratio_pct=100.0`
- `decision_latency_ms_p50=150000.0`
- `decision_latency_ms_p95=150000.0`

Artifact:
- `data/eval/curation_triage_latest.json`

### 4) Browser-path verification
Runtime:
- `http://127.0.0.1:8768`

Observed result:
- Proposal generation works for out-of-corpus entity prompt.
- Accepted decision without approval is blocked.
- Accepted decision with reviewer + approved flag passes.
- Triage summary displays approval ratio and decision latency metrics.

### 5) Rollback control verification
Command:
- `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/rollback_curation.py --decision-id fdd8fb093deb010c --reviewer anwarh --reason "false positive acceptance" --triage data/eval/curation_triage_latest.json --history data/eval/curation_triage_history.jsonl`

Observed result:
- Rollback completed and updated target decision disposition from `accepted` to `deferred`.
- `rollback_summary.rolled_back=true` present in triage artifact.
- History trail contains both `triage_snapshot` and `rollback` events in `data/eval/curation_triage_history.jsonl`.

## Performance Evidence

### 1) Curation latency
Source artifact:
- `data/eval/curation_report_latest.json`

Observed metrics:
- `latency_p50_ms=263.284`
- `latency_p95_ms=278.386`

### 2) Corpus quality control baseline
Command:
- `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/report_corpus_quality.py --report-out data/eval/corpus_quality_report_latest.json`

Observed result:
- `total_chunks=4308`
- `exact_duplicate_rate_pct=3.459`
- `near_duplicate_candidate_count=19`

Artifact:
- `data/eval/corpus_quality_report_latest.json`

## Risk Summary
- Phase 5 quality metrics are strong on current eval set; broader eval cases may still reveal precision gaps for duplicate/outdated proposals.
- Corpus near-duplicate remediation is now measurable, but cleanup actions still require ongoing source-level execution.
- Gate 5 sign-off remains pending explicit human decision.

## Reviewer Sign-Off Block
- Gate: Gate 5 (Curator + Guardrails)
- Reviewer:
- Date:
- Quality verdict: pass | conditional | fail
- Performance verdict: pass | conditional | fail
- Decision: approved | approved-with-conditions | rejected
- Conditions:
- Notes:
