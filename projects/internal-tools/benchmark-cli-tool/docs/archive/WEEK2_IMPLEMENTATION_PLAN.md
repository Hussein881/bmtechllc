# Week 2 Implementation Plan: Vector RAG & Cost-Engineered Agent

**Repo:** `projects/internal-tools/benchmark-cli-tool` (git root `/home/developer/bmtechllc/git-repo/bmtechllc`, branch `fanuel`)
**Status:** Blueprint only — no implementation code. Function signatures and pseudocode illustrate contracts; the senior developer writes the bodies.

---

## Reconciliation Notes (read before Day 1)

Four things in the brief do not match the code currently on disk. Each is resolved below with an explicit assumption; raise them at Monday standup before executing.

| # | Brief says | Repo actually has | Resolution assumed by this plan |
|---|---|---|---|
| R1 | `search_docs(query: str, limit: int = 5)` is the untouchable contract | `tools.py:81` defines `search_docs(query: str)` — no `limit` | Adding `limit: int = 5` is a backward-compatible superset. The agent passes JSON args from the tool schema and never supplies `limit`, so behavior is unchanged. **The real contract is the return shape, not the signature** — see R2. |
| R2 | (not mentioned) | `agent.py:115-119` branches on `isinstance(result, list) and result` → `evidence_seen`, and `result == []` → `zero_hit_seen` | Vector mode **must** return `list[dict[str, str]]` with keys `filename`, `location`, `snippet`, and **must return `[]`** (never `None`, never an error string) on zero hits. Breaking this silently breaks the refusal safeguard at `agent.py:63-67`, which is what the 2 out-of-corpus cases test. |
| R3 | Pricing: `gpt-4o-mini` $0.15/$0.60, `gpt-4o` $2.50/$10.00 | `config.py:25-36` ships `cheap=gpt-5.6-luna` ($1.00/$6.00) and `flagship=gpt-5.6-sol` ($5.00/$30.00); `usage_log.csv` history shows `gpt-4o-mini`/`gpt-4o` | Plan targets the brief's gpt-4o family. **Consequence:** `eval_suite.total_cost()` (`eval_suite.py:185-187`) recomputes cost from live `MODEL_TIERS`, not from the logged `total_cost_usd` column — editing pricing retroactively re-prices any historical row. Mitigated by the log rotation in §1. |
| R4 | All embedding ops go through `llm.py` for cost logging | `llm.py` only wraps *chat completions*; `logger.log_usage` requires `prompt_tokens` **and** `completion_tokens` and a `ModelConfig` with an output rate | Embeddings need a new `llm.embed_texts()` path plus an `embedding` tier whose `output_cost_per_million = 0.0`. The OpenAI embeddings response has no `completion_tokens`, so `_log_completion_usage` (`llm.py:45`) cannot be reused as-is. |

**One additional finding, load-bearing for §5:** `usage_log.csv` has no column distinguishing a *classifier* call from an *agent* call from an *embedding* call. Subtracting classifier overhead — an explicit requirement — is impossible against the current schema. §1 adds a `component` column.

---

<section_1_preflight>

## Section 1 — Pre-flight: Git Hygiene & Configuration

### 1.1 Untrack `usage_log.csv` without deleting it

`usage_log.csv` is currently **tracked** (confirmed via `git ls-files`). It is a growing telemetry artifact that will churn on every eval run and will conflict on every merge. Untrack it, keep the local file.

Run from the repo root (`/home/developer/bmtechllc/git-repo/bmtechllc`):

```bash
# 0. Confirm the working tree is clean and confirm the file is genuinely tracked.
git status --porcelain
git ls-files --error-unmatch projects/internal-tools/benchmark-cli-tool/usage_log.csv

# 1. Untrack it. --cached removes it from the index ONLY; the file stays on disk.
git rm --cached projects/internal-tools/benchmark-cli-tool/usage_log.csv

# 2. Verify: the file must still exist locally, and now show as untracked.
test -f projects/internal-tools/benchmark-cli-tool/usage_log.csv && echo "LOCAL COPY INTACT"

# 3. Ignore it going forward (see 1.2 for the exact .gitignore edit), then:
git status --porcelain   # usage_log.csv should now appear in NEITHER staged nor untracked output

# 4. Commit the removal + ignore rule together.
git add projects/internal-tools/benchmark-cli-tool/.gitignore
git commit -m "chore: untrack usage_log.csv telemetry artifact"
```

**Guardrails:**
- Never `git rm` without `--cached` here — that deletes the local file.
- Do **not** run `git filter-branch`/`filter-repo` to purge history. The file contains no secrets (bounded question text, token counts, cost), and history rewriting on a shared branch is out of scope for Week 2.
- The current branch is `fanuel`, not a default branch. Do all Week 2 work on a dedicated branch off it (`week2-vector-rag`) and do not push without explicit sign-off.

### 1.2 `.gitignore` update

Current contents (note: **the file has no trailing newline** — the append must add one first, or `*.pyc` and the new rule will concatenate):

```
.venv/
.env
__pycache__/
*.pyc
```

Target contents:

```
.venv/
.env
__pycache__/
*.pyc

# Week 2: local telemetry and eval artifacts
usage_log.csv
usage_log.*.csv
eval_results.txt
phase3_results.json
week2_results/
```

**Decision required (Day 1, 10 min):** `report.md` and `eval_results.txt` are currently committed as deliverables. Keep `report.md` tracked (it is the Friday deliverable) but untrack `eval_results.txt` and `phase3_results.json` as regenerated artifacts, using the same `git rm --cached` pattern.

### 1.3 Log rotation before schema change

Because §1.5 adds a column to `usage_log.csv`, and `logger.py:47` only writes a header when the file is absent or empty, an existing file would keep the old 7-column header while new rows carry 8 fields.

```bash
cd projects/internal-tools/benchmark-cli-tool
mv usage_log.csv usage_log.week1-archive.csv   # preserve Week 1 telemetry, out of git
```

**DoD:** `usage_log.csv` absent → first Week 2 call writes the new header cleanly.

### 1.4 `config.py` update strategy

Extend, do not restructure. `ModelConfig` (`config.py:16-22`) is a frozen dataclass consumed by `logger.calculate_cost_usd` and `eval_suite.cost`; keeping its shape means no downstream edits.

Additions:

```python
# config.py — additions only; ModelConfig shape unchanged.

MODEL_TIERS = {
    "cheap":     ModelConfig(model="gpt-4o-mini", input_cost_per_million=0.15,  output_cost_per_million=0.60),
    "flagship":  ModelConfig(model="gpt-4o",      input_cost_per_million=2.50,  output_cost_per_million=10.00),
    "embedding": ModelConfig(model="text-embedding-3-small",
                             input_cost_per_million=0.02,
                             output_cost_per_million=0.00),   # embeddings emit no completion tokens
}

EMBEDDING_TIER: Final[str] = "embedding"
EMBEDDING_DIMENSIONS: Final[int] = 1536      # must equal the vector(N) in the DDL — asserted at startup
EMBEDDING_ENCODING: Final[str] = "cl100k_base"

# Chunking
CHUNK_TARGET_TOKENS: Final[int] = 400        # inside the 250–500 band
CHUNK_MAX_TOKENS: Final[int] = 500
CHUNK_MIN_TOKENS: Final[int] = 80            # below this, merge forward instead of emitting
CHUNK_OVERLAP_TOKENS: Final[int] = 50

# Retrieval
SEARCH_MODE: Final[str] = os.getenv("SEARCH_MODE", "vector")   # "vector" | "keyword"
SEARCH_MIN_SIMILARITY: Final[float] = 0.25   # tune Day 3 against the eval set; see §4.4
SEARCH_OVERFETCH_FACTOR: Final[int] = 3      # fetch limit*3, then threshold-filter, then truncate

# Database — no credentials in source
DATABASE_URL: Final[str | None] = os.getenv("DATABASE_URL")
DB_STATEMENT_TIMEOUT_MS: Final[int] = 5000
```

Rules:
- `.env` gains `DATABASE_URL` and `SEARCH_MODE`. `.env` is already gitignored — **never** inline a connection string carrying a password into `config.py`.
- `MODEL_TIERS` gains `"embedding"`. Verify `router._VALID_LABELS` (`router.py:22`) still maps only to `cheap`/`flagship` so the classifier can never select the embedding tier.
- `eval_suite.total_cost` indexes `MODEL_TIERS[row["tier"]]`; the new `"embedding"` key means embedding rows now price correctly instead of raising `KeyError`.

### 1.5 `logger.py` — add the `component` column

Required to separate classifier overhead, agent answer cost, and ingestion cost (§5.3).

```python
CSV_FIELDS = (
    "timestamp", "component", "question", "tier", "model",
    "prompt_tokens", "completion_tokens", "total_cost_usd",
)

def log_usage(*, question, tier, model_config, prompt_tokens, completion_tokens,
              component: str = "agent",           # "classifier" | "agent" | "ingest" | "query_embed"
              log_path=USAGE_LOG_PATH) -> None: ...
```

`component` defaults to `"agent"` so no existing call site breaks. `router.classify_query` and the two embedding paths pass theirs explicitly.

### 1.6 `requirements.txt`

```
openai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
psycopg[binary]>=3.1     # psycopg3; do not mix with psycopg2
pgvector>=0.2.5          # register_vector adapter for psycopg3
tiktoken>=0.7.0          # cl100k_base counting for chunk sizing and pre-flight cost estimates
```

### Definition of Done — Section 1
- [ ] `usage_log.csv` untracked, still present on disk, ignored.
- [ ] `.gitignore` updated with a trailing newline preserved.
- [ ] `python -c "import config; assert config.EMBEDDING_DIMENSIONS == 1536"` passes.
- [ ] `test_phase1.py`, `test_phase2.py`, `test_phase3.py` still pass (they must, since only additive changes were made).

</section_1_preflight>

---

<section_2_database_spec>

## Section 2 — Database Specification

### 2.1 Extension & bootstrap

Ship as `sql/001_init.sql`, applied by a small `db.py` bootstrap helper that is safe to re-run.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Requires PostgreSQL 13+ with `pgvector >= 0.5.0` (HNSW landed in 0.5.0; on <0.5.0 the index DDL below fails and you must fall back to IVFFlat).

### 2.2 `document_chunks` table

```sql
CREATE TABLE IF NOT EXISTS document_chunks (
    id              BIGSERIAL     PRIMARY KEY,
    source_file     TEXT          NOT NULL,
    chunk_index     INTEGER       NOT NULL,
    chunk_text      TEXT          NOT NULL,
    content_sha256  CHAR(64)      NOT NULL,
    token_count     INTEGER       NOT NULL,
    embedding       vector(1536)  NOT NULL,
    metadata        JSONB         NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT document_chunks_source_chunk_uniq UNIQUE (source_file, chunk_index),
    CONSTRAINT document_chunks_hash_uniq         UNIQUE (content_sha256),
    CONSTRAINT document_chunks_text_nonempty     CHECK (length(btrim(chunk_text)) > 0),
    CONSTRAINT document_chunks_tokens_sane       CHECK (token_count BETWEEN 1 AND 2000)
);
```

Column rationale:

| Column | Purpose |
|---|---|
| `content_sha256` | SHA-256 of the **normalized** chunk text (§3.1). Drives idempotency: re-running ingest on unchanged input inserts nothing. Also deduplicates identical boilerplate across files. |
| `chunk_index` | Ordinal within `source_file`. Enables neighbor expansion later and makes `(source_file, chunk_index)` a stable human-readable address for the `location` field returned to the agent. |
| `token_count` | Stored at write time so ingestion cost can be reconstructed without re-tokenizing, and so chunk-size distribution is auditable. |
| `metadata` | JSONB. See 2.3. |
| `updated_at` | Maintained by trigger below; distinguishes re-embedded chunks from first-ingest ones. |

```sql
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS document_chunks_touch ON document_chunks;
CREATE TRIGGER document_chunks_touch
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### 2.3 `metadata` JSONB contract

Not free-form. Every row carries `source_type`; the rest are per-type. Enforce in Python at write time (a Pydantic `ChunkMetadata` model in `schema.py`), not in SQL, so the shape stays greppable in one place.

```jsonc
// source_type = "discord"
{
  "source_type": "discord",
  "channel":     "#eng-platform",
  "date":        "2026-04-17",          // ISO-8601 date of the FIRST message in the chunk
  "date_end":    "2026-04-17",          // date of the LAST message; equal for same-day chunks
  "speakers":    ["alice", "bob"],      // distinct authors in chunk order
  "message_count": 14,
  "ingested_at": "2026-08-10T09:00:00Z"
}

// source_type = "transcript"
{
  "source_type": "transcript",
  "meeting":     "Weekly Platform Sync",
  "date":        "2026-04-15",
  "speakers":    ["Alice Chen", "Bob Ortiz"],
  "section":     "Q2 roadmap",          // nearest preceding heading/agenda item, else null
  "ingested_at": "2026-08-10T09:00:00Z"
}

// source_type = "policy_doc"  (the five existing documents/*.txt)
{
  "source_type": "policy_doc",
  "section":     "Travel and Expenses",  // reuse tools._section_blocks() titles
  "date":        "2026",
  "ingested_at": "2026-08-10T09:00:00Z"
}
```

`speakers` is an array so a synthesis question ("what did Alice say about X") can filter with `metadata->'speakers' ? 'alice'`.

### 2.4 Indexes

```sql
-- Primary ANN index. Cosine distance, matching the <=> operator used in §4.
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Metadata filtering (channel / date / speaker predicates).
CREATE INDEX IF NOT EXISTS document_chunks_metadata_gin
    ON document_chunks USING gin (metadata jsonb_path_ops);

-- Source-scoped lookups and the read_doc bridge (§4.6).
CREATE INDEX IF NOT EXISTS document_chunks_source_idx
    ON document_chunks (source_file, chunk_index);

-- Keyword-mode fallback (§4.5) without a second store.
CREATE INDEX IF NOT EXISTS document_chunks_text_fts
    ON document_chunks USING gin (to_tsvector('english', chunk_text));
```

**HNSW parameter reasoning.** `m=16, ef_construction=64` are pgvector's defaults and are correct for this corpus size (expected 2k–20k chunks). Do not tune them up — build time scales with `ef_construction` and there is no recall problem to solve at this scale.

**Query-time recall** is set per-session, not in the DDL:

```sql
SET hnsw.ef_search = 40;   -- must be >= LIMIT; default 40 comfortably covers limit=5..15
```

`db.py` issues this on connection setup alongside `SET statement_timeout = 5000`.

**Build order matters:** create the HNSW index **after** the initial bulk ingest, not before. Building on an empty table then inserting 10k rows is materially slower than one post-hoc build. `001_init.sql` creates the table; `002_indexes.sql` creates the HNSW index and is run by `ingest.py --create-indexes` after the first full load. All index DDL uses `IF NOT EXISTS`, so re-running is free.

### Definition of Done — Section 2
- [ ] `psql -c "\d document_chunks"` shows all columns, both unique constraints, and four indexes.
- [ ] `SELECT extversion FROM pg_extension WHERE extname='vector';` returns ≥ 0.5.0.
- [ ] Inserting a 1537-dim vector raises; inserting a duplicate `content_sha256` raises.
- [ ] `db.py` connection helper registers the pgvector adapter and applies both `SET`s.

</section_2_database_spec>

---

<section_3_ingestion_spec>

## Section 3 — Ingestion Specification

### 3.1 Cleaning pipeline

Three source families, one normalization tail. Implement as `ingest/clean.py` with one parser per family, each returning a common `RawUnit` stream.

```python
@dataclass(frozen=True)
class RawUnit:
    """One atomic, indivisible source unit — never split across chunks."""
    text: str
    speaker: str | None
    timestamp: datetime | None
    ordinal: int
    extra: dict[str, Any]      # channel, section, meeting …

def parse_discord(path: Path)    -> Iterator[RawUnit]: ...
def parse_transcript(path: Path) -> Iterator[RawUnit]: ...
def parse_policy_doc(path: Path) -> Iterator[RawUnit]: ...
```

**Discord exports** (JSON from DiscordChatExporter, or TXT fallback). Drop, in order:

1. Messages whose author has `isBot: true`, or whose author name matches `/(bot|webhook|github|ci|jenkins|dependabot)$/i`.
2. System messages — `type` not in `{Default, Reply}` (joins, pins, boosts, channel renames).
3. Messages whose content, after stripping mentions/emoji/attachment markers, is empty — reaction-only or attachment-only messages.
4. Content shorter than 3 characters after normalization (`+1`, `ok`, `👍`).
5. Bare URL-only messages with no surrounding prose.

Then rewrite, do not delete: `<@123456789>` → `@display_name` (resolve from the export's user table; unresolvable → `@user`), `<#987654>` → `#channel-name`, custom emoji `<:shipit:123>` → `:shipit:`. Preserve code fences verbatim — they carry the technical content these questions will target.

Keep a per-message `speaker` and `timestamp`. Attach `reply_to` in `extra` when present; thread replies stay adjacent to their parent during chunking.

**Meeting transcripts** (JSON with segments, or TXT with `Speaker: text` lines):

1. Strip timestamp gutters — `[00:14:32]`, `00:14:32.123 -->`, `(14:32)`.
2. Collapse consecutive segments from the same speaker into one unit (transcription tools fragment on pauses).
3. Drop filler-only segments (`um`, `uh`, `[inaudible]`, `[crosstalk]`, `[silence]`).
4. Do **not** strip disfluencies inside otherwise substantive sentences — aggressive cleaning here changes meaning and costs more than it saves.
5. Capture the nearest preceding agenda heading into `extra["section"]`.

**Existing `documents/*.txt`** — reuse `tools._section_blocks()` (`tools.py:43`) so DB section titles are byte-identical to what `read_doc(filename, section)` accepts. This is what keeps the `list_docs → search_docs → read_doc` chain (asserted in `eval_suite.py:149-161`) working after the swap.

**Shared normalization tail**, applied to every `RawUnit.text`:
- Unicode NFKC; smart quotes → ASCII; strip zero-width and BOM characters.
- Collapse 3+ blank lines → 1; collapse runs of spaces/tabs → single space (except inside code fences).
- `rstrip()` every line; drop lines that are only punctuation or box-drawing characters.
- **Redaction pass:** regex-scrub anything matching an API-key, bearer-token, private-key header, or `password=` pattern **before** it is sent to the embeddings API. This is real company data leaving the machine — it is the one non-negotiable step in the pipeline.

`content_sha256` is computed on this normalized text, so cosmetic whitespace changes in the source do not cause re-embedding.

### 3.2 Token-aware chunking

```python
def chunk_units(units: Sequence[RawUnit], *, target=400, hard_max=500,
                min_tokens=80, overlap=50) -> list[Chunk]: ...
```

Algorithm — greedy accumulate on natural boundaries:

1. Count tokens with `tiktoken.get_encoding("cl100k_base")` (the encoder for `text-embedding-3-small`).
2. Walk units in order, accumulating into a buffer.
3. **A `RawUnit` is never split** — one Discord message, one merged speaker turn, one paragraph is atomic.
4. Emit the buffer when adding the next unit would exceed `hard_max` (500).
5. If the buffer is below `min_tokens` (80) at emit time, keep accumulating instead — except at end-of-file, where a short tail is merged into the previous chunk.
6. **Overlap:** seed the next buffer with the trailing whole units of the emitted chunk totaling ≤ 50 tokens. Whole units only — never a partial sentence.
7. **Hard boundary breaks** that force an emit regardless of buffer size (these prevent semantically incoherent chunks):
   - Discord: a time gap > 30 minutes between consecutive messages, or a channel change.
   - Transcript: an agenda-section change.
   - Policy docs: a section-block boundary from `_section_blocks()`.
8. **Oversize single unit** (one message/turn > 500 tokens): split on paragraph → sentence boundaries as a last resort, tag `metadata.split_unit = true`, and log it. A code fence longer than `hard_max` is emitted whole and over-length; note it rather than shredding it.

Each chunk is prefixed at embed time — **not** stored in `chunk_text` — with a compact context header, which materially improves retrieval on conversational data:

```
[#eng-platform · 2026-04-17 · alice, bob]
<chunk_text>
```

Store `chunk_text` clean so the snippet the agent sees is not polluted; the header lives only in the embedded string. Record `embed_prefix` in metadata so the transform is reproducible.

### 3.3 `ingest.py` design

```
python ingest.py [--source-dir DIR] [--only PATTERN] [--dry-run]
                 [--force] [--batch-size 128] [--create-indexes]
```

Flow:

```
main()
 ├─ discover(source_dir)                  → [Path]
 ├─ for each path:
 │    ├─ units   = parse_by_type(path)    → clean, redact, normalize
 │    ├─ chunks  = chunk_units(units)     → text + metadata + sha256 + token_count
 │    ├─ novel   = filter_existing(chunks)   ← SELECT content_sha256 WHERE ... = ANY(%s)
 │    ├─ if --dry-run: report counts + estimated cost, STOP (no API calls)
 │    ├─ vectors = llm.embed_texts([prefixed(c) for c in batches_of(novel, 128)])
 │    └─ upsert(chunks, vectors)          ← one transaction per file
 └─ summarize()   → files, chunks new/skipped, tokens, USD, wall-clock
```

**Batching.** 128 inputs per embeddings request. Two hard ceilings to respect: ~300k tokens per request and 2048 inputs per request — at 400 tokens/chunk, 128 × 400 ≈ 51k tokens, comfortably inside both. Retry with exponential backoff on 429/5xx (3 attempts, 1s/2s/4s); on a batch that still fails, halve the batch and retry once before failing the file. Never silently drop a batch.

**Embedding calls go through `llm.py`** (constraint 3). New function:

```python
# llm.py
def embed_texts(texts: Sequence[str], *, component: str = "ingest") -> list[list[float]]:
    """Embed via the configured embedding tier, logging token usage to usage_log.csv.

    Uses the same module-private _get_client(). The embeddings response reports
    usage.prompt_tokens / usage.total_tokens and NO completion_tokens, so this
    calls logger.log_usage(..., completion_tokens=0, component=component)
    directly rather than reusing _log_completion_usage (llm.py:45), which
    dereferences usage.completion_tokens.

    Asserts len(vector) == config.EMBEDDING_DIMENSIONS on the first vector and
    raises loudly on mismatch — a dimension drift must fail at ingest, not at
    INSERT time.
    """
```

The `question` column for ingest rows is set to `ingest:<source_file>` (bounded, no document text) so ingestion rows are attributable per file without leaking corpus content into telemetry.

**Idempotency.** Two layers:

```sql
INSERT INTO document_chunks
    (source_file, chunk_index, chunk_text, content_sha256, token_count, embedding, metadata)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (content_sha256) DO NOTHING;
```

- Layer 1 — **pre-filter**: `SELECT content_sha256 FROM document_chunks WHERE content_sha256 = ANY(%s)` before embedding. This is what makes re-runs *free*, not merely safe: unchanged chunks never reach the API.
- Layer 2 — `ON CONFLICT DO NOTHING` as the race/retry backstop.
- `--force` deletes rows for the targeted `source_file` inside the same transaction, then re-inserts. Never a global truncate.
- One transaction per source file: a crash mid-run leaves whole files ingested or absent, never half.

**Dry-run is mandatory before the first real run.** It prints chunk counts and `estimated_cost = total_tokens / 1e6 × $0.02` with zero API calls. Get this number reviewed before spending.

### Definition of Done — Section 3
- [ ] `python ingest.py --dry-run` prints per-file chunk counts, token totals, and estimated USD; makes no network calls.
- [ ] Full run completes; `SELECT count(*) FROM document_chunks` matches the dry-run count.
- [ ] **Re-running `ingest.py` inserts 0 rows and appends 0 embedding rows to `usage_log.csv`.** This is the idempotency proof.
- [ ] Token distribution check: `SELECT min(token_count), avg(token_count), max(token_count) FROM document_chunks` — avg in 250–500, max ≤ 500 except logged `split_unit` rows.
- [ ] Spot-check 5 random chunks by eye: no bot noise, no timestamp gutters, no truncated mid-sentence starts, no leaked credentials.

</section_3_ingestion_spec>

---

<section_4_retrieval_spec>

## Section 4 — Retrieval Specification

### 4.1 The contract that must not move

```python
def search_docs(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Return up to `limit` relevant snippets. MUST return [] on no match."""
```

Invariants, all enforced by `test_search_contract.py` (new, Day 3):

| Invariant | Why | Enforced by |
|---|---|---|
| Returns `list[dict[str, str]]` | `agent.py:116` checks `isinstance(result, list)` | contract test |
| Keys exactly `{filename, location, snippet}` | `agent.py` serializes with `json.dumps`; the system prompt teaches the model these keys | contract test |
| **Zero hits → `[]`**, never `None`/`""`/error string | `agent.py:118` sets `zero_hit_seen` only on `result == []`; that drives the confidence-0.0 refusal at `agent.py:63-67`, which the 2 out-of-corpus cases assert | contract test + eval cases 9–10 |
| **Never raises** | `execute_tool` (`tools.py:196`) catches only `TypeError/ValueError/OSError`. A `psycopg.Error` propagates and kills the agent loop mid-conversation | contract test with DB stopped |
| `filename` is resolvable by `read_doc` | `eval_suite.py:149-161` asserts the `list_docs → search_docs → read_doc` chain | §4.6 |
| Agent code untouched | Constraint 2 | `git diff --stat agent.py` empty at end of week |

### 4.2 Internal logic flow

```
search_docs(query, limit=5)
 │
 ├─ guard: query.strip() empty → return []
 ├─ mode = os.getenv("SEARCH_MODE", config.SEARCH_MODE).lower()
 │
 ├─ if mode == "keyword"  → return _search_keyword(query, limit)     # today's tools.py:81 body, verbatim
 │
 └─ vector path, inside a broad try/except:
      ├─ qvec = llm.embed_texts([query], component="query_embed")[0]
      ├─ rows = db.similarity_search(qvec, limit * SEARCH_OVERFETCH_FACTOR)
      ├─ hits = [r for r in rows if r.similarity >= SEARCH_MIN_SIMILARITY][:limit]
      ├─ return [_to_snippet(r) for r in hits]        # [] if hits is empty — correct, not an error
      │
      └─ except (psycopg.Error, OpenAIError, RuntimeError) as exc:
           log warning to stderr (never stdout — stdout is the captured tool trace, eval_suite.py:133)
           if config.SEARCH_FALLBACK_KEYWORD:  return _search_keyword(query, limit)
           else:                                return []
```

The mode is read **per call**, not at import — tests and the eval harness flip `SEARCH_MODE` between runs in the same process.

### 4.3 SQL query pattern

```sql
SELECT
    id,
    source_file,
    chunk_index,
    chunk_text,
    metadata,
    1 - (embedding <=> %(qvec)s::vector) AS similarity
FROM document_chunks
ORDER BY embedding <=> %(qvec)s::vector
LIMIT %(k)s;
```

Notes the developer must not get wrong:

- `<=>` is **cosine distance** in `[0, 2]`; similarity is `1 - distance`, in `[-1, 1]`. `vector_cosine_ops` in the HNSW index must match this operator — pairing `<->` (L2) with a cosine index silently degrades to a sequential scan.
- **Do not put the similarity threshold in a `WHERE` clause.** A predicate on the computed distance prevents the HNSW index from serving the `ORDER BY ... LIMIT`. Over-fetch `limit × 3` and threshold in Python (§4.2).
- Pass the query vector as a parameter with the `pgvector` psycopg3 adapter registered — never string-interpolate 1536 floats.
- Optional metadata pre-filter (`WHERE metadata->>'source_type' = %s`) is supported but **out of scope for Week 2** — pgvector applies filters post-ANN, which can under-fill results. Note it as Week 3 work.

Result → contract mapping:

```python
{
  "filename": row.source_file,
  "location": _format_location(row),   # discord:  "#eng-platform 2026-04-17 (chunk 12)"
                                        # transcript: "Weekly Platform Sync — Q2 roadmap (chunk 3)"
                                        # policy_doc: "Travel and Expenses (chunk 1)"  ← read_doc-compatible section title
  "snippet":  row.chunk_text[:600],    # bounded; whole-word truncation with an ellipsis
}
```

`similarity` is deliberately **not** in the returned dict — adding a key changes what the agent sees and risks the model reasoning about scores instead of content. Log it to stderr for tuning instead.

### 4.4 Threshold calibration (Day 3, timeboxed to 45 min)

`SEARCH_MIN_SIMILARITY = 0.25` is a starting point, not a result. Procedure: run all 10 eval questions in vector mode with the threshold at 0.0, dump `(question, similarity, source_file)` for the top 10 of each, then pick the threshold that sits below the worst *true* positive across the 8 answerable questions and above the best *false* positive on the 2 out-of-corpus questions. If no such gap exists, the two refusal cases will fail — record that honestly in the Friday report rather than hand-tuning until the number looks good.

### 4.5 Feature flag

```bash
SEARCH_MODE=vector    # default
SEARCH_MODE=keyword   # exact current behavior, byte-identical output
```

Design rules:
- The flag lives **entirely inside `tools.search_docs`**. `agent.py`, `prompts.py`, `router.py`, and the tool JSON schema (`tools.py:154-166`) are unchanged — the agent cannot observe which strategy ran.
- Keyword mode is the **existing body, moved verbatim** into `_search_keyword`, with a `[:limit]` truncation appended. Do not "improve" it while moving it; it is the control arm of the benchmark and must stay comparable to Week 1.
- Invalid value → warn on stderr, fall back to `vector`. Never crash on a typo'd env var.
- The harness sets it via `os.environ` per mode, so a single `python eval_suite.py --compare-search` run produces both arms.

### 4.6 The `read_doc` bridge — decide on Day 3

`read_doc` (`tools.py:113`) resolves filenames against `documents/*.txt` only. Once `search_docs` returns `filename` values for Discord/transcript sources, the model will call `read_doc("eng-platform-2026-04.json")` and get `"Error: Document or section not found."`, which sets `tool_error_seen` (`agent.py:128`) and short-circuits the agent into a one-shot final turn. **This silently degrades the 3 synthesis questions.**

Three options — pick one on Day 3 and write it down:

| Option | Work | Risk |
|---|---|---|
| **A (recommended)** — write cleaned sources into `documents/` as `.txt` at ingest time, and use that filename as `source_file` | ~1h; `list_docs()` picks them up for free | Duplicates corpus on disk; `documents/` must stay gitignored for real company data |
| B — extend `read_doc` with a DB fallback keyed on `source_file` | ~2h | Touches a second tool; broader blast radius |
| C — return only the 5 existing policy filenames | trivial | Guts the Week 2 goal; not viable |

Option A also keeps `list_docs()` truthful, which matters because the eval chain check requires `list_docs` to fire first. **If Discord/transcript data is confidential, `documents/` must be added to `.gitignore` before any real file lands there** — it is currently tracked with the five sample policy docs.

### Definition of Done — Section 4
- [ ] `git diff --stat agent.py prompts.py router.py schema.py` is empty.
- [ ] `test_search_contract.py` passes: shape, keys, `[]` on zero hits, no raise with Postgres stopped.
- [ ] Same query under both `SEARCH_MODE` values returns contract-identical shapes.
- [ ] Existing `test_phase*.py` pass with `SEARCH_MODE=keyword`.
- [ ] `EXPLAIN ANALYZE` on the §4.3 query shows an `Index Scan using document_chunks_embedding_hnsw`, not a `Seq Scan`.
- [ ] `read_doc` bridge option chosen, implemented, and recorded in the report.

</section_4_retrieval_spec>

---

<section_5_evaluation_and_cost>

## Section 5 — Evaluation Harness & Cost Accounting

### 5.1 Test suite structure

New module `eval_cases_week2.py`. **Do not delete the existing 11 `EVAL_CASES`** in `eval_suite.py` — they are the Week 1 regression net. Extend the dataclass additively:

```python
@dataclass(frozen=True, slots=True)
class EvalCase:
    question: str
    category: str
    expected_tier: str
    expected_confidence: float | None = None
    requires_full_read: bool = False
    # Week 2 additions:
    expected_sources: tuple[str, ...] = ()   # source_file(s) that MUST appear in retrieval
    min_sources: int = 1                     # synthesis cases require >= 2 DISTINCT sources
```

Composition — 10 questions:

| # | Category | Count | Expectations |
|---|---|---|---|
| 1–5 | `easy-lookup` | 5 | Single fact from one chunk. `expected_tier="cheap"`, `confidence > 0.5`, `expected_sources` has 1 entry, retrieval hits it in the top 5. |
| 6–8 | `cross-source` | 3 | Requires ≥ 2 distinct `source_file`s **and** ≥ 2 distinct `source_type`s (e.g. a transcript decision + the Discord thread that implemented it). `expected_tier="flagship"`, `min_sources=2`. |
| 9–10 | `out-of-corpus` | 2 | Plausible-sounding but absent. `expected_confidence=0.0` **exactly**, asserted via the existing `refusal_safe` check (`eval_suite.py:146`). |

Authoring rules — these decide whether the benchmark means anything:
- Write all 10 **from the corpus, before** any tuning, and freeze them. Questions written after seeing retrieval output measure nothing.
- Record the ground-truth answer and its `source_file` for each of questions 1–8 in the case definition. Without ground truth, "quality" is a vibe.
- The 2 out-of-corpus questions must be *near-miss* — same domain, same vocabulary, absent fact (e.g. asking about a policy the team discussed but never adopted). Asking about the weather proves nothing.
- Questions 6–8 must be genuinely unanswerable from a single source. Verify by hand before freezing.

**Scoring is manual for correctness, automatic for everything else.** Do not use an LLM judge this week — it adds cost, variance, and a second thing to debug. The harness auto-scores: routing accuracy, retrieval hit-rate (`expected_sources ⊆ retrieved`), distinct-source count, `confidence == 0.0` on refusals, schema validity, tool-chain order. A human grades answer correctness on a 3-point scale (correct / partial / wrong) into a checked-in `grades.csv`.

### 5.2 Execution harness

Extend `eval_suite.py`, reusing `run_mode`'s telemetry-slicing trick (`eval_suite.py:179-182` — snapshot row count before, slice after). That mechanism is what makes per-mode cost attribution work; keep it.

```
python eval_suite.py --suite week2 --modes routed,flagship --search vector --out week2_results/
```

Arms:

| Arm | Routing | Search | Purpose |
|---|---|---|---|
| **A. Routed** | `classify_query` per question | vector | The proposed system |
| **B. Flagship-only** | forced `tier="flagship"`, classifier **not called** | vector | Cost/quality ceiling |
| **C. Keyword-routed** *(optional, if time)* | routed | keyword | Isolates the vector contribution from the routing contribution |

Arm B must **not** invoke `classify_query` — `run_mode(..., forced_tier="flagship")` already skips it (`eval_suite.py:128`), and this is exactly what makes the classifier-overhead subtraction in §5.3 meaningful.

Determinism and honesty controls:
- Fixed question order; no shuffling.
- Both arms run against the **same** committed DB state — no re-ingest between arms.
- One run per arm this week. Note in the report that N=1 means routing-accuracy differences under ~10% are not distinguishable from noise.
- Wall-clock latency per question recorded alongside cost — a 90% cost saving that doubles latency is a trade-off, not a win.
- Persist raw per-question records to `week2_results/*.json` so the report is regenerable without re-spending.

### 5.3 Cost accounting

Two categories that must never be summed into one headline number.

**Fixed (one-time) ingestion cost:**

```
C_ingest = (T_ingest_tokens / 1_000_000) × $0.02
```

where `T_ingest_tokens = SUM(prompt_tokens) FROM usage_log WHERE component = 'ingest'`.
Cross-check against the DB: `SELECT sum(token_count) FROM document_chunks` should be within a few percent (the difference is the embed-time context header, §3.2). A large gap means re-embedding happened — investigate before reporting.

**Per-question runtime cost, routed:**

```
C_routed(q) = C_classifier(q) + C_query_embed(q) + C_answer(q)

C_classifier(q)   = (p_c × $0.15  + o_c × $0.60 ) / 1e6      # gpt-4o-mini, component='classifier'
C_query_embed(q)  = (p_e × $0.02              ) / 1e6        # component='query_embed'; ~10–30 tokens, ≈$0.0000005
C_answer(q)       = Σ over agent turns of (p × in_rate + o × out_rate) / 1e6
```

The agent loop makes **multiple** `call_llm` calls per question (up to 5 tool iterations plus a synthesis turn, `agent.py:89-155`), so `C_answer` is a sum over rows, not one row. This is why per-mode row slicing is required and per-row math is not enough.

**Per-question runtime cost, flagship-only:**

```
C_flagship(q) = C_query_embed(q) + C_answer_flagship(q)        # no classifier term
```

**Headline metrics:**

```
Savings_abs  = Σ C_flagship(q) − Σ C_routed(q)
Savings_pct  = Savings_abs / Σ C_flagship(q) × 100

Classifier overhead      = Σ C_classifier(q)
Routing savings, net     = Savings_abs                      # already includes the overhead
Routing savings, gross   = Savings_abs + Σ C_classifier(q)  # what routing would save if classification were free
Classifier overhead as % = Σ C_classifier(q) / Σ C_routed(q) × 100
```

Report both net and gross. Gross alone overstates the win; the honest number is net.

**Amortization and breakeven** — the number leadership will actually ask for:

```
Effective cost per question at N questions:
    C_eff(N) = C_ingest / N + C̄_routed

Breakeven vs. flagship-only:
    N* = C_ingest / (C̄_flagship − C̄_routed)
```

State `N*` explicitly. If ingestion cost $0.40 and routing saves $0.004/question, `N* = 100` — ingestion pays for itself after 100 questions. That framing is the deliverable, not the raw savings percentage.

**Query volume caveat:** every `SELECT` against pgvector is free, but every question costs one embedding call. At $0.02/1M tokens and ~20 tokens per query, query embedding is ~$0.0000004 per question — real but negligible. Say so rather than omitting it, so the accounting is complete.

### 5.4 Friday report template — `report_week2.md`

```markdown
# Week 2 Cost & Quality Report
**Date:** YYYY-MM-DD · **Corpus:** N files / M chunks / T tokens · **Commit:** <sha>
**Models:** gpt-4o-mini (cheap) · gpt-4o (flagship) · text-embedding-3-small
**Run config:** SEARCH_MODE=vector · min_similarity=X · limit=5 · hnsw.ef_search=40 · 1 run per arm

## 1. Executive Summary
- Routed vs flagship-only: **$A vs $B** over 10 questions — **C% saving**.
- Quality: routed answered **X/8** correctly vs flagship-only **Y/8**; refusals held **Z/2**.
- One-time ingestion: **$D**. Breakeven at **N\*** questions.
- Recommendation: <ship / ship with caveat / do not ship> — one sentence, with the reason.

## 2. Corpus & Ingestion
| Source | Files | Chunks | Tokens | Cost |
|---|---|---|---|---|
| Discord | | | | |
| Transcripts | | | | |
| Policy docs | | | | |
| **Total** | | | | **$D** |

Chunk size: min / median / p95 / max tokens. Oversize splits: n.
Re-run idempotency verified: yes/no (rows inserted on second run: 0).

## 3. Runtime Cost
| Metric | Routed | Flagship-only | Δ |
|---|---|---|---|
| Total cost (10 q) | | | |
| Mean cost / question | | | |
| Classifier overhead | | $0.00 | |
| Query-embedding cost | | | |
| API calls | | | |
| Mean latency / question | | | |

Net saving: $__ (__%) · Gross saving before classifier overhead: $__ (__%)

## 4. Quality
| # | Question | Category | Routed tier | Retrieval hit | Routed grade | Flagship grade |
|---|---|---|---|---|---|---|
(10 rows)

- Routing accuracy: _/8 · Retrieval hit-rate @5: _/8
- Cross-source: _/3 retrieved ≥2 distinct sources
- Refusal safety: _/2 held confidence 0.0
- Schema validation failures: _
- **Cases where routing chose cheap and quality suffered:** (list, or "none")

## 5. Vector vs Keyword (if arm C ran)
Retrieval hit-rate and grades, side by side. States how much of the win is retrieval vs routing.

## 6. Failure Analysis
Every wrong or partial answer: question, what was retrieved, why it failed
(retrieval miss / chunking artifact / routing error / model error). No hand-waving.

## 7. Limitations
- N=1 per arm; differences under ~10% are not significant.
- Correctness graded by one human; no inter-rater check.
- 10 questions authored by the implementer — selection bias acknowledged.
- <any Reconciliation Note R1–R4 still unresolved>

## 8. Week 3 Candidates
Ranked, with the evidence from §6 that motivates each.
```

### Definition of Done — Section 5
- [ ] 10 questions frozen with ground truth **before** any threshold tuning.
- [ ] `python eval_suite.py --suite week2 --modes routed,flagship` runs end to end and writes `week2_results/`.
- [ ] Cost table reconciles: Σ of per-arm row costs == arm total, and `component` counts match expected call counts.
- [ ] Ingestion cost reported separately from runtime cost in every table.
- [ ] Week 1 `EVAL_CASES` still pass under `SEARCH_MODE=keyword` (no regression).
- [ ] `report_week2.md` complete including §6 and §7 — a report without failure analysis is not done.

</section_5_evaluation_and_cost>

---

<section_6_schedule>

## Section 6 — Five-Day Schedule

Assumes one senior developer full-time. Every day ends with a commit on `week2-vector-rag`.

### Day 1 (Mon) — Foundations: git hygiene, config, database

**Tasks**
1. Branch `week2-vector-rag` off `fanuel`.
2. Execute §1.1 git sequence; update `.gitignore`; rotate `usage_log.csv`.
3. **Raise Reconciliation Notes R1–R4 at standup.** R3 (pricing model mismatch) needs a decision before any cost number is credible.
4. Update `config.py` per §1.4; add `component` to `logger.py` per §1.5; update `requirements.txt`.
5. Install Postgres + pgvector locally; verify `extversion >= 0.5.0`.
6. Write `sql/001_init.sql` and `db.py` (connection helper, pgvector adapter registration, `statement_timeout`, `hnsw.ef_search`).
7. Add `llm.embed_texts()` per §3.3 with a unit test against a stubbed client — no live calls yet.

**Deliverables:** clean git state · updated `config.py`/`logger.py`/`requirements.txt` · `sql/001_init.sql` · `db.py` · `llm.embed_texts()` + test.

**DoD:** `usage_log.csv` untracked and present · `document_chunks` exists with all constraints · all three `test_phase*.py` still pass · `embed_texts` logs a row with `component='ingest'` and `tier='embedding'`.

---

### Day 2 (Tue) — Ingestion pipeline

**Tasks**
1. Obtain and inspect real Discord exports + transcripts. **Confirm the confidentiality handling for `documents/` before any real file lands there** (§4.6).
2. Build `ingest/clean.py`: three parsers → `RawUnit`, plus the shared normalization + redaction tail (§3.1).
3. Build `ingest/chunk.py` per §3.2 with unit tests on synthetic fixtures (boundary breaks, oversize unit, short tail, overlap).
4. Build `ingest.py` per §3.3: discovery, sha256 pre-filter, batching, upsert, summary.
5. Run `--dry-run`; **get the cost estimate reviewed** before spending.
6. Run the real ingest. Then `002_indexes.sql` (HNSW + GIN + FTS) via `--create-indexes`.
7. Re-run `ingest.py` to prove idempotency.

**Deliverables:** `ingest/` package · `ingest.py` · `sql/002_indexes.sql` · chunking unit tests · populated DB · recorded ingestion cost.

**DoD:** all §3 DoD boxes checked · second run inserts 0 rows and costs $0 · 5 chunks manually spot-checked clean and credential-free · `C_ingest` recorded in the report draft.

---

### Day 3 (Wed) — Retrieval swap behind the flag

**Tasks**
1. Move the current `search_docs` body verbatim into `_search_keyword`; add `[:limit]`.
2. Implement the vector path per §4.2/§4.3 with over-fetch + Python-side threshold.
3. Implement `SEARCH_MODE` per §4.5, read per call.
4. Write `test_search_contract.py` — the five invariants in §4.1, **including the DB-stopped case**.
5. Decide and implement the `read_doc` bridge (§4.6). Record the choice.
6. Calibrate `SEARCH_MIN_SIMILARITY` per §4.4, timeboxed to 45 minutes.
7. `EXPLAIN ANALYZE` the retrieval query; confirm the HNSW index is used.
8. Manual smoke: run `main.py`/`agent.py` on 3 questions in each mode; eyeball the tool traces.

**Deliverables:** updated `tools.py` (only) · `test_search_contract.py` · calibrated threshold with the evidence table · `EXPLAIN ANALYZE` output.

**DoD:** `git diff --stat agent.py prompts.py router.py schema.py` empty · all §4 DoD boxes checked · Week 1 tests pass under `SEARCH_MODE=keyword`.

---

### Day 4 (Thu) — Benchmark

**Tasks**
1. Author the 10 questions with ground truth (§5.1). **Freeze them** — commit before running anything.
2. Extend `EvalCase` with `expected_sources`/`min_sources`; create `eval_cases_week2.py`.
3. Extend `eval_suite.py`: `--suite`, `--modes`, `--search`, `--out`; add retrieval hit-rate, distinct-source count, and latency capture. Reuse the existing row-slicing telemetry mechanism.
4. Implement the §5.3 cost breakdown using the `component` column: separate ingestion, classifier, query-embedding, and answer costs.
5. Run arm A (routed) and arm B (flagship-only). Arm C (keyword) only if time remains.
6. Human-grade all 20 answers into `grades.csv`.
7. Compute `Savings_abs`, `Savings_pct`, `N*`.

**Deliverables:** frozen `eval_cases_week2.py` · extended harness · `week2_results/*.json` · `grades.csv` · computed cost tables.

**DoD:** both arms complete without errors · cost table reconciles against `usage_log.csv` row-by-row · all 10 questions graded · `N*` computed.

**Risk buffer:** if arm B blows the budget or the corpus proves too thin for cross-source questions, cut arm C first, then reduce cross-source questions to 2 — and say so in §7 of the report. Do not silently reduce scope.

---

### Day 5 (Fri) — Report, hardening, handoff

**Tasks**
1. Write `report_week2.md` from the §5.4 template. §6 Failure Analysis and §7 Limitations are **not optional**.
2. Failure analysis: for every wrong/partial answer, inspect what was retrieved and classify the cause.
3. Update `README.md` (Postgres setup, `DATABASE_URL`, `SEARCH_MODE`, ingest command) and `DEMO_RUNBOOK.md` (end-to-end demo from empty DB).
4. Full regression: all `test_phase*.py`, `test_search_contract.py`, chunking tests, plus Week 1 `EVAL_CASES` under both search modes.
5. Verify no secret, no `DATABASE_URL` with a password, and no confidential corpus content is staged: `git diff --cached` reviewed line by line.
6. Rank Week 3 candidates against the evidence in §6.
7. Commit. **Do not push or merge without explicit sign-off.**

**Deliverables:** `report_week2.md` · updated `README.md` + `DEMO_RUNBOOK.md` · green test run · Week 3 backlog.

**DoD:** report complete with failure analysis and limitations · every test green with actual output pasted into the handoff · agent files provably untouched (`git diff fanuel..HEAD -- agent.py prompts.py router.py schema.py` empty) · no credentials or client data in the diff · demo runs clean from an empty database.

---

### Cross-cutting risks

| Risk | Trigger | Mitigation |
|---|---|---|
| Corpus too thin for genuine cross-source questions | Day 2 inspection | Detect on Day 2, not Day 4. Widen the export range or reduce to 2 cross-source questions and disclose. |
| `read_doc` bridge underestimated | Day 3 | Option A is ~1h; if it slips past noon Wednesday, fall back to keyword mode for the chain-dependent cases and disclose. |
| Confidential data in `documents/` gets committed | Day 2 | Gitignore `documents/` **before** the first real file lands; review `git diff --cached` on Day 5. |
| Pricing mismatch (R3) unresolved | Day 1 | Blocks every cost number. Must be decided Monday. |
| Classifier misroutes cross-source questions to cheap | Day 4 | Expected and interesting — it is a finding, not a bug. Report it; do not tune the classifier prompt mid-benchmark. |
