import type { APIRoute } from 'astro';
import { getAllPages, SECTIONS, SECTION_LABELS } from '../lib/content';

/**
 * /llms.txt — curated map for crawler-side agents.
 * Firm one-liner + section list + per-page "title — description — url".
 */
export const GET: APIRoute = async ({ site }) => {
  const pages = await getAllPages();
  const origin = site?.href.replace(/\/$/, '') ?? '';
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const url = (path: string) => `${origin}${base}${path}`;

  const lines: string[] = [
    '# BenchmarkTech LLC',
    '',
    '> AI consulting for mid-market organizations: readiness assessments, production RAG systems, and embedded technical advisory.',
    '',
    'This portal is the public knowledge base for BenchmarkTech methodology, playbooks, and reference material.',
    'Full corpus in one file: ' + url('/llms-full.txt'),
    'Structured index: ' + url('/index.json'),
    '',
  ];

  for (const section of SECTIONS) {
    const sectionPages = pages.filter((p) => p.section === section);
    if (sectionPages.length === 0) continue;

    lines.push(`## ${SECTION_LABELS[section]}`, '');
    for (const page of sectionPages) {
      lines.push(`- [${page.title}](${url(page.path)}): ${page.description}`);
    }
    lines.push('');
  }

  return new Response(lines.join('\n'), {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
