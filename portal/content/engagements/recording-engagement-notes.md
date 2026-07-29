---
title: Recording Engagement Notes
description: What to capture in an engagement folder during and after a client project, and why retros are written while the work is still fresh rather than at the end.
tags: [process, delivery, retro, client-comms]
status: draft
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 3
order: 1
---

# Recording Engagement Notes

Each client engagement gets a folder under `content/engagements/`. This page
explains what goes in it.

> [!NOTE]
> Draft. The structure below is what we want; only one past engagement has been
> written up this way so far.

## Folder structure

```
content/engagements/
└── {client-slug}/
    ├── kickoff.md      what we agreed at the start
    ├── decisions.md    running log of choices and why
    └── retro.md        what actually happened
```

## Write the retro during, not after

The single most valuable habit here: append to `retro.md` as things happen,
not from memory at the end. Specifics decay fast — by the time an engagement
closes, the detail that would have been useful next time has already blurred
into "it went fine."

Add an entry whenever one of these occurs:

- An assumption from scoping turns out to be wrong
- A technical approach fails and gets replaced
- The client asks for something that reveals a gap in our discovery
- Something takes materially longer or shorter than estimated

Each entry is two or three sentences. What happened, why, what we would do
differently.

## What makes it back into the KB

At close, review `retro.md` and ask what generalizes. Findings that apply beyond
this one client belong in a playbook, runbook, or reference page — not buried in
an engagement folder nobody will reopen.

This is the loop that makes the knowledge base compound instead of accumulate.

## Confidentiality

Engagement folders contain client specifics. Nothing here is ever marked
`visibility: shareable` without explicit client agreement, and case studies for
external use get written separately in `website/` with names and numbers
scrubbed or approved.
