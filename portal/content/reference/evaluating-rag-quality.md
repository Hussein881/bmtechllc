---
title: Evaluating RAG Quality — What Actually Matters
description: A practical framework for evaluating retrieval-augmented generation systems beyond basic accuracy metrics, covering retrieval quality, answer faithfulness, and the failure modes that matter most for business applications.
tags: [rag, llm, ai-strategy, reference]
status: published
visibility: shareable
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 10
related: [glossary, ai-readiness-assessment]
---

Most teams building RAG systems measure the wrong things first. They check whether the system produces correct answers on their test set, ship it, and discover the real failure modes in production. This article is a framework for evaluating what actually matters — written from the perspective of someone who has debugged production RAG failures.

## The three layers of RAG quality

A RAG system has two distinct jobs: *retrieval* (finding the right documents) and *generation* (producing a correct answer from those documents). Quality problems in each layer look different and require different fixes. There is also a third layer — *system behavior* — that neither pure retrieval nor pure generation metrics capture.

### Layer 1 — Retrieval quality

Retrieval fails in two directions:

**Low recall:** The right document exists but the retrieval step doesn't return it. Causes include poor chunking (the relevant sentence is split across chunks), mismatch between query phrasing and document phrasing (semantic search doesn't solve this as reliably as people expect), and metadata filtering that over-constrains the result set.

**Low precision:** The retrieval step returns documents, but they're not relevant to the query. This causes the generation layer to either hallucinate an answer (if the model is too confident) or correctly decline to answer (if it's calibrated) — but in both cases, the user gets a bad experience.

**How to measure it:**
Build a retrieval evaluation set: 50–100 queries where you know which document(s) contain the answer. Measure recall@k (did the right document appear in the top k results?) and MRR (where did it rank?). Do this before you have a generation layer at all — retrieval problems are cheaper to fix early.

### Layer 2 — Answer faithfulness

Given that the right documents were retrieved, does the model's answer accurately reflect what those documents say? This is the hallucination question, and it's the hardest layer to evaluate automatically.

Faithfulness failures are insidious because they often look correct. The model generates a fluent, confident answer that cites a real document but misrepresents what that document says — eliding a caveat, inverting a condition, or synthesizing two unrelated passages into a claim neither supports.

**How to measure it:**
Human evaluation on a stratified sample remains the most reliable method. Automated faithfulness metrics (G-Eval, RAGAS, Trulens) are useful for catching obvious failures and tracking regressions, but they have high false negative rates on subtle misrepresentations. Use them for screening, not certification.

### Layer 3 — System behavior

Beyond individual query quality, a production RAG system needs to behave correctly as a system:

- **Appropriate refusal:** When no retrieved document answers the question, does the system say so clearly, or does it confabulate? The threshold for refusal is a product decision, not a technical one — set it explicitly.
- **Consistency:** Does the same question asked in different phrasings get the same answer? Inconsistency erodes trust fast.
- **Latency distribution:** Not just average latency but p95 and p99. Users remember the slow queries.
- **Source citation accuracy:** Do the cited sources actually support the answer? Citation hallucination — citing a real document that doesn't support the claim — is a specific failure mode that requires its own test set.

## What to skip in v1

**Don't build a comprehensive automated evaluation harness before you have real users.** Test sets built in a vacuum miss the long tail of real queries. Build a minimal retrieval eval set, ship to a limited audience, collect real failure cases, and build your evaluation harness around those.

**Don't optimize embedding models before fixing chunking.** Chunking strategy is the highest-leverage lever in most early RAG systems, and it's underrated because it's boring. A well-chunked document with a mediocre embedding model outperforms a poorly-chunked document with a state-of-the-art embedding model.

## The question that matters

The evaluation question that cuts through everything else: *For the queries your actual users will ask, in the conditions your actual users will ask them, does the system produce answers you're willing to put your name on?*

That's the test. Everything else is scaffolding to help you answer it reliably.
