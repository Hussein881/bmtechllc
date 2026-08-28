/**
 * Treat an otherwise standalone $$...$$ expression as display math.
 *
 * remark-math correctly parses the expression but, when both delimiters are
 * on one line, represents it as inlineMath. The portal's existing documents
 * use this compact form, so promote it before Markdown is converted to HTML.
 */
export default function remarkDoubleDollarDisplayMath() {
  return (tree, file) => {
    walk(tree, (node) => {
      if (node.type !== 'paragraph') return;

      for (const child of node.children ?? []) {
        if (child.type !== 'inlineMath' || !isStandaloneDoubleDollar(child, file.value)) continue;

        if (node.children.length === 1) {
          promoteParagraphToDisplayMath(node, child.value);
        } else {
          // A display formula indented beneath a list item shares its
          // paragraph with the preceding list text. Preserve that structure
          // and make this one math node block-level instead.
          child.data = displayMathData(child.value, false);
        }
      }
    });
  };
}

function isStandaloneDoubleDollar(node, sourceFile) {
  const start = node.position?.start.offset;
  const end = node.position?.end.offset;
  if (typeof start !== 'number' || typeof end !== 'number') return false;

  const source = String(sourceFile);
  const expression = source.slice(start, end);
  if (!/^\$\$[\s\S]*\$\$$/.test(expression)) return false;

  const lineStart = source.lastIndexOf('\n', start - 1) + 1;
  const lineEnd = source.indexOf('\n', end);
  return source.slice(lineStart, start).trim() === '' && source.slice(end, lineEnd === -1 ? source.length : lineEnd).trim() === '';
}

function promoteParagraphToDisplayMath(node, value) {
  node.type = 'math';
  node.value = value;
  node.data = displayMathData(value, true);
  delete node.children;
}

function displayMathData(value, wrapInPre) {
  const code = {
    type: 'element',
    tagName: 'code',
    properties: { className: ['language-math', 'math-display'] },
    children: [{ type: 'text', value }],
  };

  return wrapInPre
    ? { hName: 'pre', hChildren: [code] }
    : { hName: 'code', hProperties: code.properties, hChildren: code.children };
}

function walk(node, visit) {
  visit(node);
  for (const child of node.children ?? []) walk(child, visit);
}
