# Gate 6 Readiness Packet

Generated at: 2026-07-05T05:58:31.956486+00:00

## Summary
- Gate 6 ready: yes
- Open carried conditions count: 0
- Index strategy recommendation: keep_full_rebuild_strategy
- Recommendation reason: within_warning_thresholds

## Quality Snapshot
- QA refusal accuracy (%): 100.0
- How-To run error rate (%): 0.0
- Planner gate-ready flag: True
- Baseline quality metrics present: True

## Curation Governance Snapshot
- Spot-audit disagreement rate (%): 100.0
- Accepted decision events: 1
- Rollback events: 1

## Observability Snapshot
- Corpus total chunks: 4308
- Index build stage_total_ms: None
- Triggered by time threshold: False
- Triggered by size threshold: False
- Full rebuild warning ms: 120000.0
- Full rebuild warning chunks: 50000

## How-To Eval Provenance
- Trials per case: 5
- Dataset path: data/eval/howto_eval_cases_golden.json
- Review status: reviewed
- Gate eligible: True
- Hash match: True

## Interface Parity
- Checked: False
- Status: not_requested
- Health endpoint OK: False
- Readiness key parity: False

## Source Artifacts
- qa_report: data/eval/report_latest.json
- howto_report: data/eval/howto_report_latest.json
- plan_report: data/eval/plan_report_latest.json
- curation_report: data/eval/curation_report_latest.json
- corpus_quality_report: data/eval/corpus_quality_report_latest.json
- llm_report: data/eval/llm_report_latest.json

## Reviewer Sign-Off
- Gate: Gate 6 (Evaluation + Interface)
- Reviewer:
- Date:
- Quality verdict: pass | conditional | fail
- Performance verdict: pass | conditional | fail
- Decision: approved | approved-with-conditions | rejected
- Conditions:
- Notes:
