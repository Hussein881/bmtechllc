# Demo Runbook

1. Activate the virtual environment and confirm `.env` has a valid API key.
2. Run the single-document CLI:

   ```bash
   python main.py --doc sample_policy.txt --question "What are the core working hours?"
   ```

   Point out the selected tier, validated JSON fields, grounded source quote,
   and the new CSV usage row.

3. Run a retrieval task:

   ```bash
   python agent.py --question "What is the travel meal policy?"
   ```

   Show the `list_docs`, `search_docs`, and `read_doc` trace before the final
   `QAResponse`.

4. Run a safe failure case:

   ```bash
   python agent.py --question "What is the quantum relocation allowance?"
   ```

   Confirm `confidence` is `0.0` and `source_quote` is `"N/A"`.

5. Run `python eval_suite.py`, then open `eval_results.txt` and discuss the
   measured routed versus flagship-only cost comparison, forced-cheap stress
   evidence, prompt version, schema-validation count, and tool-chain results.
