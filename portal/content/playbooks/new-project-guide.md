---
title: New Project Guide (Engineering)
description: Phase-by-phase engineering checklist for a new client project, from intake after contract signature through kickoff, build, and handoff, with a gate to meet before moving to the next phase.
tags: [playbook, delivery, checklist, process]
status: draft
visibility: internal
owner: ah
updated: 2026-08-17
reviewCycleMonths: 6
order: 50
related: [implementing-a-project-with-claude-code]
---

# New project guide (engineering)

Starts after the contract is signed, ends at handoff. Work the phases in order. Don't pass a gate until it's met. "Technical lead" throughout means Dante.

## 0. Intake

- [ ] Read the Statement of work end to end
- [ ] Write in one sentence what the client considers done, if you can't do this please escalate
- [ ] List unverified assumptions examples: (data exists, access is possible, volumes are real)

**Done when:** project summary and open questions posted in the project channel.

## 1. Kickoff and access

- [ ] Find the client's technical contact (the person who can grant access)
- [ ] Request data, sandboxes, keys, sample docs
- [ ] Get data constraints in writing: Personally identifiable information, whether data can go to OpenAI's API, where we deploy

**Done when:** you can run something against real or realistic client data.

## 2. Classify the project

- [ ] Pick the archetype:

| Client need | Archetype | Default approach |
|---|---|---|
| Questions over their docs/data | Q&A | RAG |
| Automate a repetitive process | Automation | Plain code, LLM steps only where judgment is needed |
| Assistant that acts in their systems | Agent | Tool-calling agent, narrow tools, human-in-the-loop first |
| Pull structure from documents | Extraction | Structured output plus validation |
| "What can AI do for us" | Assessment | Report, no build. Skip phases 3 to 8, use the assessment template |
| Doesn't need an LLM | Conventional | Say so and flag it, this may change scope |

- [ ] Check the two standing rules: anything that can be plain code is plain code, build the narrowest version that satisfies the SOW

**Done when:** archetype confirmed with the technical lead.

## 3. Feasibility spike (1 to 3 days)

- [ ] Name the riskiest assumption (usually "the model can do X reliably on their data")
- [ ] Write the ugliest script that tests exactly that
- [ ] Run 20 to 50 real examples, record failure rate and types
- [ ] If it fails, escalate now (renegotiating scope in week 1 is cheap, in week 5 it isn't)

**Gate:** spike results written up and shared, five bullets is fine.

## 4. Models

OpenAI only, tiered: cheapest tier that passes evals for high-volume simple work, mid tier for most work, frontier for hard reasoning and agent orchestration.

- [ ] Start every component on the cheapest tier, move up only when evals fail
- [ ] Check current model names and pricing at project start
- [ ] Pin models in config so a tier swap is a one-line change

**Done when:** per-component choices in the project README.

## 5. Evals before building

- [ ] Build an eval set from real client examples, 30 minimum
- [ ] Set the pass threshold with the technical lead
- [ ] Automate it: one command, prints a score
- [ ] If you can't write an eval, you don't understand the requirement yet. Go back to the client contact

**Done when:** eval script runs against the output.

## 6. Milestone plan

- [ ] Milestones of a week or less, each ending in something demoable
- [ ] First milestone is the thinnest end-to-end slice
- [ ] Write each as: what ships, verified by what

**Done when:** plan approved by technical lead.

## 7. Build loop (per milestone)

- [ ] Build the slice
- [ ] Run evals until threshold (fix prompts and retrieval before reaching for a bigger model)
- [ ] Demo to the client, log feedback
- [ ] Route anything outside the SOW to the technical lead as a scope item, not into the codebase
- [ ] Weekly status update: shipped, next, blocked

**Done when:** all milestones demoed and eval thresholds met.

## 8. Handoff

Done means the client can run it without us.

- [ ] README: setup, evals, tier swaps
- [ ] Keys transferred or hosting documented
- [ ] Known limitations written down, including failure modes from evals
- [ ] Walkthrough call with their technical contact
- [ ] Internal retro: what to reuse, what to template, what to never repeat

**Done when:** client sign-off.

## Escalate immediately when

- The spike fails or a threshold looks unreachable
- The client asks for anything outside the SOW
- Access is blocked more than 2 business days
- The SOW promises something infeasible
- A milestone will slip

Escalating early is better then escalating late.
