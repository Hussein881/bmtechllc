---
title: Tokenization and cl100k_base
description: Tokenization basics, OpenAI's cl100k_base vocabulary, its key advantages, and 100k token efficiency tradeoffs.
owner: fa
updated: '2026-09-01'
tags:
  - rag
  - llm
  - machine-learning
  - reference
status: published
visibility: internal
reviewCycleMonths: 6
order: 50
related: []
---

## 1. What is Tokenization?

Computers cannot process raw words or sentences directly. Before an AI model can process text, the text must be chopped into smaller pieces called **tokens**. Each token is then assigned a specific numeric identification number.

A token is not always a full word:
* Short, common words are usually **one single token**.
* Longer or complex words get chopped into **sub-word tokens**.
* Spaces, code indents, and punctuation marks also count as distinct tokens.

---

## 2. What is `cl100k_base`?

`cl100k_base` is the official Byte-Pair Encoding (BPE) token dictionary and splitting rulebook created by OpenAI. It is the default tokenizer used for **GPT-3.5-Turbo**, **GPT-4**, **GPT-4o**, and modern **embedding models** like `text-embedding-3`.

* **"100k"** represents its vocabulary size: it contains roughly **100,000 unique sub-word tokens**.

Compared to older tokenizers that held only ~50,000 tokens, `cl100k_base` compresses sentences into **15% to 20% fewer total tokens on average**.

---

## 3. Why Was 100,000 Chosen as the Default Size?

Designing a tokenizer vocabulary size ($|V|$) involves a direct tradeoff between processing speed and computer memory footprint:

* **The Small Dictionary Problem (~5,000 Tokens):** Text gets split into tiny character fragments, making token sequences very long ($N$). Because AI processing workload grows quadratically ($\mathcal{O}(N^2)$) with sequence length, long token streams slow down system execution.
* **The Large Dictionary Problem (~500,000 Tokens):** The AI requires a massive lookup table in GPU memory (VRAM). The computer wastes memory holding thousands of rare words that are seldom used.
* **The 100,000 "Sweet Spot":** A 100,000-token dictionary balances sequence compression with memory overhead, keeping token counts low while fitting within hardware RAM constraints.

---

## 4. Key Advantages of `cl100k_base`

* **Higher Context Efficiency:** Splitting text into fewer total tokens allows longer documents to fit inside an AI model's memory window.
* **Improved Multilingual Support:** Older tokenizers fragmented non-English scripts (e.g., Arabic, Cyrillic, CJK characters) into single-byte pieces. `cl100k_base` includes explicit sub-words for non-Latin scripts, reducing non-English processing costs.
* **Clean Code & Whitespace Handling:** Repeated spaces, tabs, and common programming syntax are treated as single tokens, improving efficiency for software code.
* **Dedicated Control Tokens:** Specific token IDs (starting around ID `100257`) are reserved for system signals like `<|endoftext|>`, preventing user text from being confused with background structural instructions.
