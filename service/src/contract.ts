import { z } from 'zod';
import { SECTIONS, TAGS } from './page-fields.js';

export const MAX_MARKDOWN_BYTES = 100_000;
export const createPageSchema = z.object({
  title: z.string().trim().min(1).max(160),
  description: z.string().trim().min(20, 'Description must be at least 20 chars — it is the retrieval abstract.').max(500),
  tags: z.array(z.enum(TAGS)).max(8).default([]),
  status: z.enum(['draft', 'published', 'archived']).default('draft'),
  visibility: z.enum(['internal', 'shareable']).default('internal'),
  owner: z.string().trim().min(1).max(80),
  updated: z.coerce.date(),
  reviewCycleMonths: z.number().int().positive().max(120).default(6),
  order: z.number().int().min(-10000).max(10000).default(50),
  related: z.array(z.string().trim().min(1).max(160)).max(12).default([]),
  section: z.enum(SECTIONS),
  body: z.string().trim().min(1, 'Markdown is required.').max(MAX_MARKDOWN_BYTES, 'Markdown is too large.'),
});
export type CreatePageInput = z.infer<typeof createPageSchema>;

export function slugify(title: string): string {
  const slug = title.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '').slice(0, 80);
  if (!slug || slug.includes('..') || slug.includes('/') || slug.includes('\\')) throw new Error('Title does not produce a safe page slug.');
  return slug;
}
export function assertSafeMarkdown(body: string): void {
  if (/<\/?[a-z][^>]*>/i.test(body)) throw new Error('Raw HTML is not allowed in Markdown.');
  if (new TextEncoder().encode(body).byteLength > MAX_MARKDOWN_BYTES) throw new Error('Markdown is too large.');
}
const quote = (value: string) => JSON.stringify(value);
export function renderMarkdown(input: CreatePageInput): string {
  const date = input.updated.toISOString().slice(0, 10);
  return `---\ntitle: ${quote(input.title)}\ndescription: ${quote(input.description)}\ntags: [${input.tags.map(quote).join(', ')}]\nstatus: ${input.status}\nvisibility: ${input.visibility}\nowner: ${quote(input.owner)}\nupdated: ${date}\nreviewCycleMonths: ${input.reviewCycleMonths}\norder: ${input.order}\nrelated: [${input.related.map(quote).join(', ')}]\n---\n\n${input.body.trim()}\n`;
}
