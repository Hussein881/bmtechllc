# Benchmark CLI Tool

Document-grounded Q&A CLI with dynamic model routing, structured responses,
local retrieval tools, and per-call cost telemetry.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file containing `OPENAI_API_KEY=<your key>`.

For Week 2 vector retrieval, configure a PostgreSQL database with the
`pgvector` extension in `.env` or the ignored local override `.env.local`:

```dotenv
DATABASE_URL=postgresql://user:password@localhost:5432/benchmark_cli
SEARCH_MODE=vector
```

`SEARCH_MODE=keyword` preserves the original lexical retrieval path for
comparison or a safe local fallback. Never commit `.env` or real company
exports.

## Run document Q&A

Place UTF-8 `.txt` documents in `documents/`, then run:

```bash
python main.py --doc document.txt --question "What does this document say about the decision?"
```

The CLI prints a validated JSON `QAResponse`; the selected tier is written to
stderr. `usage_log.csv` records a bounded question, tokens, model, tier, and
cost for each model call.

## Run retrieval agent

```bash
python agent.py --question "What decision was made in the available documents?"
python agent.py --tier flagship --question "Compare the decisions described across the available documents."
```

The first command routes automatically and prints `[ROUTING] Selected tier: …`
before its tool trace; `--tier` is an explicit override. The agent returns a
validated `QAResponse` and uses at most five tool-calling turns followed by one
final synthesis turn.

## Ingest a vector corpus

The pipeline accepts UTF-8 policy text, Discord JSON/TXT exports, and
transcript JSON/TXT exports. It redacts common credentials before API calls,
chunks at source boundaries, and records embedding usage separately.

```bash
# Parse/chunk and estimate cost; no API or database writes.
.venv/bin/python -m ingest.ingest --source-dir documents --dry-run

# Create the pgvector schema, embed new chunks, and create indexes.
.venv/bin/python -m ingest.ingest --source-dir documents --create-indexes
```

Vector search preserves the original `search_docs` result shape and falls back
to keyword search if the embedding service or database is unavailable.

## Tests and evaluation

```bash
python test_phase1.py
python test_phase2.py
python test_phase3.py
.venv/bin/python -m unittest -v test_embeddings test_chunking test_search_contract
```

After genuine Discord and transcript sources are ingested, freeze a reviewed
`week2_cases.json` (ground truth and source expectations included), then run:

```bash
.venv/bin/python eval_suite.py --suite week2 --modes routed,flagship --search vector --out week2_results/
```

The harness writes raw per-arm JSON plus component-level cost, latency,
routing, and retrieval metrics. It refuses to fabricate a Week 2 benchmark
when the reviewed corpus cases are absent.
