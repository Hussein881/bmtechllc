import type { APIRoute } from 'astro';
import { getAllPages } from '../lib/content';

/**
 * Raw Markdown per page: /{slug}.md
 * Canonical plain-text version — also powers the "Copy as Markdown" button.
 */
export async function getStaticPaths() {
  const pages = await getAllPages();

  return pages.map((page) => ({
    params: { slug: page.path.replace(/^\/|\/$/g, '') },
    props: { page },
  }));
}

export const GET: APIRoute = ({ props }) => {
  const { page } = props as { page: Awaited<ReturnType<typeof getAllPages>>[number] };
  const body = page.entry.body ?? '';
  const updated = page.updated.toISOString().split('T')[0];

  const header = [
    `# ${page.title}`,
    '',
    `> ${page.description}`,
    '',
    `Section: ${page.section} | Updated: ${updated} | Tags: ${page.tags.join(', ') || 'none'}`,
    '',
    '---',
    '',
  ].join('\n');

  // Strip the leading H1 from the body — it is already in the header above.
  const stripped = body.replace(/^#\s+.+\n+/, '');

  return new Response(header + stripped, {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
