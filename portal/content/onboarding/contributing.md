---
title: Contributing to the Knowledge Base
description: How to add or change a page in this knowledge base, what the frontmatter contract requires, and which checks run before a change can merge.
tags: [onboarding, process, tooling]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 6
order: 10
related: [0001-internal-only-knowledge-base]
---

# Contributing to the Knowledge Base

Adding a topic never requires an application change. Create a Markdown file in
the right folder and it becomes a page, appears in navigation, and enters the
search index automatically.

## Add a page

Create a `.md` file under the section it belongs to:

```
content/
├── onboarding/    the path a new person walks, in order
├── methodology/   how we work and why
├── playbooks/     how to execute a phase of an engagement
├── runbooks/      operational procedures and incident response
├── reference/     lookups: glossary, standards, checklists
├── templates/     artifacts you copy from at the start of work
├── decisions/     ADRs, so we stop relitigating settled questions
└── engagements/   per-client notes, retros, what actually happened
```

Folders nest one level deep for grouping — `playbooks/discovery/` renders a
"Discovery" group in the sidebar.

## Required frontmatter

```yaml
---
title: Stakeholder Interview Playbook
description: One sentence that summarizes the page. Minimum 20 characters.
tags: [discovery, playbook]
status: draft            # draft | published | archived
visibility: internal     # internal | shareable
owner: ah
updated: 2026-07-28
reviewCycleMonths: 6
order: 20
related: [engagement-model]
---
```

The build fails on a missing `description`, an unknown `owner`, or a tag outside
the controlled vocabulary in `src/content.config.ts`. Adding a tag is a one-line
change to that file — cheap, but deliberate, so the vocabulary does not rot into
near-duplicates like `rag` / `RAG` / `retrieval`.

## Writing rules

These exist because pages are the retrieval unit for our internal tooling, not
because of style preference:

1. **One page, one concept.** Target 300–1,500 words. Split beyond that.
2. **Never skip heading levels.** H2 to H4 is a lint error. Headings are chunk
   boundaries.
3. **Write self-contained sections.** A section retrieved on its own should make
   sense. Write "The discovery phase requires…" not "This phase requires…".
4. **Tables for enumerable facts, prose for reasoning.**
5. **No meaning carried only by an image.** Diagrams get a text summary.

> [!NOTE]
> Drafts are visible to the team by design. Ship a `status: draft` page early
> rather than sitting on a perfect one — the banner tells readers to treat it as
> unverified.

## Before you merge

```bash
npm run build
```

This runs the full gate: frontmatter schema validation, internal link checking,
redirect resolution, `index.json` completeness, and ownership verification.
Pages past their review cycle produce a warning, not a failure.

## Renaming a page

Add the old path to `redirects.json`. CI verifies every redirect destination
resolves to a real page, so a rename without a redirect fails the build.
