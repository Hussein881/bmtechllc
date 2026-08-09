---
title: Adding a Page
description: Step-by-step instructions for creating a new page in the knowledge base, choosing the right section, and getting it to build cleanly the first time.
tags: [onboarding, process, tooling]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 12
order: 10
related: [frontmatter-reference, writing-well]
---

Adding a topic never requires an application change. Create a Markdown file in
the right folder and it becomes a page, appears in navigation, and enters the
search index automatically.

## 1. Pick the section

Ask what question the page answers:

| If it answers… | Put it in |
|---|---|
| "How do I execute this phase?" (judgment required) | `playbooks/` |
| "What are the exact steps?" (same every time) | `runbooks/` |
| "What does this mean?" | `reference/` |
| "How do we work, and why?" | `methodology/` |

If two sections seem equally right, the page is probably two pages.

## 2. Create the file

```bash
# A top-level page in a section
content/runbooks/incident-response.md

# Grouped under a subfolder — renders as a "Discovery" group in the sidebar
content/playbooks/discovery/stakeholder-interviews.md
```

Use lowercase kebab-case. The filename becomes the URL, so it is a permanent
address — pick it deliberately.

Folders nest one level deep. Deeper than that and both the sidebar and the URL
become hard to read.

## 3. Write the frontmatter

Every page needs this block at the very top:

```yaml
---
title: Incident Response Runbook
description: What to do when a delivered system fails in production, including triage order, escalation path, and client communication.
tags: [runbook, delivery]
status: draft
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 3
order: 20
---
```

Every field is explained in the
[Frontmatter Reference](/bmtechllc/portal/guide/frontmatter-reference/).

> [!NOTE]
> Start with `status: draft`. Shipping an incomplete page early is better than
> sitting on it — the draft banner tells readers to verify before acting.

## 4. Write the body

Follow the conventions in [Writing Well](/bmtechllc/portal/guide/writing-well/).
The short version: one concept per page, never skip heading levels, and write
sections that make sense on their own.

## 5. Check it builds

```bash
npm run build
```

This runs every gate. The most common failures:

| Error | Fix |
|---|---|
| `description: Required` | Add a description of at least 20 characters |
| `Invalid enum value` on `tags` | The tag is not in the vocabulary — add it to `src/content.config.ts` or use an existing one |
| `unknown owner "xx"` | Add yourself to `KNOWN_OWNERS` in `scripts/check-build.mjs` |
| `Broken internal link` | A link points at a page that does not exist — check the path |

To preview while writing:

```bash
npm run dev
```

## 6. Link it up

Add `related:` entries pointing at pages a reader would want next. These are
bidirectional in effect — the target page automatically shows a
**Referenced by** entry pointing back at yours, which is how the KB stays
navigable as it grows.

```yaml
related: [engagement-model, stakeholder-interviews]
```

Use the bare filename without the extension or folder path.
