# Benchmark CLI Tool

Document-grounded Q&A CLI with model routing, structured responses, local retrieval,
vector ingestion, and cost telemetry.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

The default test suite is deterministic: it uses sanitized documents in
`tests/fixtures/` and makes no API calls. Configure `OPENAI_API_KEY` in `.env`
only when you want to use a live command or test.

## Commands

Put local source exports in `data/documents/` (ignored by Git), then use:

```bash
benchmark-qa --doc policy.txt --question "What is the reimbursement limit?"
benchmark-agent --question "What decision was made in the available documents?"
benchmark-ingest --source-dir data/documents --dry-run
benchmark-ingest --source-dir data/documents --create-indexes
```

Set `DATABASE_URL` and `SEARCH_MODE=vector` in `.env` or `.env.local` for
pgvector retrieval. `SEARCH_MODE=keyword` is a deterministic local fallback.

## Tests and evaluation

```bash
pytest                         # unit + fixture-backed integration tests
pytest -m unit
pytest -m integration
pytest -m live                 # opt-in: calls OpenAI and writes artifacts/telemetry/
benchmark-eval --suite week2 --modes routed,flagship --search vector
```

Evaluation outputs and telemetry are written to `artifacts/` by default.
Reviewed evaluation cases belong at `data/eval_cases_week2.json`; real source
documents are intentionally ignored.

## Repository map

```text
src/benchmark_cli/   Application package and console entry points
  providers/         OpenAI integration
  storage/           PostgreSQL/pgvector adapter and SQL migrations
  telemetry/         Usage logging
  ingestion/         Source cleaning, chunking, and ingestion pipeline
  evaluation/        Benchmark case loading and execution
tests/               Unit, integration, live E2E tests, and tracked fixtures
data/                Local corpus and reviewed evaluation inputs
artifacts/           Ignored telemetry and generated evaluation outputs
docs/                Guides, architecture notes, assessments, and archived plans
```

See [documentation index](docs/README.md) for detailed guides and historical context.
