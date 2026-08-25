# Tool Flow

```text
Documents folder
     ↓
Ingestion creates searchable chunks in the local database
     ↓
You ask a question
     ↓
Router uses Luna to classify it
     ├─ simple lookup → Luna ("cheap")
     └─ broader analysis → Terra ("flagship")
     ↓
Agent searches the document library
     ↓
Agent reads the relevant source document(s)
     ↓
Selected model produces a validated JSON answer
     ↓
CLI prints the answer, confidence, source quote, and routing trace
     ↓
Usage log records token cost and routing savings
```

## Entry points

- `main.py` answers a question from one named document.
- `agent.py` searches across all documents in the library and can combine information from multiple sources.

Example:

```bash
.venv/bin/python agent.py --question "What p99 retrieval latency did pgvector achieve with HNSW?"
```

The tool routes the question, searches the indexed documents, reads the best source, and returns a validated response:

```json
{
  "answer": "...",
  "confidence": 1.0,
  "source_quote": "..."
}
```

If the documents do not contain the answer, the tool responds safely with `confidence: 0.0` rather than guessing.
