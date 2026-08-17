# Demo Runbook

1. Activate the virtual environment and confirm `.env` has a valid API key.
   For the Week 2 demo, set `DATABASE_URL` and `SEARCH_MODE=vector` in `.env`
   or `.env.local`. Start the supplied local database with `docker compose up -d`.

2. From an empty database, inspect the source corpus without writing or calling
   an API, then ingest it:

   ```bash
   .venv/bin/python -m ingest.ingest --source-dir documents --dry-run
   .venv/bin/python -m ingest.ingest --source-dir documents --create-indexes
   ```

   The first command reports chunks, tokens, and estimated embedding cost. The
   second creates the schema, embeds only new hashes, and creates the HNSW
   index. Re-run it once to demonstrate idempotency (`inserted: 0`).

3. Run the single-document CLI:

   ```bash
   python main.py --doc document.txt --question "What does this document say about the decision?"
   ```

   Point out the selected tier, validated JSON fields, grounded source quote,
   and the new CSV usage row.

4. Run a retrieval task:

   ```bash
   python agent.py --question "What decision was made in the available documents?"
   ```

   Show the `list_docs`, `search_docs`, and `read_doc` trace before the final
   `QAResponse`.

5. Toggle the retrieval control arm and repeat the same question:

   ```bash
   SEARCH_MODE=keyword python agent.py --question "What decision was made in the available documents?"
   ```

   Both modes return the same tool result shape. Vector mode logs a
   `query_embed` usage row; keyword mode does not.

6. Run a safe failure case:

   ```bash
   python agent.py --question "What does the library say about the fictional Orion allowance?"
   ```

   Confirm `confidence` is `0.0` and `source_quote` is `"N/A"`.

7. After reviewed `week2_cases.json` has been frozen from the actual corpus,
   run the Week 2 arms:

   ```bash
   .venv/bin/python eval_suite.py --suite week2 --modes routed,flagship --search vector --out week2_results/
   ```

   Open `week2_results/summary.txt` and the per-arm JSON files. Discuss runtime
   versus separate ingestion cost, classifier/query-embedding overhead, routing
   accuracy, retrieval hit-rate, cross-source retrieval, and latency.

8. The retired sample-document benchmark is intentionally unavailable. Use the
   Week 2 evaluation after its reviewed real-document cases have been added.
