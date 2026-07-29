---
title: Discovery Readiness Checklist
description: The access, artifacts, and stakeholder commitments that must be in place before a discovery phase begins, so the first week is spent on findings rather than logistics.
tags: [discovery, checklist, playbook]
status: published
visibility: internal
owner: ah
updated: 2026-07-28
reviewCycleMonths: 6
order: 20
related: [stakeholder-interviews, engagement-model]
---

# Discovery Readiness Checklist

Discovery phases fail on logistics more often than on method. This checklist covers what must be in place before day one so the first week produces findings instead of access requests.

Run this during scoping, not at discovery kickoff. Items that are not resolved before the phase begins consume the phase.

## Stakeholder commitments

- [ ] Executive sponsor identified by name and confirmed available for a 60-minute interview
- [ ] Operational owner identified and their manager has approved the time commitment
- [ ] Technical lead identified with authority to describe infrastructure constraints
- [ ] A named client-side coordinator who can unblock scheduling
- [ ] All interviews scheduled before the phase starts

> [!IMPORTANT]
> An engagement where the executive sponsor cannot commit an hour is an engagement without an executive sponsor. Surface this during scoping — it is a material risk to delivery, not a scheduling inconvenience.

## Data access

- [ ] Read access granted to the data sources the intended use case requires
- [ ] Sample dataset provided, large enough to reveal quality problems (not a curated demo extract)
- [ ] Data dictionary or schema documentation supplied, or its absence documented as a finding
- [ ] Any PII, PHI, or regulated data identified with handling requirements stated in writing
- [ ] NDA and data processing agreements executed

## System access

- [ ] Credentials issued for systems that must be inspected
- [ ] VPN or network access working and tested before day one
- [ ] Named contact for access problems, with an escalation path

## Documentation

- [ ] Existing architecture diagrams collected, however outdated
- [ ] Prior vendor assessments or internal analyses on the same problem
- [ ] Any written requirements or business case already produced
- [ ] Records of previous attempts at this problem and why they stopped

> [!NOTE]
> Prior failed attempts are among the highest-value inputs available. They reveal constraints that nobody thinks to mention because everyone internal already knows them.

## Constraints stated in writing

- [ ] Deployment constraints (cloud vs. on-prem, approved vendors, regions)
- [ ] Security review requirements and their expected timeline
- [ ] Compliance regimes that apply
- [ ] Budget envelope for the follow-on build, even as a range
- [ ] Hard deadlines and where they originate

## Exit criteria

Discovery is ready to begin when every item above is either checked or explicitly
waived in writing, with the waiver's risk noted in the engagement record.

Unresolved items are not blockers by default — but each one is a documented risk
with a named owner, not a silent assumption.
