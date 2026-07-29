import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * INTERNAL KNOWLEDGE BASE CONTRACT
 *
 * This corpus serves the BenchmarkTech team, not prospects. Two consequences
 * shape every decision below:
 *
 *   1. Everything is internal by default. There is no public/private build
 *      gate, because there is no public build. `visibility: shareable` is an
 *      opt-in marker for pages we would be willing to publish externally —
 *      it changes a badge, not the build.
 *
 *   2. Drafts render. Internal teams collaborate on work in progress; hiding
 *      it defeats the purpose. Drafts render with a visible banner instead.
 */

// ─── Controlled tag vocabulary ────────────────────────────────────────────────
// Adding a tag = one-line PR here. Free-form tags are a build error.
export const TAGS = [
  // Technical domains
  'ai-strategy',
  'rag',
  'llm',
  'data-engineering',
  'machine-learning',
  'evaluation',
  'automation',
  'infrastructure',
  'security',

  // Engagement lifecycle
  'scoping',
  'discovery',
  'delivery',
  'handoff',
  'retro',

  // Operating the business
  'onboarding',
  'tooling',
  'process',
  'pricing',
  'client-comms',

  // Document type
  'runbook',
  'playbook',
  'template',
  'checklist',
  'decision',
  'reference',
  'postmortem',
] as const;

type Tag = typeof TAGS[number];

// ─── Schema ──────────────────────────────────────────────────────────────────

const pageSchema = z.object({
  title: z.string(),

  /**
   * The retrieval abstract. Doubles as the search-result summary and the
   * index.json description consumed by internal agent tooling. Forcing it to
   * exist forces every page to be summarizable — a quality gate in itself.
   */
  description: z
    .string()
    .min(20, 'Description must be at least 20 chars — it is the retrieval abstract.'),

  tags: z.array(z.enum(TAGS as [Tag, ...Tag[]])).default([]),

  /**
   * Drafts and archived pages still build; the layout renders a banner.
   * Hiding in-progress work from your own team is counterproductive.
   */
  status: z.enum(['draft', 'published', 'archived']).default('draft'),

  /** Marks pages we would be comfortable publishing externally. Display only. */
  visibility: z.enum(['internal', 'shareable']).default('internal'),

  /** Accountable maintainer. Pairs with `updated` for the staleness gate. */
  owner: z.string(),

  updated: z.coerce.date(),

  /**
   * Months before this page is considered stale. Reference material ages
   * slowly; tooling and pricing notes age fast. Defaults to 6.
   */
  reviewCycleMonths: z.number().int().positive().default(6),

  order: z.number().int().default(50),

  related: z.array(z.string()).default([]),
});

// ─── Collections ─────────────────────────────────────────────────────────────
// Section rationale:
//   onboarding  — the path a new person walks, in order
//   methodology — how we work and why (stable, slow-changing)
//   playbooks   — how to execute a phase of an engagement
//   runbooks    — operational procedures and incident response
//   reference   — lookups: glossary, standards, checklists
//   templates   — artifacts you copy from at the start of work
//   decisions   — ADRs; why we settled a question, so we stop relitigating it
//   engagements — per-client working notes, retros, what actually happened

const section = (dir: string) =>
  defineCollection({
    loader: glob({ pattern: '**/*.md', base: `./content/${dir}` }),
    schema: pageSchema,
  });

export const collections = {
  onboarding: section('onboarding'),
  methodology: section('methodology'),
  playbooks: section('playbooks'),
  runbooks: section('runbooks'),
  reference: section('reference'),
  templates: section('templates'),
  decisions: section('decisions'),
  engagements: section('engagements'),
};
