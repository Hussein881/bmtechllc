import type { APIRoute } from 'astro';
import { getAllPages } from '../lib/content';

/**
 * /index.json — retrieval manifest for internal tooling.
 *
 * On a public site this artifact existed so external crawlers wouldn't have to
 * scrape HTML. Internally its job is different and more valuable: it is the
 * ingestion surface for our own RAG pipelines and agent tooling, which is
 * exactly the kind of reusable asset worth extracting from this build.
 *
 * Consumers get status and staleness so a pipeline can decide whether to trust
 * or down-rank a page — something an external index could never expose.
 */
export const GET: APIRoute = async () => {
  const pages = await getAllPages();
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');

  const index = pages.map((page) => {
    const body = page.entry.body ?? '';

    const headings = Array.from(body.matchAll(/^(#{2,4})\s+(.+)$/gm)).map((m) => ({
      depth: m[1]!.length,
      text: m[2]!.trim(),
      slug: slugify(m[2]!.trim()),
    }));

    return {
      url: `${base}${page.path}`,
      markdownUrl: `${base}${page.path.replace(/\/$/, '')}.md`,
      title: page.title,
      description: page.description,
      section: page.section,
      tags: page.tags,

      // Trust signals — let an ingesting pipeline weight or filter
      status: page.status,
      visibility: page.visibility,
      isStale: page.isStale,
      monthsSinceUpdate: page.monthsSinceUpdate,

      updated: page.updated.toISOString().split('T')[0],
      owner: page.owner,
      headings,
      wordCount: body.split(/\s+/).filter(Boolean).length,
    };
  });

  return new Response(JSON.stringify(index, null, 2), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
};

/** Matches Astro's default GitHub-style heading slugger. */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}
