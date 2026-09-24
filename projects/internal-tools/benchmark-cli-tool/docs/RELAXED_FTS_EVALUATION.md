# Relaxed Search Evaluation

## What we tested

The system searches lecture-note chunks in two ways:

- **Keyword search** looks for words from the question.
- **Vector search** looks for text with a similar meaning.

We tested a more forgiving version of keyword search. Normally, every
important word in a question must appear in the same chunk. In the test,
matching any one of those words was enough for a chunk to be considered. In
PostgreSQL, this changes the parsed keyword query from `&` (and) to `|` (or).

The more forgiving search did not improve the reviewed 30-question golden-set
result. It still found the same amount of required material, but placed some
correct results lower in the list. For that reason, the change was not kept.

| Mode | Recall@5 | MRR |
| --- | ---: | ---: |
| Vector-only baseline | 0.950 | 0.860 |
| Relaxed keyword + vector search | 0.950 | 0.842 |
| Change | +0.000 | -0.018 |

**Recall@5** means “did the first five results include the material we needed?”
**MRR** measures how close to the top the first useful result appears. Higher
is better for both measures.

We also tried a strict-first version: use the normal keyword search first, and
only use the more forgiving search if normal search found fewer than five
chunks. It produced the same scores. Normal keyword search was usually too
strict for full-sentence questions, so the fallback was used often enough to
have the same downside.

## Why normal keyword search often finds little

Questions written in ordinary language often mention several ideas that appear
in different parts of the notes. For example:

> How do storage and management stages differ in the data life cycle?

Normal keyword search requires all of the remaining important words to appear
in one chunk. The notes may have one useful chunk about storage and another
about management, while neither contains every word in the sentence. As a
result, keyword search can find little or nothing even though the notes contain
the answer.

## Why forgiving keyword search can lower result quality

The forgiving search treats the same question more like this:

> storage OR management OR stage OR data OR life OR cycle OR differ

PostgreSQL automatically removes common words such as “the” and “in.” However,
many broad course words remain. A chunk that merely mentions `data`,
`management`, or `cycle` can now be included even when it does not answer the
question.

PostgreSQL ranks these keyword matches partly by how often the words appear and
how close they are together. This is useful for literal word matching, but it
does not understand whether the chunk actually answers the question. A chunk
that repeats broad words can therefore rank above a shorter, more useful one.

The system then combines the keyword and meaning-based result lists using
**Reciprocal Rank Fusion (RRF)**. RRF gives credit for where an item appears in
each list, rather than how confident each search method is. This means a weak
keyword match near the top of the keyword list can still move ahead of a better
meaning-based match.

This explains the scores: the needed chunks were still often in the top five,
so Recall@5 stayed the same. But some moved lower, so MRR fell. Questions that
need information from more than one chunk are especially difficult: adding
more broad keyword matches does not reliably find the second needed passage.

## What to check next

Before trying another forgiving-keyword change, record the following for every
test question:

- how many chunks normal keyword search found;
- how many chunks forgiving keyword search found;
- which query words each forgiving result matched; and
- where each result ranked before and after the lists were combined.

This will show whether the main problem is overly strict matching, overly broad
matching, or the way RRF combines the results. A future test could require a
forgiving result to match at least two distinctive words before adding it,
instead of adding it just because normal keyword search found too few chunks.
