---
title: Discovery Summary Template
description: The structure for the Discovery Summary document that closes a discovery phase, capturing findings, tensions between stakeholders, and their implications for the build.
tags: [template, discovery, delivery]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 6
order: 10
related: [stakeholder-interviews]
---

# Discovery Summary Template

Copy the structure below at the end of a discovery phase. This is the document
both parties sign off on before any architecture decision is made.

Keep it to two pages. If it runs longer, the findings are not yet synthesized.

## Structure

### 1. Problem statement

One paragraph, in the client's vocabulary, restating what we are solving. If
this differs from the SOW's framing, say so explicitly and explain why.

### 2. What we found

Group findings by the four assessment areas. For each, state the finding, the
evidence, and the severity.

| Area | Finding | Evidence | Severity |
|---|---|---|---|
| Data infrastructure | | | High / Medium / Low |
| Workflow fit | | | |
| Stakeholder alignment | | | |
| Organizational capability | | | |

### 3. Tensions

Where stakeholders contradicted each other. These are design decisions or risks,
not noise — surfacing them is the highest-value part of this document.

For each tension: who holds which position, what is actually at stake, and what
we recommend.

### 4. Implications for the build

What the findings mean for scope, sequencing, and architecture. Be specific
about what we are now *not* going to do, and why.

### 5. Open questions

What we could not resolve during discovery, who owns resolving it, and by when.

### 6. Recommendation

One of three, stated plainly:

- **Proceed as scoped.**
- **Proceed with modifications** — enumerate them.
- **Do not proceed** — explain what would need to change first.

> [!NOTE]
> The recommendation section is not optional and must not hedge. A discovery
> phase that ends without a clear recommendation has not concluded.
