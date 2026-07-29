import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeExternalLinks from 'rehype-external-links';
import rehypeSlug from 'rehype-slug';
import remarkGfm from 'remark-gfm';
import remarkCallouts from './src/plugins/remark-callouts.mjs';

// Slug renames must ship with a redirect — see redirects.json.
const { redirects } = JSON.parse(readFileSync(new URL('./redirects.json', import.meta.url), 'utf8'));

export default defineConfig({
  base: '/bmtechllc/portal',
  output: 'static',
  trailingSlash: 'always',
  redirects,
  // No sitemap integration: this is an internal tool with no crawlers.
  markdown: {
    remarkPlugins: [remarkGfm, remarkCallouts],
    rehypePlugins: [
      // Must run before autolink so heading IDs exist to link to.
      rehypeSlug,
      [
        rehypeAutolinkHeadings,
        {
          behavior: 'append',
          properties: { class: 'heading-anchor', ariaLabel: 'Link to this section' },
          content: { type: 'text', value: '#' },
        },
      ],
      [
        rehypeExternalLinks,
        {
          target: '_blank',
          rel: ['noopener', 'noreferrer'],
        },
      ],
    ],
    shikiConfig: {
      theme: 'github-dark',
      wrap: true,
    },
    gfm: true,
  },
});
