import { z } from 'zod';
import { TAGS } from './page-fields';
export { TAGS, SECTIONS } from './page-fields';

export const pageSchema = z.object({
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
});

export type PageMetadata = z.infer<typeof pageSchema>;
