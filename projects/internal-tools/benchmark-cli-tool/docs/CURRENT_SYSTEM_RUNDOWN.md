# Current System Rundown

## What it is

This is a retrieval-only RAG foundation. It ingests documents, creates OpenAI
embeddings, stores chunks in PostgreSQL with pgvector, retrieves evidence with
keyword and vector search, and measures retrieval quality.

It does not generate answers, run agents, route requests between models, or
provide routed-versus-flagship cost accounting.

## How it works

1. Ingestion reads `.txt`, `.md`, and `.json` files from `data/documents/`.
2. It identifies policy documents, Discord exports, and meeting transcripts;
   normalizes text; preserves metadata such as section, speaker, channel,
   meeting, and dates; and redacts a limited set of credentials.
3. It chunks text with a 400-token target, 500-token maximum, 80-token
   minimum, and up to 50 tokens of overlap. Chunks do not cross meaningful
   section, channel, or meeting boundaries.
4. Each chunk is embedded with OpenAI `text-embedding-3-small` (1,536
   dimensions). PostgreSQL stores the chunk text, metadata, SHA-256 hash,
   vector, and generated full-text index.
5. `search_docs()` is the primary hybrid search API. It embeds the query once,
   retrieves 20 vector candidates and 20 PostgreSQL FTS candidates
   concurrently, applies optional provenance filters to both arms, deduplicates
   results, fuses them with Reciprocal Rank Fusion (RRF, `k = 60`), and returns
   the top five by default.
6. `hybrid_search()` remains as a backward-compatible wrapper around
   `search_docs()`. Vector-only and FTS-only modes are also available.
7. Returned chunk text is marked `untrusted: true` and wrapped in
   `<untrusted-retrieved-chunk>` delimiters. A chunk cannot close its own
   delimiter, but retrieved text must still be treated as data rather than
   instructions.
8. `read_doc()` expands a selected chunk into adjacent chunks from the same
   source and section, within a default 1,200-token context budget.

## Commands

### Set up and start PostgreSQL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d
```

### Ingest documents

```bash
benchmark-ingest --source-dir data/documents --dry-run
benchmark-ingest --source-dir data/documents --create-indexes
benchmark-ingest --source-dir data/documents --only '*policy*.txt'
benchmark-ingest --source-dir data/documents --force --create-indexes
```

`--force` replaces chunks for the supplied files. Deleted or renamed source
files are not automatically pruned.

### Search

```bash
benchmark-search --query "equipment reimbursement"
benchmark-search --mode fts --query "equipment reimbursement"
benchmark-search --mode vector --query "remote work policy"

benchmark-search --query "architecture decision" --speaker Ada
benchmark-search --query "deployment plan" --source meeting.txt
benchmark-search --query "release decision" --date 2026-08-14
```

`--source` matches a source filename. `--speaker` matches a stored speaker, and
`--date` accepts an ISO-8601 date (`YYYY-MM-DD`).

### Read surrounding context

```bash
benchmark-search --read-doc 42
benchmark-search --read-doc 42 --max-context-tokens 2000
```

### Evaluate retrieval

```bash
benchmark-evaluate --dataset data/evaluation/golden_queries.json
```

Compare vector-only to hybrid RRF and write a Markdown report:

```bash
benchmark-evaluate \
  --dataset data/evaluation/golden_queries.json \
  --compare-vector \
  --comparison-report /tmp/retrieval-comparison.md
```

### Run checks

```bash
python -m pytest
python -m ruff check .
```

Run the opt-in live integration test with the local database and real
embeddings:

```bash
python -m pytest -o addopts='' -m integration_live tests/integration/test_hybrid_pgvector.py
```

## Evaluation and logging

The golden dataset has 30 reviewed questions:

- 10 lookup questions
- 10 multi-chunk questions
- 10 unanswerable questions

Expected chunks use source filename plus chunk SHA-256 rather than database IDs,
so labels survive re-ingestion when the reviewed source content is unchanged.

The evaluator reports:

- **Recall@5**: the fraction of expected chunks returned in the first five.
- **MRR**: how highly the first relevant chunk ranks.

Rows are appended to `artifacts/retrieval_evaluation.csv`, with retrieval mode,
latency, returned chunk IDs, RRF/vector scores, per-query Recall@5, and
run-level Recall@5/MRR. Compatible older evaluation logs are migrated before new
rows are appended.

The current live comparison is a tie:

| Retrieval mode | Recall@5 | MRR |
| --- | ---: | ---: |
| Vector-only | 0.950 | 0.860 |
| Hybrid RRF | 0.950 | 0.860 |

Hybrid retrieval is implemented and measured, but it has not yet shown a
quality improvement on this golden set.

## Current limitations

- No answer generation, chat orchestration, router, or flagship model.
- No relevance threshold or explicit no-result response.
- No query rewriting, decomposition, or reranker.
- FTS uses English text search; multilingual corpora need additional work.
- Credential redaction is limited and is not full PII/DLP protection.
- No automatic source synchronization or pruning.
- Long policy-style sections may not always produce ideal parent-context
  boundaries.

For more detail, see the [runbook](RUNBOOK.md),
[system overview](SYSTEM_OVERVIEW.md), [system flow](SYSTEM_FLOW.md), and
[system design](SYSTEM_DESIGN.md).
