import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { pageSchema } from './lib/page-contract';
export { TAGS } from './lib/page-contract';

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
// ─── Collections ─────────────────────────────────────────────────────────────
// Section rationale:
//   guide       — how to use and maintain this knowledge base itself
//   onboarding  — the path a new person walks, in order
//   methodology — how we work and why (stable, slow-changing)
//   playbooks   — how to execute a phase of an engagement
//   runbooks    — operational procedures and incident response
//   reference   — lookups: glossary, standards, checklists

const section = (dir: string) =>
  defineCollection({
    loader: glob({ pattern: '**/*.md', base: `./content/${dir}` }),
    schema: pageSchema,
  });

export const collections = {
  guide: section('guide'),
  onboarding: section('onboarding'),
  methodology: section('methodology'),
  playbooks: section('playbooks'),
  runbooks: section('runbooks'),
  reference: section('reference'),
};
