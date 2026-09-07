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

Use `--force` when a supplied document has changed. It deletes the existing
chunks for each supplied source file, then re-embeds and inserts that file's
current chunks. This removes chunks deleted from an edited file, but it cannot
remove chunks for a source file that has itself been deleted or renamed: that
file is no longer supplied to the command.

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --force --create-indexes
```

Force one matching source without touching other sources:

```bash
.venv/bin/benchmark-ingest --source-dir data/documents --only 'remote_work_policy.txt' --force --create-indexes
```

### Remove stale sources or rebuild the local corpus

The current CLI has no source-manifest or `--sync`/`--prune` option. Therefore,
after deleting or renaming a source file, clear the chunk table before a full
re-ingestion if the database must exactly match `data/documents`:

```bash
docker compose exec postgres \
  psql -U benchmark -d benchmark_cli \
  -c 'TRUNCATE TABLE document_chunks RESTART IDENTITY;'

.venv/bin/benchmark-ingest --source-dir data/documents --create-indexes
```

`pgvector` is a PostgreSQL extension, not a separate database. The
`document_chunks` rows hold both the OpenAI embeddings and the source text; the
PostgreSQL `search_vector` used for full-text search is generated from that
text. As a result, this command clears vector, full-text, and chunk data
together while retaining the schema, pgvector extension, and indexes. It is
destructive and cannot be undone.

For a complete local database rebuild, including schema and indexes, remove the
Compose volume and start the service again:

```bash
docker compose down -v
docker compose up -d
.venv/bin/benchmark-ingest --source-dir data/documents --create-indexes
```

This removes all data in this project's local PostgreSQL volume, not just
retrieval chunks. Use it only when that volume contains no data you need. A
future `benchmark-ingest --sync` or `--prune` command should delete only rows
for source files no longer present, avoiding a full reset and re-embedding of
unchanged files.

## 6. Inspect retrieval manually

```bash
.venv/bin/benchmark-search --query "home office equipment reimbursement"
.venv/bin/benchmark-search --mode fts --query "equipment reimbursement"
.venv/bin/benchmark-search --mode vector --query "remote work policy"
.venv/bin/benchmark-search --top-k 10 --query "deployment rollback plan"
```

The command prints chunk IDs, source files, metadata, text, and the relevant
native or fused score as JSON.

### Read parent-section context for a hit

Search results remain precise, isolated chunks. After selecting a relevant
`chunk_id`, retrieve its surrounding source-section context with:

```bash
.venv/bin/benchmark-search --read-doc 42
```

`--read-doc` returns the hit plus adjacent chunks from the same source file and
section, ordered by source position. The default context budget is 1,200 tokens;
when a section is larger, the response marks `section_complete` as `false` and
returns a contiguous window centered on the hit. Adjust the budget when needed:

```bash
.venv/bin/benchmark-search --read-doc 42 --max-context-tokens 2000
```

## 7. Run the real integration test

```bash
.venv/bin/python -m pytest -o addopts='' -m integration_live tests/integration/test_hybrid_pgvector.py
```

The test uses real OpenAI embeddings and the local pgvector Docker database to
verify FTS retrieval, vector retrieval, and RRF fusion. It clears only its local
test chunks before and after running.

## 8. Run retrieval evaluation

Use retrieval evaluation to measure whether known-relevant chunks appear in the
first five hybrid-search results. Run it after ingesting the same document set
used to create the evaluation dataset.

### Prepare a golden dataset

Copy `data/evaluation/golden_queries.example.json` to a private, non-example
file. The example questions match the sample documents and use reviewed
`expected_chunks` references. Each reference pairs a source filename with the
SHA-256 hash of the reviewed chunk text. The evaluator resolves those durable
references to the current PostgreSQL IDs when it runs, so a truncate and
re-ingestion needs no ID update when the source text is unchanged.

If a reviewed chunk's text changes, is removed, or its source file is renamed,
evaluation stops with the missing reference rather than producing a misleading
score. Review that question and update its reference to the intended new chunk.

Include lookup and multi-chunk questions with one or more reviewed chunk
references. Keep unanswerable questions with an empty `expected_chunks` list; they are
reported individually but excluded from Recall@5 and MRR because those metrics
do not apply when no relevant chunk exists.

### Run the evaluation

```bash
.venv/bin/benchmark-evaluate \
  --dataset data/evaluation/golden_queries.json
```

The command prints JSON containing the overall Recall@5 and MRR, followed by
the retrieved chunk IDs and per-query metrics. Recall@5 measures what fraction
of each question's expected chunks appear in the top five; MRR rewards placing
the first relevant chunk nearer the top.

### Review the CSV run log

Every run appends one row per query to `artifacts/retrieval_evaluation.csv` by
default. The rows share a `run_id` and record:

- retrieval time in milliseconds, including query embedding and hybrid database retrieval;
- the returned chunk IDs plus their RRF and vector-similarity scores;
- per-query Recall@5 and the run-level Recall@5 and MRR.

`generation_time_ms` is blank by design: this is a retrieval-only system and
does not generate answers. To write the log somewhere else:

```bash
.venv/bin/benchmark-evaluate \
  --dataset data/evaluation/golden_queries.json \
  --metrics-csv /path/to/retrieval_evaluation.csv
```

## 9. Run normal checks

```bash
.venv/bin/python -m pytest
.venv/bin/python -m pytest -m unit
.venv/bin/python -m ruff check .
```
