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

## Run document Q&A

Place UTF-8 `.txt` documents in `documents/`, then run:

```bash
python main.py --doc sample_policy.txt --question "What are the core working hours?"
```

The CLI prints a validated JSON `QAResponse`; the selected tier is written to
stderr. `usage_log.csv` records a bounded question, tokens, model, tier, and
cost for each model call.

## Run retrieval agent

```bash
python agent.py --question "What is the travel meal policy?"
python agent.py --tier flagship --question "Compare travel and reimbursement requirements."
```

The first command routes automatically and prints `[ROUTING] Selected tier: …`
before its tool trace; `--tier` is an explicit override. The agent returns a
validated `QAResponse` and uses at most five tool-calling turns followed by one
final synthesis turn.

## Tests and evaluation

```bash
python test_phase1.py
python test_phase2.py
python test_phase3.py
python eval_suite.py
```

`eval_suite.py` performs measured routed and flagship-only runs, plus a
forced-cheap complex-task stress run. It writes detailed results to
`eval_results.txt`.
