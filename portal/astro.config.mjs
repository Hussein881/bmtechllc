import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeExternalLinks from 'rehype-external-links';
import rehypeKatex from 'rehype-katex';
import rehypeSlug from 'rehype-slug';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import remarkCallouts from './src/plugins/remark-callouts.mjs';
import remarkDoubleDollarDisplayMath from './src/plugins/remark-double-dollar-display-math.mjs';

// Slug renames must ship with a redirect — see redirects.json.
const { redirects } = JSON.parse(readFileSync(new URL('./redirects.json', import.meta.url), 'utf8'));

export default defineConfig({
  base: '/bmtechllc/portal',
  output: 'static',
  trailingSlash: 'always',
  redirects,
  // No sitemap integration: this is an internal tool with no crawlers.
  markdown: {
    // Parse $...$ and $$...$$ before the Markdown-to-HTML transform so GFM
    // cannot mistake TeX underscores for emphasis.
    remarkPlugins: [remarkGfm, remarkMath, remarkDoubleDollarDisplayMath, remarkCallouts],
    rehypePlugins: [
      // Render parsed TeX during the static build; published pages need no
      // client-side math renderer.
      rehypeKatex,
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
