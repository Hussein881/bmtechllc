---
title: Runbooks
description: The exact steps for a recurring operation — procedures that should go the same way every time, no judgment required.
tags: [runbook, process]
status: published
visibility: internal
owner: team
updated: 2026-08-09
reviewCycleMonths: 12
order: 1
---

# Runbooks

## What belongs here

**Checklists**, not judgment calls. A runbook is a fixed sequence of steps
for an operation that recurs and should be executed the same way every
single time, regardless of who's doing it.

- Kickoff sequences, incident response, recurring operational procedures
- Numbered steps someone can follow without needing prior context
- The kind of page where "it depends" would be a bug, not a feature

## What doesn't belong here

- Guidance that requires judgment or varies by situation → **Playbooks**
- The reasoning behind why the procedure exists → **Methodology** or
  **Decisions**
- A document you copy and fill in → **Templates**

A good test before writing one: could someone unfamiliar with the situation
follow this runbook correctly on their first read, with no additional
context? If the steps genuinely change depending on circumstances, it's a
playbook wearing a runbook's clothes — split it.
