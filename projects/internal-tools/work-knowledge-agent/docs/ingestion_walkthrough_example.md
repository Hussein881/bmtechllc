# Ingestion Walkthrough Example

This file shows a small synthetic example of how the current ingestion pipeline turns raw data into chunks, metadata, and artifacts.

## 1. Synthetic Raw Data

Imagine the following file exists at `data/raw/demo/network_runbook.md`:

```md
# Network Recovery Runbook

## Restart Interface

If the interface stops responding, restart the network service.

sudo systemctl restart NetworkManager
sudo systemctl status NetworkManager

## Validate Connectivity

Run a quick connectivity test.

ping 8.8.8.8 -c 4

Common failure:
ERROR: DNS resolution failed after restart
```

That is the raw source document. At this stage, it is just one Markdown file on disk.

## 2. Load Step

The loader reads the file as plain text.

Current code path:
- `scripts/ingest_docs.py`
- `src/work_knowledge_agent/ingestion/pipeline.py`
- `src/work_knowledge_agent/ingestion/loaders/markdown_loader.py`

Loaded result:

```text
# Network Recovery Runbook

## Restart Interface

If the interface stops responding, restart the network service.

sudo systemctl restart NetworkManager
sudo systemctl status NetworkManager

## Validate Connectivity

Run a quick connectivity test.

ping 8.8.8.8 -c 4

Common failure:
ERROR: DNS resolution failed after restart
```

## 3. Chunk Step

The chunker splits large text into smaller overlapping sections so retrieval can search focused pieces instead of one large file.

Current code path:
- `src/work_knowledge_agent/ingestion/chunking.py`

Because this synthetic example is small, it would likely become one chunk with the current defaults.

Example chunk output:

```json
[
  {
    "chunk_id": "data/raw/demo/network_runbook.md::chunk-0000",
    "content": "# Network Recovery Runbook\n\n## Restart Interface\n\nIf the interface stops responding, restart the network service.\n\nsudo systemctl restart NetworkManager\nsudo systemctl status NetworkManager\n\n## Validate Connectivity\n\nRun a quick connectivity test.\n\nping 8.8.8.8 -c 4\n\nCommon failure:\nERROR: DNS resolution failed after restart"
  }
]
```

If the file were larger, the pipeline would produce multiple chunks such as `chunk-0000`, `chunk-0001`, and so on.

## 4. Metadata Extraction Step

For each chunk, the pipeline adds structured metadata so retrieval and filtering remain reliable.

Current code path:
- `src/work_knowledge_agent/ingestion/metadata_extractor.py`

Example metadata for the chunk:

```json
{
  "source_file": "data/raw/demo/network_runbook.md",
  "section_heading": "Network Recovery Runbook",
  "project": "work_knowledge_agent",
  "machine": "unknown",
  "component": "unknown",
  "mode": "unknown",
  "doc_type": "readme",
  "date": "2026-07-03",
  "owner": "unknown",
  "tags": ["ingested", "md"],
  "confidentiality_level": "internal",
  "extracted_commands": [
    "sudo systemctl restart NetworkManager",
    "sudo systemctl status NetworkManager"
  ],
  "extracted_errors": [
    "ERROR: DNS resolution failed after restart"
  ]
}
```

What this metadata means:
- `source_file`: where the chunk came from.
- `section_heading`: the first heading found in the chunk.
- `doc_type`: inferred from file extension.
- `tags`: lightweight retrieval labels.
- `extracted_commands`: command-like lines found in the text.
- `extracted_errors`: troubleshooting/error lines found in the text.

## 5. Validation Step

After metadata is extracted, the pipeline validates that required fields exist and have the correct shape.

Examples of validation checks:
- `source_file` must exist and be a non-empty string.
- `tags` must be a list.
- `extracted_commands` must be a list.
- `extracted_errors` must be a list.

If validation fails, the file is recorded as failed instead of silently producing bad retrieval data.

## 6. Artifact Step

Artifacts are the saved outputs produced by ingestion and indexing.

### Artifact A: Chunks file

Written to:
- `data/processed/chunks.jsonl`

Example record:

```json
{"chunk_id": "data/raw/demo/network_runbook.md::chunk-0000", "content": "# Network Recovery Runbook\n\n## Restart Interface\n...", "metadata": {"source_file": "data/raw/demo/network_runbook.md", "section_heading": "Network Recovery Runbook", "project": "work_knowledge_agent", "machine": "unknown", "component": "unknown", "mode": "unknown", "doc_type": "readme", "date": "2026-07-03", "owner": "unknown", "tags": ["ingested", "md"], "confidentiality_level": "internal", "extracted_commands": ["sudo systemctl restart NetworkManager", "sudo systemctl status NetworkManager"], "extracted_errors": ["ERROR: DNS resolution failed after restart"]}}
```

### Artifact B: Metadata file

Written to:
- `data/processed/metadata.parquet`

Important note:
- In the current bootstrap implementation, this file contains line-delimited JSON content even though the filename ends with `.parquet`.

Example record:

```json
{"chunk_id": "data/raw/demo/network_runbook.md::chunk-0000", "source_file": "data/raw/demo/network_runbook.md", "section_heading": "Network Recovery Runbook", "project": "work_knowledge_agent", "machine": "unknown", "component": "unknown", "mode": "unknown", "doc_type": "readme", "date": "2026-07-03", "owner": "unknown", "tags": ["ingested", "md"], "confidentiality_level": "internal", "extracted_commands": ["sudo systemctl restart NetworkManager", "sudo systemctl status NetworkManager"], "extracted_errors": ["ERROR: DNS resolution failed after restart"]}
```

### Artifact C: Retrieval indexes

After ingestion, `scripts/build_indexes.py` reads the chunk artifact and writes:
- `data/indexes/keyword/index.json`
- `data/indexes/vector/index.json`

These indexes are what the future retrieval system will search.

## 7. End-to-End Flow Summary

```text
raw markdown file
-> loader reads file into text
-> chunker splits text into smaller pieces
-> metadata extractor adds structured labels
-> validator checks schema correctness
-> pipeline writes chunk + metadata artifacts
-> index builder creates keyword and vector retrieval artifacts
```

## 8. Simple Mental Model

- Raw data: the original document.
- Chunk: a smaller piece of that document.
- Metadata: the structured label attached to that piece.
- Artifact: the saved output file produced by processing.

## Last Updated
2026-07-03
