import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import rehypeExternalLinks from 'rehype-external-links';
import rehypeSlug from 'rehype-slug';
import remarkGfm from 'remark-gfm';

export default defineConfig({
  site: 'https://Hussein881.github.io',
  base: '/bmtechllc/portal',
  output: 'static',
  trailingSlash: 'always',
  integrations: [sitemap()],
  markdown: {
    remarkPlugins: [remarkGfm],
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
