---
title: Stakeholder Interview Playbook
description: A step-by-step guide for conducting stakeholder interviews during the discovery phase of an AI consulting engagement, including question frameworks, facilitation techniques, and synthesis methods.
tags: [discovery, client-comms, playbook]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 6
order: 10
related: [engagement-model, ai-readiness-assessment]
---

Stakeholder interviews are the highest-leverage activity in the discovery phase. Done well, they surface the real problem (rarely identical to the stated problem), reveal organizational constraints that will determine what is actually buildable, and create the alignment that makes delivery possible.

Done poorly, they produce a collection of quotes that confirm whatever hypothesis you walked in with.

## When to run this playbook

Run stakeholder interviews during:
- AI Readiness Assessments (mandatory, with all three stakeholder types)
- Discovery phases of build engagements (mandatory before architecture decisions)
- Scope change evaluations involving major new areas

## Stakeholder types and focus areas

### Executive sponsor

**Goal:** Understand what success looks like at the level that matters for the engagement to be considered a win.

Key questions:
- What specific outcome would make this engagement worth the investment, in your words?
- What does failure look like, and what would cause it?
- What decisions will be made differently if this system works as intended?
- What other initiatives is this adjacent to, and how does it need to connect?
- What is the timeline pressure, and where does it come from?

> [!NOTE]
> Executive sponsors often frame problems in terms of desired outcomes ("we want to reduce time to answer customer questions") rather than technical requirements. This is valuable — capture the framing precisely, including their vocabulary. The technical requirements come later.

### Operational owner

**Goal:** Understand the day-to-day reality of the process the AI system will touch.

Key questions:
- Walk me through what actually happens in a typical [relevant workflow] from start to finish.
- Where do things slow down or break down?
- What workarounds have people built, and why?
- What would make your day measurably better?
- What are you afraid might go wrong with an AI system here?

> [!NOTE]
> The operational owner usually knows the most important constraints — the ones that don't appear in any documentation. Give them time to tell you about the exceptions and edge cases. That's where the real requirements live.

### Technical lead

**Goal:** Understand the infrastructure and constraints that bound what is feasible.

Key questions:
- What does the data look like that this system would need — where does it live, what format, how fresh?
- What integrations are required, and what do those systems look like on the inside?
- What security and compliance requirements apply?
- What deployment constraints exist (cloud vs. on-prem, approved tooling, etc.)?
- What does your team's capacity look like to support this after delivery?

## Interview structure

Each interview is 45–60 minutes:

| Segment | Duration | Purpose |
|---|---|---|
| Context-setting | 5 min | Explain the project, your role, how the interview will be used |
| Open exploration | 20–25 min | Open-ended questions; listen more than you talk |
| Focused probing | 15–20 min | Drill into the two or three most important threads |
| Constraints and concerns | 5–10 min | Explicitly ask what could go wrong; surface risk |
| Close | 3–5 min | Who else should you talk to? Any questions for you? |

## Synthesis process

After interviews, synthesize before sharing findings:

1. **Transcript review:** Note every distinct claim, constraint, concern, and desired outcome — one per note.
2. **Affinity grouping:** Cluster notes into themes across respondents.
3. **Tension identification:** Flag where respondents contradict each other — these are design decisions or risks, not noise.
4. **Priority ranking:** Which findings most constrain the solution space? Which most clearly define success?

The synthesis output is a **Discovery Summary** (1–2 pages) documenting findings, tensions, and implications. This is the document that both parties sign off on before architecture decisions are made.
