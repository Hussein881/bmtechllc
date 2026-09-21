# Retrieval Evaluation Results

## Test run

Date: 2026-09-08

Command:

```bash
.venv/bin/benchmark-evaluate \
  --dataset data/evaluation/golden_queries.json \
  --metrics-csv /tmp/benchmark-retrieval-evaluation.csv
```

The test used the live local PostgreSQL/pgvector corpus and the reviewed
30-question golden dataset: 10 lookup, 10 multi-chunk, and 10 unanswerable
questions. The aggregate retrieval metrics exclude unanswerable questions,
because Recall@5 and MRR are undefined when no relevant chunk exists.

## Question types

A **lookup** question has one specific chunk that contains its answer. It tests
whether the system can find a single fact. For example, “What does
non-volatile mean as a data warehouse characteristic?” has one expected chunk:
the chunk defining non-volatility. A lookup question scores Recall@5 of 1.0
when that chunk is in the first five results, or 0.0 when it is absent.

A **multi-chunk** question needs two or more distinct chunks to answer
completely. It tests whether retrieval finds all evidence required for a
comparison or synthesis. For example, “How does cycle time differ from work
time?” requires the separate chunks defining cycle time and work time. Its
Recall@5 is the fraction of expected chunks found in the first five results, so
finding one of two produces 0.5.

**MRR** applies to both question types. It measures the rank of the first
relevant chunk, rewarding systems that put useful evidence nearer the top even
when a multi-chunk answer still needs additional retrieved evidence.

## Results

| Measure | Result |
| --- | ---: |
| Relevant-query Recall@5 | 0.95 |
| Relevant-query MRR | 0.86 |
| Lookup Recall@5 | 1.00 |
| Multi-chunk Recall@5 | 0.90 |
| Median retrieval time | 201 ms |
| p95 retrieval time | 644 ms |
| Slowest retrieval | 3.0 s |

The first query was the 3.0-second outlier. Two of the 30 requests exceeded
500 ms; the other retrievals were generally near the 200 ms median. Retrieval
time includes query embedding and both database retrieval paths, so it is an
end-to-end measure for the current retrieval system.

## What worked well

- All 10 lookup questions returned their expected chunk in the top five. Nine
  of those chunks ranked first.
- Eight of 10 multi-chunk questions returned every expected chunk in the top
  five.
- A concise FTS-only query worked as expected. For example,
  `benchmark-search --mode fts --query "attack formula"` returned the Attack
  Formula chunk first.

These results show that the current vector retrieval is a strong baseline for
finding facts that are present in the corpus, especially for focused lookup
questions.

## Gaps exposed by the test

### Incomplete multi-chunk coverage

Two multi-chunk questions returned only one of their two expected chunks:

- The storage-versus-management question returned the storage chunk but missed
  the management chunk.
- The scope-errors-versus-framing-components question returned the scope-errors
  chunk but missed the framing-components chunk.

Several other questions found the correct content below rank one. This explains
the 0.86 MRR despite the high Recall@5.

### Hybrid search did not gain from FTS in this run

Every evaluated result had a single-arm RRF score and a vector-similarity score.
This means FTS contributed no candidates to these natural-language queries, so
the nominal hybrid path behaved as vector-only for this test.

The likely cause is query formulation: PostgreSQL FTS works well for compact
keywords, but the current long, natural-language questions add terms that are
not present in a single chunk. The current `websearch_to_tsquery` path then has
no full-text match. This is an observed behavior from this evaluation, not a
claim that FTS is unavailable; the compact `attack formula` query returned the
expected result.

### No abstention for out-of-corpus requests

Each of the 10 unanswerable questions still received five retrieved chunks.
The system has no relevance threshold or explicit `no_relevant_information`
response, so it cannot yet safely distinguish a nearest semantic neighbor from
useful evidence.

## Recommended next steps

1. Normalize or shorten the FTS version of a natural-language query so it uses
   meaningful terms rather than every word in the question.
2. Add and calibrate a no-result decision policy using the unanswerable portion
   of the golden dataset.
3. Add a reranker or broaden candidate/context handling for multi-chunk
   questions, then repeat this evaluation.
4. Compare vector-only and hybrid metrics after query normalization to verify
   that FTS improves Recall@5 and MRR rather than merely adding complexity.

This is one evaluated corpus and one reviewed golden set, not a general
production-quality guarantee. Re-run the evaluation after meaningful changes to
the corpus, chunking, embedding model, or retrieval behavior.
