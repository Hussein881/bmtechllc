# Work Knowledge Agent

This folder is intentionally isolated from the IML Debug Agent implementation.

The LLM provider is selected with:

- `WKA_LLM_PROVIDER` (`watsonx` or `anthropic`)

Watson-related credential sources are reused:

- `DEBUG_AGENT_LLM_WATSONX_PROJECT_ID`
- `DEBUG_AGENT_LLM_WATSONX_URL`
- `DEBUG_AGENT_LLM_WATSONX_APIKEY_FILE`
- `DEBUG_AGENT_LLM_IAM_TOKEN_URL`
- `WKA_WATSONX_MODEL_ID`
- `WKA_WATSONX_API_VERSION`
- `WKA_WATSONX_PROMPT_VERSION`

The API key is expected in a JSON file with this shape:

```json
{"apikey": "<your_watsonx_apikey>"}
```

Default key file location (same as IML agent defaults):

- `~/.config/iml-agent/apikey.json`

Live Watsonx check:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py --json
```

Live Claude (Anthropic) check:

```bash
export WKA_LLM_PROVIDER=anthropic
export WKA_ANTHROPIC_API_KEY=<your_rotated_anthropic_key>
export WKA_ANTHROPIC_MODEL_ID=claude-3-5-sonnet-20241022
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py --json
```

Anthropic key file option (same JSON shape as Watsonx):

```json
{"apikey": "<your_anthropic_apikey>"}
```

Example with file-based secret:

```bash
export WKA_LLM_PROVIDER=anthropic
export WKA_ANTHROPIC_APIKEY_FILE=~/.config/iml-agent/anthropic_apikey.json
export WKA_ANTHROPIC_MODEL_ID=claude-3-5-sonnet-20241022
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py --json
```

If you do not want to export env vars in the shell first, you can pass overrides directly:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py \
	--project-id <watsonx_project_id> \
	--apikey-file ~/.config/iml-agent/apikey.json \
	--model-id ibm/granite-3-8b-instruct \
	--json
```

Anthropic overrides can also be passed directly:

```bash
WKA_LLM_PROVIDER=anthropic \
WKA_ANTHROPIC_API_KEY=<your_rotated_anthropic_key> \
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py \
	--anthropic-model-id claude-3-5-sonnet-20241022 \
	--json
```

Or with direct file override:

```bash
WKA_LLM_PROVIDER=anthropic \
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/check_llm.py \
	--anthropic-apikey-file ~/.config/iml-agent/anthropic_apikey.json \
	--anthropic-model-id claude-3-5-sonnet-20241022 \
	--json
```

## Phase 6 Interfaces

Unified CLI interface:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/interface_cli.py phase6-readiness \
	--run-observability \
	--report-out data/eval/phase6_readiness_latest.json \
	--markdown-out data/eval/phase6_readiness_packet.md
```

Run all eval harnesses through one interface command:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/interface_cli.py all-evals --with-observability
```

Optional local API interface:

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 scripts/interface_api.py --port 8770
```

API endpoints:
- `GET /health`
- `GET /phase6/readiness`
- `GET /phase6/readiness/packet`
- `POST /phase6/readiness/run` (body: `{"run_observability": true|false}`)
