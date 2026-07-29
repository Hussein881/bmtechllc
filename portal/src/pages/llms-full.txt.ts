import type { APIRoute } from 'astro';
import { getAllPages, SECTION_LABELS } from '../lib/content';

/**
 * /llms-full.txt — full concatenated public corpus in Markdown with URL
 * delimiters, so a tool can ingest everything in a single fetch.
 */
export const GET: APIRoute = async ({ site }) => {
  const pages = await getAllPages();
  const origin = site?.href.replace(/\/$/, '') ?? '';
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');

  const parts: string[] = [
    '# BenchmarkTech LLC — Full Public Corpus',
    '',
    `Generated: ${new Date().toISOString().split('T')[0]}`,
    `Pages: ${pages.length}`,
    '',
  ];

  for (const page of pages) {
    const url = `${origin}${base}${page.path}`;
    const updated = page.updated.toISOString().split('T')[0];

    parts.push(
      '',
      '================================================================================',
      `URL: ${url}`,
      `Title: ${page.title}`,
      `Section: ${SECTION_LABELS[page.section]}`,
      `Updated: ${updated}`,
      `Tags: ${page.tags.join(', ') || 'none'}`,
      '================================================================================',
      '',
      page.entry.body ?? '',
      ''
    );
  }

  return new Response(parts.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
