import { visit } from 'unist-util-visit';

/**
 * GitHub-style callouts: `> [!NOTE]`, `> [!WARNING]`, etc.
 *
 * Transforms a blockquote whose first paragraph opens with `[!TYPE]` into
 * <aside class="callout callout-note"> with a rendered label. Content stays
 * inside the blockquote children, so the raw Markdown remains readable and
 * degrades gracefully in any renderer that does not support this syntax.
 */
const TYPES = {
  NOTE: 'Note',
  TIP: 'Tip',
  IMPORTANT: 'Important',
  WARNING: 'Warning',
  CAUTION: 'Caution',
};

export default function remarkCallouts() {
  return (tree) => {
    visit(tree, 'blockquote', (node) => {
      const first = node.children[0];
      if (first?.type !== 'paragraph') return;

      const firstText = first.children[0];
      if (firstText?.type !== 'text') return;

      const match = firstText.value.match(/^\[!(\w+)\]\s*\n?/);
      if (!match) return;

      const type = match[1].toUpperCase();
      const label = TYPES[type];
      if (!label) return;

      // Remove the [!TYPE] marker from the text content
      firstText.value = firstText.value.slice(match[0].length);
      if (!firstText.value.trim() && first.children.length === 1) {
        node.children.shift();
      }

      node.data = {
        hName: 'aside',
        hProperties: {
          className: ['callout', `callout-${type.toLowerCase()}`],
          role: type === 'WARNING' || type === 'CAUTION' ? 'alert' : 'note',
        },
      };

      node.children.unshift({
        type: 'paragraph',
        data: { hProperties: { className: ['callout-label'] } },
        children: [{ type: 'text', value: label }],
      });
    });
  };
}
