---
title: Writing Well
description: Authoring conventions for knowledge base pages — scope, structure, heading discipline, and the self-containment rule that makes pages useful to both readers and retrieval tooling.
tags: [process, reference, onboarding]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 30
related: [adding-a-page, frontmatter-reference]
---

These conventions are not style preferences. Each one exists because a page here
is read two ways: by a teammate scanning for an answer, and by our own retrieval
tooling pulling a section out of context. Both readers need the same things.

## One page, one concept

Target 300–1,500 words. Beyond that, split.

A page is the unit people bookmark, link to, and retrieve. An omnibus page
covering four topics can only be found by whichever topic you happened to put in
the title, and it can only be updated by someone willing to read all of it.

The test: if the `description` needs an "and," you have two pages.

## Never skip heading levels

H2 to H4 is a lint error. Headings are chunk boundaries — skipping a level tells
a parser the document is more deeply nested than it is, and produces chunks
scoped to the wrong parent.

```markdown
## What we assess          ← H2
### Data infrastructure    ← H3, correct
#### Access requirements   ← H4, correct
```

Use headings generously. A wall of prose under one heading is one enormous chunk;
the same content under four headings is four retrievable answers.

## Write self-contained sections

A section pulled out on its own must still make sense. This means naming the
subject rather than referring back to it.

**Avoid:**
> This phase requires three stakeholder interviews before it can conclude.

**Write:**
> The discovery phase requires three stakeholder interviews before it can conclude.

The cost is a little repetition. The benefit is that every section survives being
read in isolation — which is exactly what happens in a search result, a linked
anchor, or a retrieval result.

## Tables for facts, prose for reasoning

Anything enumerable — options, steps with owners, comparisons, thresholds —
belongs in a table. Tables scan quickly and parse cleanly.

Reasoning belongs in prose. Deeply nested bullets do neither job well: they are
harder to scan than a table and lose the logical connectives that make an
argument followable.

| Use | For |
|---|---|
| Table | Enumerable facts, comparisons, step-owner-timing |
| Prose | Reasoning, tradeoffs, why something is the way it is |
| Bullets | Short unordered lists, 3–7 items, one level deep |

## Never carry meaning only in an image

Every diagram gets a text summary nearby. That text is also your alt text.

Images are invisible to search, invisible to retrieval, and invisible to anyone
reading on a bad connection. If the diagram is the only place a constraint is
recorded, that constraint is effectively unwritten.

## Use callouts sparingly

```markdown
> [!NOTE]
> Supporting context that is genuinely easy to miss.

> [!WARNING]
> Something that will cause real damage if ignored.

> [!TIP]
> A shortcut that is not obvious.
```

Three per page is plenty. Callouts work by contrast — a page where everything is
highlighted has nothing highlighted.

## Link deliberately

Inline links are fine for passing references. For pages a reader genuinely needs
next, use `related` frontmatter instead: it renders a Related block, and it
creates a backlink on the target page automatically.

Inline links are one-directional and invisible to the target. Frontmatter
relations are machine-readable graph edges.

## Write the reasoning down

The most valuable thing in this KB is not what we do — it is why. Anyone can
reconstruct a procedure by watching someone follow it. Nobody can reconstruct
the three alternatives you rejected and the constraint that killed them.

When you document a decision, record what you chose, what you did not, and what
would have to change for the answer to be different.

> [!TIP]
> If a page could have been written by someone who had never done the work, it
> is probably missing the part that makes it worth reading.
