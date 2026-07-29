import type { APIRoute } from 'astro';
import { getAllPages } from '../lib/content';

/**
 * /index.json — retrieval manifest.
 * A ready-made index so an ingesting pipeline never has to scrape HTML.
 * Also powers the client-side search modal.
 */
export const GET: APIRoute = async ({ site }) => {
  const pages = await getAllPages();
  const origin = site?.href.replace(/\/$/, '') ?? '';
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');

  const index = pages.map((page) => {
    const body = page.entry.body ?? '';

    // Extract ATX headings with their computed anchor slugs
    const headings = Array.from(body.matchAll(/^(#{2,4})\s+(.+)$/gm)).map((m) => ({
      depth: m[1]!.length,
      text: m[2]!.trim(),
      slug: slugify(m[2]!.trim()),
    }));

    return {
      url: `${base}${page.path}`,
      absoluteUrl: `${origin}${base}${page.path}`,
      markdownUrl: `${base}${page.path.replace(/\/$/, '')}.md`,
      title: page.title,
      description: page.description,
      section: page.section,
      tags: page.tags,
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
