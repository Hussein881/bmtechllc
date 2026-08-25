# Week 2 Cost & Quality Report

**Date:** _pending corpus ingestion_
**Corpus:** No Discord export or transcript corpus is present in this checkout.
**Models:** gpt-4o-mini (cheap), gpt-4o (flagship), text-embedding-3-small

## Status

The vector-RAG implementation is ready for ingestion and evaluation, but no
live cost, quality, or retrieval claim has been recorded. A report with
invented cross-source questions would not be credible. Complete the fields
below only after the reviewed corpus and `week2_cases.json` are frozen.

## 1. Recommendation

_Pending evidence from routed and flagship-only Week 2 arms._

## 2. Corpus & Ingestion

| Source | Files | Chunks | Tokens | Cost |
| --- | ---: | ---: | ---: | ---: |
| Discord | | | | |
| Transcripts | | | | |
| Policy documents | | | | |
| **Total** | | | | |

## 3. Cost

| Arm | Runtime cost | Classifier | Query embedding | Agent | Latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Routed | | | | | |
| Flagship-only | | | | | |

One-time ingestion cost: _. Breakeven query volume: _.

## 4. Quality

| # | Question | Category | Routed tier | Retrieval hit | Routed grade | Flagship grade |
| ---: | --- | --- | --- | --- | --- | --- |

Record routing accuracy, retrieval hit-rate at 5, cross-source retrieval,
refusal safety, schema-validation failures, and cases where cheap routing
degraded quality.

## 5. Vector vs. Keyword

Optional control-arm comparison after vector retrieval is calibrated.

## 6. Failure Analysis

For every partial or incorrect answer, classify the cause: retrieval miss,
chunking artifact, routing error, or model error.

## 7. Limitations

- One run per arm is not statistically conclusive.
- Similarity-threshold calibration and HNSW query-plan verification are pending
  a populated database.
- The current checkout lacks the source corpus needed for an honest
  cross-source evaluation.
