# BMTech — Website Design Brief

**Status:** Design brief only. No implementation.
**Version:** 1.0 — 2026-07-27
**Owner:** BMTech (client) · Design/build team (agency)

---

## 0. How to read this document

This brief defines *what* the BMTech website must be and *why*, based on evidence from a
research pass over 23 comparable small AI consultancies. It is prescriptive about structure,
conversion mechanics, visual system, and honesty constraints. It is deliberately **not** a
component library, a Figma spec, or code.

### 0.1 Source inputs

| Input | What it gave us |
|---|---|
| `outputs/ai_consultancy_success_research_brief.md` | Ranked competitive set, evidence scoring, client archetypes |
| `.firecrawl/homes/mission_automate.md` (rank 1) | Third-party review widget, hard numbers block, partner badges, free 15-min call |
| `.firecrawl/homes/sharp_hue.md` (rank 2) | Problem-first hero, "start with one task" entry offer, anti-bloat positioning |
| `.firecrawl/homes/elevate.md` (rank 3) | Service taxonomy, logo wall, FAQ/TL;DR blocks, 30–90 day ROI framing |
| `.firecrawl/homes/applied_ai_co.md` (rank 4) | Named-practitioner authority, audience proof, offer ladder (audit → train → build) |
| `.firecrawl/homes/ai_army.md` (rank 5) | Four-phase process transparency, free product as top-of-funnel |
| `.firecrawl/cases/*` (Elevate, Mission, Sharp Hue, Loophole, Agents Dynamic, Building AI, Agency AI) | Case-study anatomy, metric formats, guarantee language, pricing transparency |

### 0.2 Critical assumption — flag before build

**There is no BMTech source material in this repository.** No brand assets, client list,
service catalogue, pricing, team bios, or delivery history were available. Every BMTech-specific
fact in this brief is therefore written as a **typed placeholder** (see §11.4), not as an
assertion. Before any page is built, BMTech must complete the **Proof Intake** (§11.5).

If the Proof Intake comes back thin — for example, no named clients and no completed
engagements — the site does **not** get padded with invented numbers. It gets built on the
"credible newcomer" pattern in §11.6 instead. That is a design decision, not a fallback.

Open questions requiring a BMTech answer are collected in §13.

---

## 1. What the evidence actually says

Five findings from the research set drive nearly every decision below.

1. **Independent proof outranks volume of claims.** The two top-scored firms (Mission Automate,
   Sharp Hue) won on verified Clutch reviews and two decades of operating history. Firms
   publishing bigger numbers with no corroboration (White Glove Labs: "50+ enterprise clients,
   95% success, 40% ROI improvement" with zero named clients) scored *lower* than firms with
   modest, named, verifiable outcomes. Unverifiable maximalism is a negative signal to informed
   buyers, and the research treated it as one.

2. **Named beats numeric.** "Anne Bradfield, CEO of Analog Plant Rentals — ~15 hours/month back,
   avoided a $2,500/mo hire" (Loophole) carries more weight than "$1M saved" floating free.
   Summit West's anonymous "$1.2M annual savings" was explicitly discounted as illustrative.

3. **Narrow entry offers convert.** Sharp Hue: "Start with one task. We mean it." Building AI
   Agents: "One success metric. Agreed before we build." Mission Automate: a $0, 15-minute call
   priced on the page. The winners sell a small, legible first step — not a transformation.

4. **Process transparency substitutes for scale.** AI ARMY publishes four named phases through
   to "Handoff & Transfer… without long-term dependency." Agency AI publishes real price bands
   (£2,500–£5,000 for a single-process automation; £500/mo support, month-to-month). Both make
   a small firm feel safe to buy from.

5. **Interactive assets are the differentiating top-of-funnel.** Mission Automate runs an "AI
   Readiness Scan." AI ARMY offers a free Agent Hub. Applied AI Co leads with an "Agentic
   Readiness Audit." Almost nobody in this set has a genuinely good, honest ROI/workflow tool.
   That is the gap BMTech's interactive feature (§10) exploits.

**Design consequence:** premium here means *restraint and verifiability*, not gradient meshes and
big round numbers. The site should feel like it was made by people who would be embarrassed to
overstate something.

---

## 2. Target clients

### 2.1 Primary ICP — Operations-heavy mid-market (60% of site weight)

- **Firmographics:** 50–500 employees, $10M–$250M revenue, multi-site or multi-team.
- **Verticals with the strongest observed fit in the research set:** professional services
  (legal, accounting, agencies), healthcare/multi-location clinics, property management,
  logistics/field services, specialty manufacturing/distribution, financial claims and insurance ops.
- **Trigger:** headcount request they don't want to approve; a backlog they can't hire out of;
  a compliance or turnaround-time SLA slipping.
- **Diagnostic tell:** the work is repeatable, touches an inbox or a spreadsheet, and someone
  can name the hours.

### 2.2 Secondary ICP — Enterprise department sponsor (25%)

- **Who:** a VP/Director of Ops, Marketing, or Finance inside a 1,000+ person company with
  budget authority for a departmental pilot, buying ahead of central IT.
- **Trigger:** a mandate to "show AI progress this quarter" with a defensible ROI story.
- **What they need from the site:** governance, security, data-handling, and procurement
  legibility — plus something they can forward to a skeptical CFO.

### 2.3 Tertiary ICP — Tool-rich growth-stage team (15%)

- **Who:** RevOps/marketing ops at a 20–200 person company already running HubSpot, Salesforce,
  Slack, Notion, or similar, needing the connective layer.
- **Trigger:** tools that don't talk; reporting that takes a person a day a week.

### 2.4 Buying committee

| Role | Cares about | Site answer |
|---|---|---|
| Economic buyer (owner/CFO/VP) | Payback period, downside risk | ROI tool (§10), fixed-price bands, guarantee |
| Champion (ops lead/dept head) | Will this actually work on *my* mess? | Workflow patterns, case studies, process page |
| Technical gatekeeper (IT/security) | Data, access, dependency, exit | Security & Data page, handoff/ownership commitments |
| Skeptic (long-tenured operator) | "Are you replacing me?" | Human-in-the-loop stance, augmentation framing |

### 2.5 Explicit disqualifiers — state these publicly

Publishing who BMTech *won't* serve is a premium signal and a lead-quality filter. Recommended,
subject to BMTech confirmation:

- Engagements whose stated goal is headcount reduction (mirrors Elevate's public stance).
- Net-new consumer products or model training from scratch.
- Sub-$X engagements with no identified process (X = BMTech's floor; must be confirmed).
- Anything requiring regulated data BMTech is not certified to handle.

---

## 3. Positioning

### 3.1 Category

BMTech is an **AI implementation partner for operations-heavy mid-market businesses** — not an
AI training company, not a dev shop, not a strategy consultancy. Training and strategy exist as
supporting offers, never as the headline.

### 3.2 Positioning statement (internal, not for the page)

> For operations leaders who can name the work that's eating their week, BMTech builds and
> hands over the AI workflows that delete it — starting with one process, measured against one
> number agreed before we build, and owned by the client at the end.

### 3.3 The three differentiators (each must be provable, or cut)

1. **One process, one number, agreed up front.** BMTech commits in writing to a baseline, a
   target, and a test method before work starts. *(Requires BMTech to actually adopt this
   operating practice. If they won't, cut it — see §11.)*
2. **You own it, and we hand it over.** Documentation, credentials, architecture, and prompt
   assets transfer to the client. No hostage dependency, no black-box retainer.
3. **We show the arithmetic.** Every number on the site is either the client's own input
   (ROI tool), a named client's attributed outcome, or independently verifiable. Nothing else.

Differentiator 3 is unusual enough in this market to be the *brand*, not a footnote. The
research set is saturated with unsourced percentages; BMTech's competitive move is to be the
firm that refuses to publish one.

### 3.4 Competitive contrast (internal)

| Their move | BMTech's counter |
|---|---|
| Big unverified stat blocks | Named outcomes + a "how we measure" note on every metric |
| "AI transformation roadmap" | One process, in weeks, with an agreed target |
| Opaque pricing, "book a call" | Published bands and a scoped first engagement |
| Retainer dependency | Documented handover as a stated deliverable |
| Generic AI-agency aesthetic (purple gradients, orbiting nodes) | Editorial, instrument-panel restraint (§7) |

### 3.5 Offer ladder

| Tier | Offer | Price posture | Purpose |
|---|---|---|---|
| 0 | Workflow ROI Mapper (self-serve, §10) | Free, no gate to see results | Top-of-funnel, qualification, memorable asset |
| 1 | Process Teardown — 60–90 min working session, written findings | Free or nominal fixed fee | Low-risk first contact; produces a real artifact |
| 2 | One-Process Build — scoped, fixed-price, 3–6 weeks | Published band | Core wedge; the thing the site sells |
| 3 | Workflow Program — multi-process, quarterly | Published band or "from" | Expansion |
| 4 | Ongoing support & improvement | Published monthly, month-to-month | Retention without lock-in |

Every price and duration above is a **placeholder** pending BMTech confirmation. Publish real
bands or publish none — never publish invented ones.

---

## 4. Page structure

### 4.1 Sitemap

```
/                             Home
/services                     Services overview
  /services/process-automation
  /services/ai-agents
  /services/data-and-reporting
  /services/enablement          (training — secondary, deliberately)
/work                         Case studies index
  /work/[slug]                Individual case study
/roi                          Workflow ROI Mapper (interactive, §10)
/process                      How we work
/pricing                      Pricing & engagement models
/about                        Team, story, operating principles
/security                     Security, data handling & governance
/insights                     Articles / notes
  /insights/[slug]
/contact                      Book / apply
/legal/privacy, /legal/terms, /legal/accessibility
```

Ship in this order: Home → /roi → /process → /pricing → /contact → /services → /work → /security
→ /about → /insights. The ROI tool is the second-most-important page on the site and should not
be deferred to "phase 2."

### 4.2 Home — section by section

| # | Section | Job | Notes |
|---|---|---|---|
| 1 | Hero | Name the pain, name the offer, one primary CTA | Problem-first, in the buyer's language. No "empowering the future of AI." Sharp Hue's "Stop paying for ten tools that each do 30% of the job" is the register to hit. Secondary CTA: "Map your workflow cost" → /roi |
| 2 | Proof strip | Immediate credibility | Named client logos **with permission**, or third-party review widget, or certifications. If none exist: omit the strip entirely — do not use grey placeholder logos, do not use "trusted by teams like yours" |
| 3 | Problem articulation | Earn the read | Three concrete symptoms (tools not talking, skilled people doing manual work, leadership without numbers). Written as observations, not accusations |
| 4 | Interactive teaser | Pull to /roi | Live mini-widget: one input ("hours/week on X"), one output, one link to the full tool. Must work without a full page load |
| 5 | What we build | Legible offer | 3–4 workflow patterns with a one-line before→after each, not a service-name grid |
| 6 | Featured case study | Depth over breadth | One story, named client, named person, one headline metric with its measurement method visible |
| 7 | How it works | De-risk | Four phases ending in handover/ownership. Include what the client is responsible for |
| 8 | The commitment | Differentiate | One-metric guarantee, stated in exact terms including its conditions. Model the precision of Building AI Agents' version, which names the exception ("provided the agreed access, data, and business inputs remain available") |
| 9 | Pricing preview | Filter | Real bands + "what changes the price" + link to /pricing |
| 10 | Team | Humanize | Real named people, real photos, real credentials. Founder-led is an asset at this size — Applied AI Co and Building AI Agents both lead with a named practitioner |
| 11 | FAQ | Handle objections | 6–8 questions in buyer's phrasing, answered plainly, including the uncomfortable ones ("What if it doesn't work?", "Do you replace staff?") |
| 12 | Final CTA | Convert | Restate the small first step. Show what happens after they click |

### 4.3 Case study template (mandatory structure)

Derived from the strongest examples in the set (Loophole/Analog, Agents Dynamic/Echo):

1. Client identity: name, industry, size, location — **or the study doesn't publish**
2. Situation: the specific work, in the operator's words
3. Baseline: what was measured before, and how
4. What we built: named tools and systems, honestly (Loophole names Booqable → Make.com →
   Slack → Google Calendar; that specificity *is* the credibility)
5. Result: metric, measurement window, method, attributed quote from a named person
6. What we'd do differently / what didn't work — one honest paragraph. Rare in this market;
   disproportionately trust-building
7. Ownership & handover: what the client now runs themselves
8. CTA to the analogous pattern

Every case study carries a **provenance line**: who supplied the number, over what period, and
whether the client reviewed and approved the page. See §11.3.

### 4.4 Other pages — key requirements

- **/services/[x]:** each opens with the *symptom*, not the capability. Ends with the specific
  first engagement for that service and the price band.
- **/process:** phases, durations, what BMTech needs from the client (access, data, decision-maker
  time), what could go wrong and how it's handled. Include the exit/handover artifact list.
- **/pricing:** real bands, what moves price up or down, what's included, what isn't, payment
  terms, contract length. If BMTech won't publish numbers, publish the *method* (fixed-price
  after teardown, no hourly, no change-order surprises) — but recognize that Agency AI's
  transparency was scored as a genuine advantage.
- **/security:** data residency, model providers used, whether client data trains anything
  (state plainly), access scoping, subprocessor list, retention, deletion, incident contact.
  This page unblocks the enterprise-department ICP and is routinely absent among competitors.
- **/about:** operating principles as commitments, not adjectives. Include the disqualifier list
  from §2.5.

---

## 5. Conversion patterns

### 5.1 CTA architecture

- **One primary action per page.** Site-wide primary: *Book a Process Teardown*.
- **Site-wide secondary:** *Map your workflow cost* (→ /roi). This is the low-commitment path
  and should appear wherever the primary appears.
- **Tertiary/passive:** subscribe to notes; download a pattern library.
- Sticky header CTA appears after the hero scrolls out; never a full-screen interstitial, never
  an exit-intent modal. Both read as downmarket for a premium positioning.

### 5.2 The commitment ladder

Design the funnel so no step asks for more than the previous one earned:

```
Read → Use ROI tool (no email) → Email the result to yourself (email only)
     → Book a teardown (name, company, one text field) → Scoped proposal
```

Never gate the ROI results. Gating a calculator is the single most common conversion mistake in
this category and it destroys the honesty positioning at the same time.

### 5.3 Form design

- Teardown booking: **4 fields max** — name, work email, company, "what's eating the time?"
  (open text, generous, no character counter).
- Never ask for phone number before a call is booked. Never ask company size or budget as a
  required dropdown; if BMTech needs qualification, ask it as one optional question with a
  neutral "not sure yet" option.
- Inline validation on blur, never on keystroke. Errors are text next to the field, not toasts.
- Post-submit: a real page (not a modal) stating exactly what happens next and when —
  "You'll get a reply from [named person] within one business day, with two proposed times."
- Calendar embed permitted only if it loads lazily and has a keyboard-accessible fallback link.

### 5.4 Proof placement rules

- Proof appears adjacent to the claim it supports, never quarantined in a testimonials carousel.
- Carousels are prohibited for proof content (accessibility and comprehension cost, and they
  signal thin inventory). Use a static grid of 2–3.
- Every metric shown outside a case study links to the case study containing its method.
- Third-party review badges (Clutch, Google) rank above first-party quotes and should sit high
  on Home if BMTech has them. Mission Automate's placement of its Clutch widget in the hero
  region is the pattern to copy — *if and only if* BMTech has real reviews.

### 5.5 Risk reversal

Publish, in exact terms: the guarantee and its conditions, contract length, cancellation, IP and
data ownership, and what happens if BMTech is the wrong fit ("we'll say so on the teardown call
and you keep the written findings").

### 5.6 Measurement

Instrument: ROI tool starts, completions, and email-result submissions; teardown bookings by
source; scroll-depth to the pricing preview; case-study reads preceding a booking. Primary KPI
is **teardown bookings**; ROI completions are the leading indicator. Use a cookieless or
consent-gated analytics setup — running invasive tracking under an honesty brand is a
contradiction the team will regret.

---

## 6. Anti-patterns — do not build these

Observed across the research set and explicitly rejected:

- Grey/anonymized client logo walls, or logos used without written permission.
- Infinite-scrolling logo marquees (Applied AI Co's repeats the same five logos five times —
  it reads as padding).
- Auto-advancing testimonial carousels.
- Counter animations on unverified statistics.
- "Trusted by Fortune 500" when the relationship was a single workshop.
- AI-generated stock imagery of humanoid robots, glowing brains, or blue circuit boards.
- Chat widgets that open unprompted.
- Cookie walls that make "Accept all" one click and "Reject" three.
- Fake urgency ("2 slots left this month") unless it is literally true and verifiable.

---

## 7. Visual system

### 7.1 Brand attributes

**Precise · Calm · Substantial · Unhurried.** The reference feel is a well-made instrument or a
serious editorial publication — not a SaaS landing page and not an "AI agency."

### 7.2 Colour

- **Foundation:** a warm near-black (`~#12100E`) and a warm off-white (`~#FAF8F5`). Warm neutrals
  read as premium and immediately separate BMTech from the cool-blue/violet default of this
  category.
- **Primary accent:** exactly one saturated colour, used sparingly — for primary CTAs, active
  states, and data emphasis only. Recommend a deep amber or a deep teal, chosen against BMTech's
  existing brand assets once supplied.
- **Support neutrals:** a 5-step warm grey ramp for surfaces, borders, and secondary text.
- **Semantic:** success / warning / error / info, each tested at AA against both foundations.
- **Data-viz palette (for the ROI tool):** 4 hues, distinguishable in greyscale and under
  deuteranopia/protanopia simulation. Never encode meaning in colour alone (§9).
- Support light and dark themes; respect `prefers-color-scheme`, with a manual override that
  persists.

### 7.3 Typography

- **Display/headings:** a high-contrast serif or a distinctive grotesk with real character.
  Avoid Inter — it is the default of everything this brief is trying not to look like.
- **Body:** a highly legible humanist sans, 17–18px base on desktop, 16px minimum on mobile,
  line-height 1.6, measure capped at 68–72 characters.
- **Numerals/data:** a monospaced or tabular-figure face for all metrics, prices, and calculator
  output. Tabular figures are mandatory anywhere numbers align or animate.
- Type scale: modular, ~1.25 ratio, fluid via `clamp()`. Maximum 6 steps.
- Self-host fonts (`font-display: swap`, subset, preloaded) — no third-party font CDN.

### 7.4 Layout & space

- 12-column grid, 1200px content max, 720px for prose. Generous vertical rhythm — section padding
  should feel one step larger than instinct suggests.
- 8px spacing base; a 6-step scale.
- Breakpoints: 480 / 768 / 1024 / 1280 / 1600.
- Asymmetry is permitted and encouraged for editorial sections; the ROI tool stays on a strict grid.

### 7.5 Surfaces & depth

Borders and background-tone shifts over drop shadows. At most two elevation levels. Radii: 4px
(inputs, small), 8px (cards). No 24px pill cards. No glassmorphism, no neon glow, no animated
gradient meshes.

### 7.6 Imagery

Priority order: (1) real photographs of the BMTech team and real client sites, with permission;
(2) real product/system screenshots with sensitive data genuinely redacted, not blurred-for-effect;
(3) precise diagrams and typographic compositions; (4) nothing. Stock photography of generic
"business people" ranks below nothing.

Diagrams are a brand asset: workflow before/after diagrams, drawn in one consistent visual
language, are the most persuasive imagery available for this offer.

### 7.7 Motion

- Purposeful only: state transitions, reveal-on-scroll at low amplitude (≤16px, ≤300ms),
  focus/hover feedback.
- Standard easing, 150–300ms. No parallax, no scroll-jacking, no auto-playing video with sound.
- **`prefers-reduced-motion: reduce` must disable all non-essential motion**, including the ROI
  tool's number transitions (which then snap to final value).

### 7.8 Component inventory

Buttons (primary/secondary/tertiary/destructive × default/hover/active/focus/disabled/loading),
inputs, select, slider, radio/checkbox, form field with label+hint+error, card, metric block with
provenance footnote, quote block with attribution, logo lockup, table, tabs, accordion (FAQ),
banner/callout, breadcrumb, pagination, toast, skip link, footer, sticky CTA bar, ROI tool
composite (§10), workflow diagram, progress/step indicator.

### 7.9 Performance budget

LCP < 2.0s on 4G mobile; CLS < 0.05; INP < 200ms. JS ≤ 150KB gzipped for content pages
(the ROI route may add ≤ 80KB, code-split). No layout shift from fonts, images, or the ROI tool's
first render. Static generation for all content pages.

---

## 8. Copy direction

### 8.1 Voice

Plain, specific, quietly confident. The voice of a senior operator who has done the work and
doesn't need to impress you. Contractions yes; exclamation marks no; em-dashes sparingly.

### 8.2 Rules

- **Concrete nouns beat abstractions.** "Invoice matching" not "back-office optimization."
- **The buyer's words, not ours.** Say "the Friday report," "the copy-paste ritual," "chasing
  signatures." Sharp Hue's "the task that makes your team sigh" is the standard.
- **Second person, active voice.** "You'll get…" not "Clients receive…"
- **Every claim carries its evidence or gets cut.** No orphan adjectives: "proven," "leading,"
  "world-class," "cutting-edge," "trusted," "revolutionary" are banned unless immediately
  followed by the proof.
- **No hedged numbers.** "Up to 80%" and "as much as 10x" are prohibited. Publish the actual
  observed number for a named client, or a range with both ends real, or nothing.
- **Name the limits.** Say what BMTech doesn't do, what won't work, and what it costs. This is
  the highest-leverage copy move available given the positioning.
- Reading level: clear enough for a busy COO on a phone. Short sentences. Technical depth lives
  on /services and /security, where the gatekeeper will look for it.
- Sentence case for all headings. No Title Case Everywhere.

### 8.3 Headline formulas that fit the positioning

- Symptom → relief: *"Your team spends [X] on [task]. It shouldn't take a person."*
- Refusal: *"We don't sell roadmaps. We delete one process, then you pick the next."*
- Ownership: *"We build it, document it, and hand you the keys."*
- Arithmetic: *"One process. One number. Agreed before we start."*

### 8.4 Draft hero (placeholder — requires BMTech confirmation of the offer)

> **The work that eats your week, deleted one process at a time.**
> BMTech builds AI workflows for operations-heavy businesses — scoped to one process, measured
> against one number we agree before we start, and handed over documented so your team owns it.
> `[Book a process teardown]` `[Map your workflow cost →]`

### 8.5 Microcopy

Buttons state the outcome ("Book a process teardown," not "Submit"). Empty states teach. Error
messages say what to do next. Loading states in the ROI tool say what's being calculated.
The 404 offers the three most useful destinations.

---

## 9. Accessibility

**Target: WCAG 2.2 Level AA, with named AAA exceptions.** Non-negotiable, including in the ROI
tool. Publish `/legal/accessibility` with the conformance level, known gaps, and a contact route.

### 9.1 Requirements

- **Contrast:** 4.5:1 body, 3:1 large text and UI components/graphical objects. Target 7:1 for
  body copy on the primary surfaces (AAA) — it costs nothing at this palette.
- **Colour independence:** every colour-coded meaning also carries text, icon, or pattern. In
  the ROI tool, chart series are labelled directly, not via a colour-only legend.
- **Keyboard:** full operability, logical order, no traps. Visible focus indicator with ≥3:1
  contrast against adjacent colours and a 2px minimum outline — never `outline: none`.
  Skip-to-content link as the first focusable element.
- **Targets:** 24×24px minimum (WCAG 2.2 SC 2.5.8); 44×44px for primary mobile actions.
- **Semantics:** one `<h1>` per page, no skipped levels, landmark regions, native elements before
  ARIA. The ROI tool's controls are real `<input>`/`<label>` pairs.
- **Live regions:** ROI results update via `aria-live="polite"` with debounced announcements so
  screen-reader users aren't flooded on every slider tick.
- **Forms:** persistent visible labels (never placeholder-as-label), programmatic error
  association, hints via `aria-describedby`. SC 3.3.7 — don't re-ask for information already
  provided in the same flow.
- **Motion:** honour `prefers-reduced-motion`. No content flashing more than 3×/second.
- **Media:** captions and transcripts for any video; meaningful alt text; decorative images
  `alt=""`. Diagrams get a text-equivalent description, not `alt="diagram"`.
- **Zoom/reflow:** usable at 400% zoom and 320px width without horizontal scroll.
- **Language:** `lang` set; page titles unique and descriptive.

### 9.2 Verification

Automated (axe + Lighthouse in CI, zero serious/critical violations to merge) **plus** manual:
keyboard-only pass, VoiceOver/Safari and NVDA/Firefox passes on Home, /roi, /contact, and one
case study, 400% zoom pass, and forced-colours-mode check. Automated testing alone catches
roughly a third of real issues; treat the manual pass as required.

---

## 10. Interactive feature — Workflow ROI Mapper

The site's signature asset. It lives at `/roi`, is linked from every page, requires no email, and
is the primary reason someone forwards the site to a colleague.

### 10.1 Concept

The buyer describes one painful process. The tool returns two things:

1. **A workflow map** — an auto-generated before/after diagram of their process, showing which
   steps become automated, which stay human-in-the-loop, and where the handoffs are.
2. **Honest arithmetic** — what that process currently costs them, per their own inputs, and what
   a realistic range of recovered time and cost looks like.

The workflow map is what makes it memorable; the arithmetic is what makes it forwardable to a CFO.

### 10.2 Flow

**Step 1 — Pick a pattern.** 6–8 pre-modelled workflow patterns as cards, plus "something else."
Each corresponds to a real BMTech capability (e.g. inbound lead intake and routing; document/
invoice extraction and matching; recurring report assembly; scheduling and coordination across
tools; support triage and first response; onboarding checklists and chasing).

**Step 2 — Describe it.** 4–6 inputs, sliders with typed-entry fallback, all pre-filled with a
labelled, sourced default so the tool is never empty:
- volume (items per week/month)
- minutes of human handling per item
- people involved
- fully-loaded hourly cost (with a plain-language definition and a regional default)
- rework/error rate (optional)
- cycle time, where the pattern makes it relevant

**Step 3 — See the map and the numbers.** Rendered immediately and live. No submit button, no gate.

**Step 4 — Take it with you.** Copy link (state encoded in the URL, shareable), download a
one-page PDF, or email it to yourself. Email is optional, clearly labelled as optional, and the
results remain fully visible whether or not it's given.

**Step 5 — Convert.** "This is an estimate from your numbers. A teardown replaces it with
measured ones." → book.

### 10.3 The arithmetic (must be visible in the UI)

```
current_annual_hours   = volume_per_week × minutes_per_item / 60 × 52 × people_touching
current_annual_cost    = current_annual_hours × loaded_hourly_cost
rework_annual_cost     = current_annual_cost × error_rate × rework_multiplier
recovered_hours_range  = current_annual_hours × automation_share[pattern] × [low, high]
net_first_year_range   = (recovered_hours_range × loaded_hourly_cost)
                         − engagement_cost_band − annual_run_cost_band
payback_months_range   = engagement_cost_band / (monthly recovered value)
```

An **"How this is calculated"** panel is open by default on desktop and one tap away on mobile.
It shows every formula, every assumption, and the source and confidence of each
`automation_share` coefficient. Coefficients come from BMTech's own delivery history where it
exists; where it doesn't, they are labelled **"industry-typical range, not BMTech-measured"** —
and if BMTech has no basis at all for a pattern, that pattern ships without a coefficient and the
tool reports only current cost, not projected savings.

### 10.4 Honesty constraints (these are product requirements, not disclaimers)

- Results are always **ranges**, never single numbers. A range communicates uncertainty
  structurally, where a footnote doesn't.
- The persistent framing line — not fine print, but sitting next to the headline number:
  *"These are your numbers, our arithmetic. Not a projection of results, and not a quote."*
- Costs (engagement + ongoing run costs: model API spend, platform subscriptions, maintenance)
  are subtracted, visibly. A calculator that only shows savings is a sales toy; one that shows
  net is a tool.
- The tool must be able to return a discouraging answer. If inputs imply payback beyond ~18
  months, it says so plainly and suggests the process may not be worth automating yet. This
  single behaviour does more for credibility than any testimonial on the site.
- No dark patterns: no fake "calculating…" delay, no "your custom report is being prepared,"
  no results teased behind a form.
- Zero server-side storage of inputs unless the user opts in by emailing themselves the result;
  state that in the UI, not just the privacy policy. Computation runs client-side.

### 10.5 UX & states

Desktop: inputs left, live map and results right, both visible without scrolling. Mobile: stacked,
with a sticky summary bar showing the headline range as inputs change. Debounce recalculation at
~150ms; animate number changes ≤200ms with tabular figures (and no animation under reduced
motion). Handle: no JS (server-rendered static version of the patterns with a printable worksheet),
extreme/zero/nonsense inputs (clamp with an explanatory message, never `NaN`, never `Infinity`),
and deep links restoring full state.

### 10.6 Accessibility of the tool

Sliders are `<input type="range">` with visible labels, numeric text inputs, and full keyboard
support (arrows, Home/End, Page Up/Down). Results carry `aria-live="polite"` with debounced,
summarized announcements ("Estimated annual cost, forty-one thousand to fifty-two thousand
dollars"). The workflow diagram has an equivalent ordered-list text representation, always
available — not hidden behind a toggle labelled "accessible version." All chart data is also
available as a table.

### 10.7 Success criteria

≥35% of /roi visitors complete step 3; ≥15% of completions share, download, or email; ≥8% of
completions book a teardown; and qualitatively — prospects arrive at the teardown call already
holding their own numbers.

---

## 11. Proof integrity — the strict rule

### 11.1 The rule

> **Nothing appears on the BMTech website that BMTech cannot substantiate on demand.**
>
> No invented client names, logos, testimonials, quotes, headshots, case studies, metrics,
> ratings, review counts, certifications, awards, partner badges, team members, credentials,
> project counts, client counts, years in business, or "trusted by" claims. Not in production,
> not in staging, not in a screenshot, not "as a placeholder we'll swap later."

This applies to everyone who touches the site — BMTech, designers, developers, copywriters, and
any AI tool used in production. It is a release-blocking condition, not a guideline.

### 11.2 Why it's a business decision, not just ethics

The research explicitly downgraded firms for unsubstantiated claims: White Glove Labs' "50+
enterprise clients, 95% success, 40% ROI improvement" scored 49/100 and "Low" confidence
specifically because nothing was corroborated, while Loophole's single named client with a
modest 15-hours-a-month result scored higher. Sophisticated mid-market buyers apply the same
discount. Fabricated proof is also legally exposed (FTC endorsement rules, UK CAP Code, and
EU UCPD all bite), and it is the one mistake that permanently ends a consultancy's credibility
with the exact audience BMTech wants.

### 11.3 Evidence tiers — what may be published

| Tier | Evidence | May publish as |
|---|---|---|
| A | Third-party verifiable (Clutch/Google reviews, certifications, public client references) | Headline proof, hero placement |
| B | Named client, written permission, client-confirmed metric | Case studies, quotes, logos |
| C | Named client, permission, but metric is BMTech-measured and not client-confirmed | Case study with the measurement method disclosed |
| D | Anonymized client ("a 40-person logistics firm"), real engagement, real number | Permitted only with the anonymization reason stated and the number's method shown |
| E | Aggregate across engagements ("across 6 engagements, median…") | Permitted only if n is stated and n ≥ 3 |
| F | Founder's prior-employer work | Permitted only on /about, attributed to the individual and the employer, never as BMTech's record |
| G | Industry benchmarks and third-party research | Permitted only with a citation and an explicit "not our result" label |
| H | Anything else | **Not published** |

**Provenance line requirement:** every metric published at Tier B–E carries a visible note
covering source, measurement window, and method. Format: *"Measured over 8 weeks post-launch
against a 4-week pre-launch baseline; figures confirmed by [Client]."*

### 11.4 Placeholder convention during build

Placeholders must be **impossible to mistake for real content and impossible to ship**:

- Text: `{{CLIENT_NAME}}`, `{{METRIC_VALUE}}`, `{{TESTIMONIAL_QUOTE}}` — double-brace, uppercase.
- Images: a visibly marked "PLACEHOLDER — NOT FOR RELEASE" asset. Never a real-looking logo,
  never a stock headshot, never an AI-generated face.
- No lorem ipsum in proof components — it hides emptiness. Use `{{...}}` so it reads as missing.
- **CI gate:** a build step fails the production build if `{{`, `PLACEHOLDER`, or `lorem ipsum`
  appears in any committed content or rendered output. This is the mechanical enforcement of
  §11.1 and should be implemented in the first sprint, before any content pages.

### 11.5 Proof Intake (BMTech must complete before content work)

For each engagement BMTech wants to reference:

1. Client legal name and contact who can approve
2. Written permission on file? (logo use / name use / quote use / metric use — separately)
3. What was actually delivered
4. Baseline: metric, value, how measured, over what period
5. Result: metric, value, how measured, over what period
6. Who measured it — BMTech, the client, or a system report
7. Attributable quote + speaker name, title, and their approval
8. Has the client reviewed the final page? (date)

Plus, firm-level: founding date, headcount, completed-engagement count, review profiles,
certifications and their issuers, partner statuses and their evidence, team credentials with
issuing institutions.

Anything without a complete row does not go on the site.

### 11.6 If proof is thin — the credible-newcomer pattern

If BMTech has few or no publishable engagements, the site does **not** compensate with vague
claims. It substitutes **demonstrated capability** for track record:

- Lead with the ROI Mapper — a working artifact is proof of competence that requires no clients.
- Publish detailed, honest methodology: /process and /security show exactly how work is done.
- Publish workflow teardowns on public or self-owned processes — "here's how we'd automate a
  dental practice's payroll, in detail, with the actual tools" — clearly labelled as illustrative,
  not as client work.
- Publish the founders' verifiable individual histories at Tier F, correctly attributed.
- Say the honest thing plainly: *"We're a new firm. Here's exactly how we work, what it costs,
  and what happens if it doesn't hit the number."* Founded-date transparency plus a real
  guarantee outperforms a fake logo wall with every buyer worth having.

### 11.7 Review gate

Before launch and before any content release, one named person signs a checklist:
every claim mapped to a tier; every Tier B–E metric carrying a provenance line; every logo backed
by written permission on file; every quote approved by its named speaker; every statistic traced
to a source; every ROI coefficient labelled as measured or industry-typical; no placeholders in
the build; CI proof-gate green.

---

## 12. Technical direction (light)

Static-first: Astro or Next.js (SSG) with the ROI tool as an isolated, code-split island. Content
in MDX with a typed schema that makes the provenance fields on case studies and metrics
**required** — the schema is where §11.3 gets enforced structurally rather than by memory.
Client-side-only computation for the ROI tool. Privacy-respecting analytics. No third-party
scripts without a documented justification and a consent gate.

---

## 13. Open questions for BMTech

**Blocking (content cannot be written without these):**
1. Full name, legal entity, founding date, headcount, locations.
2. Existing brand assets — logo, colours, type — or is this a from-scratch identity?
3. Actual service catalogue and the one thing BMTech most wants to sell.
4. Proof Intake (§11.5) — completed.
5. Will BMTech adopt the "one metric, agreed before build" commitment and the guarantee? If not,
   §3.3.1 and Home §8 are cut.
6. Real price bands for tiers 1–4, or an explicit decision not to publish them.

**Non-blocking (design can proceed with assumptions):**
7. Primary geography and languages.
8. Named practitioners to feature, and are they willing to be the face of the site?
9. Delivery data available to ground the ROI coefficients (§10.3).
10. CRM/calendar/analytics stack the site must integrate with.
11. Which of the ICPs in §2 does BMTech actually want to prioritize?
12. Compliance obligations (GDPR, HIPAA, SOC 2 status) that /security must reflect.

---

## 14. Definition of done

- [ ] Every section in §4.1 built and content-complete with real, sourced content
- [ ] Proof Intake complete; every claim mapped to a tier in §11.3
- [ ] CI proof-gate implemented and green; zero placeholders in production build
- [ ] axe/Lighthouse: zero serious or critical a11y violations
- [ ] Manual a11y pass complete on Home, /roi, /contact, one case study
- [ ] Performance budgets met on throttled 4G mobile
- [ ] ROI Mapper: math reviewed by BMTech, coefficients labelled, discouraging-answer path tested
- [ ] Copy reviewed against §8.2, with every banned adjective removed or evidenced
- [ ] Analytics and conversion tracking live
- [ ] §11.7 review gate signed by a named owner
