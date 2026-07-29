import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// ─── Controlled tag vocabulary ────────────────────────────────────────────────
// Adding a tag = one-line PR here. Free-form tags are a build error.
export const TAGS = [
  // Practice areas
  'ai-strategy',
  'ai-readiness',
  'data-engineering',
  'machine-learning',
  'rag',
  'llm',
  'automation',
  'process-improvement',
  // Delivery phases
  'discovery',
  'delivery',
  'handoff',
  'stakeholder-management',
  // Industries
  'financial-services',
  'healthcare',
  'retail',
  'manufacturing',
  // Content types
  'playbook',
  'template',
  'checklist',
  'case-study',
  'article',
  'reference',
  // Audiences
  'technical',
  'executive',
  'mid-market',
] as const;

type Tag = typeof TAGS[number];

// ─── Schema ──────────────────────────────────────────────────────────────────

const pageSchema = z.object({
  title: z.string(),
  description: z.string().min(20, 'Description must be at least 20 chars — it is the retrieval abstract.'),
  tags: z.array(z.enum(TAGS as [Tag, ...Tag[]])).default([]),
  audience: z.enum(['public', 'client', 'internal']),
  status: z.enum(['draft', 'published', 'archived']),
  owner: z.string(),
  updated: z.coerce.date(),
  order: z.number().int().default(50),
  related: z.array(z.string()).default([]),
});

// ─── Collections ─────────────────────────────────────────────────────────────

const services = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/services' }),
  schema: pageSchema,
});

const methodology = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/methodology' }),
  schema: pageSchema,
});

const playbooks = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/playbooks' }),
  schema: pageSchema,
});

const reference = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/reference' }),
  schema: pageSchema,
});

const insights = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/insights' }),
  schema: pageSchema,
});

const about = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './content/about' }),
  schema: pageSchema,
});

export const collections = {
  services,
  methodology,
  playbooks,
  reference,
  insights,
  about,
};
