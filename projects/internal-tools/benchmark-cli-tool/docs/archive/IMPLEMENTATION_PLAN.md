You are an expert Python developer building a command-line tool.

Follow the implementation plan below to generate a complete, production-ready implementation. 

Requirements for your output:
1. Generate the complete source code for every file mentioned in the plan (`config.py`, `logger.py`, `schema.py`, `router.py`, `tools.py`, `agent.py`, `main.py`, `requirements.txt`, `.env`).
2. Do not use placeholders, `# TODO` comments, or truncated snippets. Write out all functions and logic in full.
3. Use strict typing (`pydantic`, Python 3.11 type hints) and robust error handling as outlined in the plan.

Here is the implementation plan:

# Implementation Plan: Centralized Routing Q&A CLI Tool

Build a command-line Q&A tool using Python 3.11+ and the official OpenAI Python SDK. The system routes questions between cheap and flagship model tiers, enforces structured JSON output, uses 3 retrieval tools with failure handling, logs token costs, and handles missing information gracefully.

---

## Architecture Overview

* **Environment (`venv`, `requirements.txt`, `.env`)**: Isolated virtual environment managing dependencies and API credentials.
* **Version Control (`.gitignore`, Git)**: Configured repository avoiding tracking sensitive credentials or virtual environment binaries.
* **CLI Interface (`main.py`)**: Entry point for user questions and output display.
* **LLM Core (`llm.py`)**: Single wrapper function for all OpenAI API calls. No direct SDK calls elsewhere.
* **Tier Config (`config.py`)**: Maps tier names (`cheap`, `flagship`) to exact OpenAI model identifiers, pricing rates, and environment variables.
* **Classifier (`router.py`)**: Fast classification step using the cheap tier to route queries to `cheap` or `flagship`.
* **Retrieval Tools (`tools.py`)**: Standardized tool functions (`list_docs`, `search_docs`, `read_doc`) with explicit error catching.
* **Cost Logger (`logger.py`)**: CSV logger recording tokens and calculated USD costs per call.

---

## Phase 1: Repository Initialization, Virtual Environment & Centralized LLM Wrapper

### Deliverables
* Initialized Git repository with proper `.gitignore`.
* Local Python virtual environment (`.venv`).
* `requirements.txt` and `.env` files for dependency and API key management.
* Centralized `config.py` loading `.env` variables and mapping model tiers to exact IDs and cost rates.
* Centralized `llm.py` handling all model calls and token telemetry.

### Tasks
1. **Initialize Git Repository & `.gitignore`**:
   * Initialize git repository:
     ```bash
     git init
     ```
   * Create `.gitignore`:
     ```text
     .venv/
     .env
     __pycache__/
     *.pyc
     usage_log.csv
     ```

2. **Initialize Virtual Environment & Dependencies**:
   * Create and activate Python virtual environment:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate  # On Windows: .venv\Scripts\activate
     ```
   * Create `requirements.txt`:
     ```text
     openai>=1.0.0
     pydantic>=2.0.0
     python-dotenv>=1.0.0
     ```
   * Install packages:
     ```bash
     pip install -r requirements.txt
     ```
   * Create `.env`:
     ```env
     OPENAI_API_KEY=your_openai_api_key_here
     ```

3. **Initialize Config (`config.py`)**:
   * Load environment variables via `python-dotenv`:
     ```python
     import os
     from dotenv import load_dotenv

     load_dotenv()
     OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
     ```
   * Map model tiers and pricing rates:
     * `cheap`: `"gpt-4o-mini"` (Input: $0.15 / 1M tokens, Output: $0.60 / 1M tokens)
     * `flagship`: `"gpt-4o"` (Input: $2.50 / 1M tokens, Output: $10.00 / 1M tokens)

4. **Implement LLM Wrapper (`llm.py`)**:
   * Initialize standard SDK client using key from `config.py`.
   * Implement single entry function `call_llm(tier: str, messages: list, tools: list | None = None, response_format = None) -> dict`.
   * Select model string based on `tier`.
   * Invoke `client.chat.completions.create(...)`.
   * Extract usage statistics (`prompt_tokens`, `completion_tokens`) and pass metadata to logger.
   * Return completion response object.

5. **Implement Cost Logger (`logger.py`)**:
   * Append query details to `usage_log.csv`: `timestamp`, `question`, `tier`, `model`, `prompt_tokens`, `completion_tokens`, `total_cost_usd`.

6. **Initial Git Commit**:
   * Stage and commit setup baseline:
     ```bash
     git add .gitignore requirements.txt config.py llm.py logger.py
     git commit -m "feat: initial repository setup and LLM wrapper"
     ```

---

## Phase 2: Tier Routing & Structured JSON Output

### Deliverables
* Query classifier function routing user prompts to `cheap` or `flagship`.
* Pydantic schema enforcing structured JSON outputs.

### Tasks
1. **Implement Query Classifier (`router.py`)**:
   * Function `classify_query(question: str) -> str`.
   * Send user prompt to `cheap` tier with system guidance:
     * Flag `"EASY"` for factual lookups or single-section retrievals.
     * Flag `"HARD"` for complex reasoning, synthesis across sources, or ambiguous prompts.
   * Map `"EASY"` $\rightarrow$ `"cheap"` and `"HARD"` $\rightarrow$ `"flagship"`.

2. **Define Structured Output Schema (`schema.py`)**:
   * Create Pydantic model:
     ```python
     from pydantic import BaseModel

     class QAResponse(BaseModel):
         answer: str
         confidence: float  # Range 0.0 - 1.0
         source_quote: str  # Direct quote or "N/A" if refused
     ```

3. **Enforce JSON in `llm.py`**:
   * Use OpenAI Structured Outputs (`response_format=QAResponse`) or JSON mode (`type: "json_object"`) in `call_llm`.
   * Validate that both `cheap` and `flagship` tiers format output according to schema.

---

## Phase 3: Tool Implementation & Failure Resilience

### Deliverables
* Three retrieval functions (`list_docs`, `search_docs`, `read_doc`).
* Safe wrappers preventing runtime crashes on empty searches or invalid file paths.
* Agent tool-calling execution loop in `agent.py`.

### Tasks
1. **Implement Retrieval Tools (`tools.py`)**:
   * `list_docs()`: Returns JSON metadata for files (`title`, `type`, `date`).
   * `search_docs(query: str)`: Searches document collection for `query`.
     * *Failure handling*: If no matches found, return `"No results found for query: '<query>'."`
   * `read_doc(filename: str, section: str | None = None)`: Reads specific document or section.
     * *Failure handling*: If target file is missing, return `"Error: File '<filename>' does not exist. Call list_docs() to verify available file names."`

2. **Construct OpenAI Tool Specifications**:
   * Write JSON schemas for `list_docs`, `search_docs`, and `read_doc` adhering to the OpenAI function specification format.

3. **Implement Tool Execution Loop (`agent.py`)**:
   * Accept query, determine target model tier via `classify_query`.
   * Send prompt and tools array to `call_llm`.
   * If model returns `tool_calls`:
     * Execute target tool safely in Python.
     * Append execution result to message history with `role: "tool"`.
     * Re-invoke `call_llm` until final response is produced or max iterations reached (e.g., 5).

4. **Implement Refusal Prompting Rules**:
   * Instruct model: If the answer cannot be found after using retrieval tools, set `confidence` to `0.0`, `source_quote` to `"N/A"`, and state in `answer` that the document does not contain the required information.

---

## Phase 4: CLI Interface, Test Suite & Documentation Deliverables

### Deliverables
* Command-line application entry point (`main.py`).
* 10-question evaluation run.
* Cost analysis comparing routed execution against flagship-only execution.
* Half-page performance write-up.

### Tasks
1. **Build CLI Entrypoint (`main.py`)**:
   * Accept user question argument.
   * Print selected tier and execution progress to stdout.
   * Display structured JSON output upon completion.

2. **Run 10-Question Test Suite**:
   * 5 Easy questions (simple factual lookups).
   * 5 Hard questions (synthesis/complex queries).
   * Include questions where answers are absent to test refusal mechanisms.
   * Execute suite with **Dynamic Routing** (`cheap` + `flagship`).
   * Execute suite with **Flagship Only** (`flagship` for all calls).

3. **Generate Project Write-Up (`report.md`)**:
   * **Tier Performance Comparison**: Document where `cheap` succeeded versus where tool chaining or JSON schema adherence degraded.
   * **Cost Comparison Table**: Compare token usage and total cost ($) between routed and flagship-only execution.
   * **Prompt Evolution**: Highlight prompt adjustments made to stabilize tool selection or output compliance.