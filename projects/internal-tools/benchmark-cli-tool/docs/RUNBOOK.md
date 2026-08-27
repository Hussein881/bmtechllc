# Retrieval Pipeline Runbook

## 1. Set up the environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

Use the existing `.env` and optional `.env.local` files. The application loads
`.env` first, then fills any unset values from `.env.local`; set
`OPENAI_API_KEY` and `DATABASE_URL` there.

All `benchmark-*` commands below are installed in `.venv/bin`. They work as
shown after `source .venv/bin/activate`; otherwise prefix them with `.venv/bin/`.

## 2. Start PostgreSQL with pgvector

```bash
docker compose up -d
docker compose ps
```

Useful Docker lifecycle commands:

```bash
docker compose logs -f postgres
docker compose down
```

## 3. Add documents

Place source files in `data/documents/`. This directory is intentionally ignored
by Git because it may contain company data.

## 4. Inspect ingestion without writes

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --dry-run
```

Limit ingestion to matching source files when needed:

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --only '*policy*.txt' --dry-run
```

## 5. Ingest and index

This command creates the schema, generates embeddings, stores chunks, creates
the PostgreSQL `tsvector` values, and creates the vector and FTS indexes.

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --create-indexes
```

Use a smaller embedding request batch only when diagnosing provider or network
issues:

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --batch-size 16 --create-indexes
```

### Incremental behavior and replacing a source

Normal ingestion is incremental by chunk-content hash: unchanged chunk text is
not embedded or inserted again. It does not remove chunks that were deleted
from, or changed within, an existing source file.

Use `--force` when the supplied documents have changed and the database should
exactly reflect their current contents. It deletes the existing chunks for each
supplied source file, then re-embeds and inserts its current chunks.

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --force --create-indexes
```

Force one matching source without touching other sources:

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --only 'remote_work_policy.txt' --force --create-indexes
```

Until source-manifest/version tracking is added, prefer `--force` for edited or
deleted documents; use normal ingestion for append-only or unchanged corpora.

## 6. Inspect retrieval manually

```bash
.venv/bin/benchmark-search --query "home office equipment reimbursement"
.venv/bin/benchmark-search --mode fts --query "equipment reimbursement"
.venv/bin/benchmark-search --mode vector --query "remote work policy"
.venv/bin/benchmark-search --top-k 10 --query "deployment rollback plan"
```

The command prints chunk IDs, source files, metadata, text, and the relevant
native or fused score as JSON.

## 7. Run the real integration test

```bash
.venv/bin/python -m pytest -o addopts='' -m integration_live tests/integration/test_hybrid_pgvector.py
```

The test uses real OpenAI embeddings and the local pgvector Docker database to
verify FTS retrieval, vector retrieval, and RRF fusion. It clears only its local
test chunks before and after running.

## 8. Run retrieval evaluation

Copy `data/evaluation/golden_queries.example.json` to a private location and
replace its placeholder `expected_chunk_ids` with reviewed database chunk IDs.

```bash
.venv/bin/benchmark-evaluate --dataset /path/to/golden_queries.json
```

The command reports Recall@5 and MRR for lookup and multi-chunk queries, plus
the retrieved chunk IDs for every query.

## 9. Run normal checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m pytest -m unit
.venv/bin/python -m ruff check .
```
