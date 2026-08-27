# Corpus Quality Controls (Phase 5)

Purpose:
- Define measurable duplicate-control baselines for corpus health.
- Provide operational guidance for exact and near-duplicate remediation.

## Control 1: Exact-hash dedupe baseline
- Method: normalize chunk text (lowercase, collapsed whitespace) and compute SHA-256 hash.
- Signal: duplicate group count and duplicate chunk rate.
- Artifact: `data/eval/corpus_quality_report_latest.json` under `controls.exact_hash_dedupe`.

## Control 2: Near-duplicate strategy
- Method: source-scoped pair comparisons using text similarity ratio with a configurable threshold.
- Defaults:
  - threshold: `0.93`
  - max pairs per source: `200`
- Signal: candidate count and top near-duplicate pairs for review.
- Artifact: `data/eval/corpus_quality_report_latest.json` under `controls.near_duplicate_strategy`.

## Remediation policy
- Exact duplicates:
  - Keep one canonical chunk path and remove redundant copies at source level.
  - If duplicates are intentional references, convert repeats to short pointers.
- Near-duplicates:
  - Prioritize high similarity and high-traffic sources first.
  - Merge overlap when operational guidance is materially equivalent.
  - Keep separate chunks only when context or audience differs.

## Operational command
- `PYTHONPATH=src /opt/homebrew/bin/python3 scripts/report_corpus_quality.py --report-out data/eval/corpus_quality_report_latest.json`

## Current baseline snapshot
- Total chunks: 4308
- Exact duplicate rate: 3.459%
- Near-duplicate candidates: 19

## Last Updated
2026-07-05
