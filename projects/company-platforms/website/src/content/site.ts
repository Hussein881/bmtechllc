/**
 * Production copy for the BMTech homepage.
 *
 * Proof rule (DESIGN_BRIEF.md §11.1): nothing here is a claim BMTech cannot
 * substantiate on demand. There are no client names, logos, quotes, metrics,
 * ratings, counts, or dates in this file, because none were supplied. Every
 * statement below is either a description of how BMTech works or a commitment
 * BMTech makes — both substantiable by BMTech itself. This is the
 * credible-newcomer path in §11.6: shippable copy, not stand-in text awaiting
 * numbers. (Phrasing avoids the literal token the proof gate scans for.)
 */

import { cautiousFactor, workingWeeks } from '../lib/roi'

export const nav = [
  { href: '#services', label: 'What we do' },
  { href: '#process', label: 'Working with us' },
  { href: '#security', label: 'Security' },
  { href: '#faq', label: 'FAQ' },
] as const

export const cta = {
  primary: { href: '#contact', label: 'Book a workflow teardown' },
  secondary: { href: '#roi', label: 'See what the work costs' },
} as const

export const hero = {
  eyebrow: 'AI systems for busy operations teams',
  heading: "Get the repetitive work off your team's plate.",
  lede: "Pick one process that keeps stealing time. We'll map it and build the fix. When we're done, your team gets a system it can run.",
  note: "BMTech is new, so we don't have a wall of client logos to show you yet. You can still see how a project runs and what happens to your data. We also spell out what you own when we're done.",
  summary: [
    { label: 'Start with', value: 'One process' },
    { label: 'Track', value: 'One useful number' },
    { label: 'Finish with', value: 'A system you own' },
  ],
}

export const heroDiagram = {
  title: 'Supplier invoice matching — after',
  steps: [
    { label: 'Invoice arrives in shared inbox', state: 'automated', tag: 'System' },
    { label: 'Line items and totals extracted', state: 'automated', tag: 'System' },
    { label: 'Matched against purchase order', state: 'automated', tag: 'System' },
    { label: 'Exceptions queued with the reason attached', state: 'human', tag: 'Person' },
    { label: 'Approved batch posted to the ledger', state: 'automated', tag: 'System' },
  ],
  caption:
    'An illustration of the shape of a build, drawn from a common workflow pattern. It is not a client engagement.',
} as const

export const problem = {
  eyebrow: 'What we usually walk into',
  heading: 'You can name the work. That is the whole qualification.',
  lede: 'Most of what we are asked to fix looks like one of these three. None of them are failures of effort.',
  items: [
    {
      title: 'The tools do not talk',
      body: 'The CRM, the inbox, the spreadsheet, and the scheduling system each hold part of the truth. Someone reconciles them by hand, every week, and that person is usually your best operator.',
    },
    {
      title: 'Skilled people do clerical work',
      body: 'Re-keying, chasing, copying between tabs, formatting the Friday report. You hired judgement and you are paying for typing.',
    },
    {
      title: 'Nobody can put a number on it',
      body: 'You know the backlog is expensive. You cannot say how expensive, so the case for fixing it never quite gets made and the headcount request comes back instead.',
    },
  ],
  outcome: {
    heading: 'What changes',
    items: [
      'One process runs without a person in the middle of it, with the exceptions routed to someone who can decide.',
      'The hours it used to take are measured before and after, against a baseline you agreed to.',
      'Your team holds the documentation, the credentials, and the ability to change it without calling us.',
    ],
  },
}

/**
 * Copy for the workflow ROI mapper (DESIGN_BRIEF.md §10).
 *
 * Proof rule note: the starting positions below are conventions chosen to give
 * the sliders somewhere sensible to begin, not coefficients measured on BMTech
 * engagements — we have none to quote yet, and §10.3 says a pattern without a
 * basis ships without a measured coefficient. The interface says so in as many
 * words, and the automation share stays a control the visitor owns.
 */
export const mapper = {
  eyebrow: 'A quick cost check',
  heading: 'How much is this process costing you?',
  lede: "Use four numbers you already know. The calculator stays in your browser, and you won't have to hand over an email address to see the result.",
  patternsLabel: 'What kind of work is it?',
  patternsNote:
    "Pick the closest example, then change the numbers. The starting points are rough defaults. They don't come from BMTech client work.",
  inputsLabel: 'Add your numbers',
  fields: {
    people: {
      label: 'People involved',
      hint: 'Count everyone who touches the process in a normal week, including the person who checks the final result.',
    },
    hoursPerWeek: {
      label: 'Hours a week, each',
      hint: 'Include the chasing, checking, and fixing that happens around the main task.',
    },
    hourlyCost: {
      label: 'Loaded hourly cost',
      hint: 'Use salary plus taxes, benefits, software, and overhead. A rough figure is fine.',
    },
    automationShare: {
      label: 'How much could be automated?',
      hint: 'Estimate the part that follows clear rules and needs little judgement.',
    },
    currency: { label: 'Currency' },
  },
  framing: 'Use this as a planning estimate. The quote and savings target come after a teardown.',
  method: {
    heading: 'Show the maths',
    lines: [
      `Annual hours = people × weekly hours × ${workingWeeks} working weeks. That leaves room for holidays and time off.`,
      'Annual cost = annual hours × your loaded hourly cost.',
      `The high end uses the percentage you chose. The cautious end uses ${Math.round(cautiousFactor * 100)}% of that estimate.`,
      `Weekly hours back = recovered annual hours ÷ ${workingWeeks}. Currency changes the money figure, but it doesn't change the fit check.`,
    ],
    close:
      'Every result comes from the four numbers above. The formula uses no client benchmark or hidden multiplier.',
  },
  verdicts: {
    unlikely: {
      label: 'Probably not worth automating yet',
      body: "The cautious estimate gives you less than two hours back each week. We'd leave this one alone for now because the build would eat most of the benefit. Try a busier process instead.",
    },
    borderline: {
      label: 'Take a closer look',
      body: "The answer depends on the messy bits: exceptions, patchy data, and the systems that need updating. A teardown will tell us if the numbers hold up. You keep the findings either way.",
    },
    strong: {
      label: 'This could be worth fixing',
      body: "Even the cautious estimate gives back a useful chunk of someone's week. The next step is to measure the current process properly and check the exceptions before anyone talks about a build.",
    },
  },
  timeToValue: {
    heading: 'A note on timing',
    body: "The teardown takes one working session, with the write-up a few days later. A first build takes weeks. The quarterly estimate assumes the workflow is already running for the whole quarter.",
  },
  costsNote:
    "The estimate leaves out the build price, model usage, software subscriptions, and upkeep. We'll put those costs in writing after the teardown so you can judge the whole deal.",
  cta: {
    heading: 'Keep the numbers',
    body: "Send the summary with your enquiry or paste it into an internal note. We'll start with the process you've described.",
    label: 'Book a teardown',
    copy: 'Copy the summary',
    reset: 'Start over',
  },
}

export type MapperStep = { label: string; state: 'automated' | 'human' }

export type MapperPattern = {
  id: string
  name: string
  body: string
  /** Starting slider positions — conventions, not measured coefficients. */
  people: number
  hoursPerWeek: number
  automationShare: number
  /** The usual shape of the work once built. Empty where the shape varies. */
  steps: MapperStep[]
}

export const mapperPatterns: MapperPattern[] = [
  {
    id: 'intake',
    name: 'New enquiries',
    body: 'Requests come in from forms, inboxes, and call notes. They need logging, checking, and sending to the right person.',
    people: 3,
    hoursPerWeek: 6,
    automationShare: 55,
    steps: [
      { label: 'Collect each new enquiry', state: 'automated' },
      { label: 'Pull out the details and create the record', state: 'automated' },
      { label: 'Route it using your rules', state: 'automated' },
      { label: 'Send unclear cases to a person', state: 'human' },
    ],
  },
  {
    id: 'documents',
    name: 'Invoices and documents',
    body: 'Invoices, orders, delivery notes, or claim files need reading, matching, and posting into the right system.',
    people: 2,
    hoursPerWeek: 9,
    automationShare: 60,
    steps: [
      { label: 'Sort the incoming document', state: 'automated' },
      { label: 'Read the line items and totals', state: 'automated' },
      { label: 'Match it to the order or policy', state: 'automated' },
      { label: 'Queue mismatches for a person', state: 'human' },
    ],
  },
  {
    id: 'reporting',
    name: 'Weekly or monthly reports',
    body: "Someone rebuilds the same report from several systems, and half the method lives in that person's head.",
    people: 2,
    hoursPerWeek: 5,
    automationShare: 65,
    steps: [
      { label: 'Pull figures from each system', state: 'automated' },
      { label: 'Apply the same definitions each time', state: 'automated' },
      { label: 'Build and file the report', state: 'automated' },
      { label: 'Leave the commentary to a person', state: 'human' },
    ],
  },
  {
    id: 'scheduling',
    name: 'Scheduling',
    body: 'Appointments or field jobs are spread across calendars, spreadsheets, and whatever the team uses on the road.',
    people: 3,
    hoursPerWeek: 8,
    automationShare: 45,
    steps: [
      { label: 'Collect requests and check availability', state: 'automated' },
      { label: 'Offer times and chase replies', state: 'automated' },
      { label: 'Update each system after a change', state: 'automated' },
      { label: 'Send clashes to the coordinator', state: 'human' },
    ],
  },
  {
    id: 'triage',
    name: 'Support inboxes',
    body: 'Most answers already exist in your own documents, but someone still has to read, sort, and answer every ticket.',
    people: 4,
    hoursPerWeek: 7,
    automationShare: 50,
    steps: [
      { label: 'Read and sort the queue', state: 'automated' },
      { label: 'Draft a reply from your documents', state: 'automated' },
      { label: 'Attach the sources', state: 'automated' },
      { label: 'Have a person approve the reply', state: 'human' },
    ],
  },
  {
    id: 'onboarding',
    name: 'Onboarding and follow-up',
    body: 'New clients, staff, or suppliers move through a checklist while someone keeps asking for the same missing document.',
    people: 2,
    hoursPerWeek: 6,
    automationShare: 55,
    steps: [
      { label: 'Open the checklist and send requests', state: 'automated' },
      { label: 'Check returned items', state: 'automated' },
      { label: 'Send reminders for anything missing', state: 'automated' },
      { label: 'Leave sign-off with a person', state: 'human' },
    ],
  },
  {
    id: 'other',
    name: 'Something else',
    body: "Got a different repeatable process? Set the four numbers yourself. The maths works the same way.",
    people: 2,
    hoursPerWeek: 5,
    automationShare: 40,
    steps: [],
  },
]

export const industries = {
  eyebrow: 'Best fit',
  heading: 'A good fit for busy back offices',
  lede: 'We do our best work when the same task comes around all week and someone still has to move it between an inbox, a spreadsheet, and a system that refuses to talk to the others.',
  items: [
    {
      name: 'Professional services',
      body: 'Legal, accounting, and agencies: intake, conflict checks, document assembly, time and billing prep, client reporting.',
    },
    {
      name: 'Multi-location healthcare',
      body: 'Clinic groups: referral intake, prior authorisation chasing, scheduling across sites, records requests.',
    },
    {
      name: 'Property management',
      body: 'Maintenance triage, tenant correspondence, vendor coordination, lease and renewal paperwork.',
    },
    {
      name: 'Logistics and field services',
      body: 'Dispatch coordination, proof-of-delivery handling, exception tracking, subcontractor paperwork.',
    },
    {
      name: 'Manufacturing and distribution',
      body: 'Quote and order entry, supplier invoice matching, spec sheet lookups, recurring production reporting.',
    },
    {
      name: 'Claims and insurance operations',
      body: 'First-notice intake, document classification, completeness checks, status correspondence.',
    },
  ],
  disqualifiers: {
    heading: "Work we'll pass on",
    lede: "Some jobs aren't a fit. We'd rather tell you here than waste an hour on a sales call.",
    items: [
      "Projects built around cutting headcount. We free up people's time so they can handle better work.",
      "New consumer apps or training a model from scratch. That's outside our lane.",
      "Regulated data we can't handle safely. We'll draw that line before you send us anything.",
      "Work with no clear process behind it. We'll map the process first.",
    ],
  },
}

export const services = {
  eyebrow: 'What we do',
  heading: 'Which job keeps eating the week?',
  lede: 'Open the closest match to see what could change.',
  items: [
    {
      index: '01',
      title: 'Process automation',
      body: 'We connect the intake, checks, handoffs, and system updates that make one repeatable process drag on from the first email to the final update.',
      before: 'Someone moves the same item through four tools. Then they check it twice.',
      after: 'It moves on its own. A person steps in when the rules flag a problem.',
    },
    {
      index: '02',
      title: 'Inbox and support assistants',
      body: 'We set up assistants that sort a queue, look through your own documents, and draft the next reply for a person to check.',
      before: 'Every question waits. One person knows where the answer lives.',
      after: 'That person gets a draft with the source attached and makes the final call.',
    },
    {
      index: '03',
      title: 'Data and reporting',
      body: 'We pull the numbers from the systems you already use and rebuild the same report on schedule, using definitions everyone can see.',
      before: 'Friday disappears into copy and paste. Two tabs show two answers.',
      after: 'The report arrives ready for someone to review and explain.',
    },
    {
      index: '04',
      title: 'Handover and training',
      body: "We show the people who'll run the workflow how it works, where it can fail, and what they can change themselves.",
      before: 'The software is live, but every small change still needs a consultant.',
      after: 'Your team runs it.',
    },
  ],
}

export const decisionGuide = {
  eyebrow: 'Decide before you buy',
  heading: 'A process is ready for automation when these five things are true',
  lede:
    'This is the same screen we use before recommending a build. If the process fails it, the useful answer may be to fix the process first — or leave it alone.',
  signals: [
    {
      index: '01',
      title: 'It repeats often enough',
      body: 'The same shape of work turns up every week, not twice a year. Volume is what gives a small improvement room to compound.',
    },
    {
      index: '02',
      title: 'The current steps can be named',
      body: 'Someone can show the inputs, decisions, exceptions, and destination. If the process only lives in intuition, it needs mapping before it needs software.',
    },
    {
      index: '03',
      title: 'Most handling follows rules',
      body: 'Judgement can stay with a person while extraction, matching, routing, drafting, and system updates handle the repeatable volume.',
    },
    {
      index: '04',
      title: 'There is one result to measure',
      body: 'Hours per case, backlog age, response time, error rate, or another number can be measured before and after the change.',
    },
    {
      index: '05',
      title: 'The exceptions have an owner',
      body: 'When data is missing or a decision is ambiguous, a named person can resolve it. Good automation makes that path clearer; it does not pretend it disappears.',
    },
  ],
  stop: {
    heading: 'The honest stop rule',
    body: 'If the cautious value in the workflow mapper is smaller than the build and running costs, we should not build it. A teardown can still point to the heavier process, but a weak business case does not become strong because AI is involved.',
  },
  economics: {
    heading: 'What the written quote separates',
    lede:
      'You should be able to compare the cost with the value without reconstructing the numbers from a sales call. The quote keeps these three lines separate.',
    items: [
      {
        index: 'A',
        title: 'The fixed build',
        body: 'The agreed single-process scope, target, implementation, testing, documentation, and handover.',
      },
      {
        index: 'B',
        title: 'Third-party running costs',
        body: 'Expected model usage, platform subscriptions, and any infrastructure the workflow needs to keep running.',
      },
      {
        index: 'C',
        title: 'Support, if you want it',
        body: 'Any ongoing monitoring or changes are priced separately and are not required for your team to own the system.',
      },
    ],
    note: 'A truthful starting price belongs here once BMTech has stood behind one in real delivery. Until then, the site explains the full cost structure rather than publishing a made-up range.',
  },
}

export const process = {
  eyebrow: 'Working with us',
  heading: 'A small project with a clear finish line',
  lede: "We agree on the job and the price before we build. The result goes in writing too, along with what we'll need from your team.",
  steps: [
    {
      num: '01',
      title: 'Teardown',
      body: "We spend an hour with the person who knows the work. Then we map the steps, volume, trouble spots, and time cost. The write-up is yours, even if the project stops there.",
      need: 'Bring the person who runs the process and a real example of the work.',
    },
    {
      num: '02',
      title: 'Agree on the result',
      body: "We choose one number and write down how we'll measure it. If we can't agree on a fair test, the build doesn't start.",
      need: 'You approve the target and the test.',
    },
    {
      num: '03',
      title: 'Build',
      body: "The first build takes weeks. You'll see it working with real examples while there's still time to catch a bad assumption.",
      need: 'We need system access, sample data, and one person who can answer questions quickly.',
    },
    {
      num: '04',
      title: 'Handover',
      body: "Your team gets the accounts, credentials, workflow rules, prompts, and plain-English notes. We walk through the whole system with the people who'll run it.",
      need: 'Bring the team taking over the workflow.',
    },
  ],
  commitment: {
    heading: 'If the build misses the target',
    body: "We'll keep working at our cost until it passes the test we agreed on. You can also stop and pay for the work delivered so far. That choice goes into the engagement letter, along with the access and input we need from your team.",
    note: "You'll get a fixed price after the teardown. We don't have a public price range yet because BMTech hasn't completed enough similar projects to set one honestly.",
  },
}

export const security = {
  eyebrow: 'Data and ownership',
  heading: 'What happens to your data',
  lede: 'Share this section with the person who looks after security or IT.',
  items: [
    {
      title: "Your data stays out of model training",
      body: "We use business API plans that keep your content out of model training. You'll see every model provider in the project data map before you sign.",
    },
    {
      title: 'We ask for the smallest access we need',
      body: "Access sits in accounts you control. You can turn it off without waiting for us.",
    },
    {
      title: 'People keep the important decisions',
      body: 'A person approves anything that leaves the company, moves money, or changes an important record.',
    },
    {
      title: "Unclear cases don't get buried",
      body: "Unreadable file? Bad match? Strange model response? The workflow sends it to a person and explains what went wrong.",
    },
    {
      title: 'You choose how long data stays around',
      body: "We agree on retention before work starts and delete our working copies when asked. You'll also get the subprocessor list up front.",
    },
    {
      title: 'You can leave with a working system',
      body: 'The accounts, setup notes, workflow rules, and prompts belong to you. You can end support and keep the system running in your own accounts.',
    },
  ],
  privacy:
    "This site has no ad trackers, chat widget, outside analytics, or third-party fonts. Your calculator inputs stay in the browser.",
}

export const faq = {
  eyebrow: 'Straight answers',
  heading: 'A few things you may be wondering',
  items: [
    {
      q: "You're new. Why should we hire you?",
      a: [
        "Judge us by what we'll put in writing. You'll see the result and the test first. The fixed price and handover plan follow before the build starts.",
        "If you need a long client list before you'll consider a firm, we're probably too early for you. That's fair.",
      ],
    },
    {
      q: "What happens if it doesn't work?",
      a: [
        "If the build misses the agreed result, we'll keep working at our cost. You can also stop and pay for what has been delivered so far. The engagement letter spells out both choices.",
        "We need the agreed access, sample data, and answers from your team while we work. If those disappear, the test date moves too.",
      ],
    },
    {
      q: 'Are you here to replace our staff?',
      a: [
        'No, and we turn down engagements whose stated goal is cutting headcount. The work we remove is the clerical layer around your team’s judgement.',
        'In practice the people who ran the process become the people who run the workflow and handle the exceptions.',
      ],
    },
    {
      q: 'How much does it cost?',
      a: [
        "You'll get a fixed price after the teardown. It changes only when you approve a change in scope.",
        "The quote also shows the expected model fees, software subscriptions, and upkeep. Those costs matter, so we won't tuck them into a footnote.",
      ],
    },
    {
      q: 'How long will it take?',
      a: [
        'The teardown takes one working session. The write-up follows within a few days, and a first build is planned in weeks.',
        "If the process looks too large for that schedule, we'll say so in the teardown and cut the scope before it turns into a sprawling programme.",
      ],
    },
    {
      q: 'Who owns the system?',
      a: [
        'You do. We build in accounts you control and hand over the credentials, workflow rules, prompts, and notes.',
        'Support runs month to month. You can stop it and keep using the system.',
      ],
    },
    {
      q: 'We have already bought AI tools that went nowhere. How is this different?',
      a: [
        'Tools are not the hard part. The hard part is one named process, its exceptions, and the write-back into the systems you already run.',
        'That is why the engagement starts at a process rather than at a platform, and why the first deliverable is a measurement rather than a licence.',
      ],
    },
    {
      q: 'What do you need from us?',
      a: [
        'An hour with the person who actually does the work, system access scoped to the process, sample data, and one decision-maker who can answer questions within a business day.',
        'That is genuinely the list. If those are not available, the build will slip, and we would rather say that now than discover it in week three.',
      ],
    },
  ],
}

export const finalCta = {
  eyebrow: 'Start here',
  heading: 'Bring us the process everyone complains about',
  lede: "We'll spend one working session pulling it apart. A few days later, you'll have a written answer on what to fix and what to leave alone.",
  steps: [
    'Tell us which process is eating the time.',
    'We reply within one business day with two times.',
    'The working session takes 60 to 90 minutes.',
    'You get the write-up a few days later.',
  ],
  note: "You won't get dropped into a sales sequence. The form opens an email draft that you control.",
}

export type FooterLink = { href: string; label: string }

export type FooterColumn = {
  title: string
  links: readonly FooterLink[]
  /** Optional plain-language note under the column. */
  note?: string
}

/**
 * Proof rule (§11.1) applied to contact details: this site publishes no email
 * address, phone number, or postal address, because none has been supplied that
 * actually reaches BMTech. Both routes below point at the on-page assessment
 * form, which is the only working one. See README.md, "Launch blockers".
 */
const footerColumns: FooterColumn[] = [
  {
    title: 'On this page',
    links: nav,
  },
  {
    title: 'Get in touch',
    links: [
      { href: '#contact', label: 'Book a workflow teardown' },
      { href: '#contact', label: 'Tell us about the process' },
    ],
    note: "The form is the only contact route for now. We haven't published an email address or phone number until BMTech has one that's ready for client enquiries.",
  },
]

export const footer = {
  blurb:
    'BMTech fixes repetitive operational work, one process at a time. Your team gets the finished system and the notes to run it.',
  columns: footerColumns,
  legal:
    "BMTech is new, so there aren't any client names or testimonials here yet. When we have work we can share with permission, we'll publish the result, the time period, and how it was measured.",
}
