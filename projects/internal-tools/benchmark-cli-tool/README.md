# Benchmark Retrieval Pipeline

A retrieval-only RAG foundation: document ingestion, OpenAI embeddings,
PostgreSQL full-text search, vector search, Reciprocal Rank Fusion, and
retrieval-level evaluation. It intentionally does not generate answers or run
agent workflows.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d
```

The application loads the existing `.env` first, then the optional `.env.local`
without overriding values already set in `.env`. Ensure they provide
`OPENAI_API_KEY` and `DATABASE_URL`. Place source exports in `data/documents/`;
that directory is ignored by Git.

## Ingest and retrieve

```bash
benchmark-ingest --source-dir data/documents --dry-run
benchmark-ingest --source-dir data/documents --create-indexes
```

`search_docs(query, top_k=5)` embeds the query once, concurrently retrieves 20
pgvector candidates and 20 PostgreSQL FTS candidates, then merges them with
RRF (`k = 60`). It returns chunks and fused search scores only. The optional
`speaker`, `source` (source filename), and ISO-8601 `date` filters apply to
both retrieval arms.

Inspect retrieval manually with:

```bash
benchmark-search --query "home office equipment reimbursement"
benchmark-search --mode fts --query "equipment reimbursement"
benchmark-search --mode vector --query "remote work policy"
benchmark-search --query "architecture decision" --speaker Ada --date 2026-08-14
```

## Retrieval evaluation

The 30-item template at `data/evaluation/golden_queries.example.json` has 10
lookup, 10 multi-chunk, and 10 unanswerable queries. Its expected chunks are
anchored by source filename and content hash, then resolved to the current
database IDs when evaluation runs. Copy it to a private dataset path and review
any reference that becomes unavailable after source-content changes, then run:

```bash
benchmark-evaluate --dataset /path/to/golden_queries.json
benchmark-evaluate --dataset /path/to/golden_queries.json --compare-vector \
  --comparison-report /tmp/retrieval-comparison.md
pytest
```

The comparison report is a before/after table for vector-only and hybrid RRF
Recall@5/MRR. It records the deltas and whether both measures improved. The
evaluation log includes retrieval mode, latency, and quality columns.
Unanswerable queries remain in the per-query output but are excluded from the
metrics because they have no relevant chunk IDs.

## Real integration check

The default suite is offline. To verify the complete pgvector and embedding
path with the supplied Docker database, run this opt-in test after `docker
compose up -d` and configuring `OPENAI_API_KEY`:

```bash
pytest -m integration_live tests/integration/test_hybrid_pgvector.py
```

It indexes two small fixtures with real OpenAI embeddings, verifies FTS, vector,
and fused retrieval, then clears only the local Compose database's chunk table.

## Layout

```text
src/benchmark_cli/
  ingestion/       Parse, normalize, chunk, embed, index
  providers/       Embedding provider boundary
  storage/         PostgreSQL/pgvector + FTS schema and queries
  retrieval.py     Concurrent hybrid retrieval and pure RRF fusion
  evaluation/      Golden dataset loading, metrics, CLI
tests/unit/        Chunking, embeddings, RRF, and metric tests
data/evaluation/   30-query golden-dataset template
```
