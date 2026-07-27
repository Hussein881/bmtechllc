// Proof gate (DESIGN_BRIEF.md §11.4): fails the build if unshippable placeholder
// content reaches source. Mechanical enforcement of "nothing ships that BMTech
// cannot substantiate on demand."
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'

const ROOT = new URL('..', import.meta.url).pathname
const SCAN_DIRS = ['src', 'public', 'index.html']
const EXTS = new Set(['.ts', '.tsx', '.css', '.html', '.svg', '.json', '.txt', '.md'])
const PATTERNS = [
  { re: /\{\{/, label: 'double-brace placeholder' },
  { re: /PLACEHOLDER/i, label: 'placeholder marker' },
  { re: /lorem ipsum/i, label: 'lorem ipsum' },
  // A reserved-TLD address or domain is a stand-in contact detail: it looks
  // real in a screenshot and reaches nobody. Publish the address that works or
  // publish none — see README.md, "Launch blockers".
  { re: /\.example\b/i, label: 'stand-in domain' },
  // Any hard-coded mail recipient. The assessment form deliberately opens
  // `mailto:?subject=`, with the recipient left empty until BMTech supplies one.
  { re: /mailto:[^"'`?\s>]/i, label: 'hard-coded email recipient' },
]

const failures = []

function scan(path) {
  const stats = statSync(path)
  if (stats.isDirectory()) {
    for (const entry of readdirSync(path)) scan(join(path, entry))
    return
  }
  if (!EXTS.has(extname(path))) return
  const text = readFileSync(path, 'utf8')
  text.split('\n').forEach((line, i) => {
    for (const { re, label } of PATTERNS) {
      if (re.test(line)) failures.push(`${path}:${i + 1} — ${label}: ${line.trim().slice(0, 90)}`)
    }
  })
}

for (const target of SCAN_DIRS) {
  try {
    scan(join(ROOT, target))
  } catch {
    // Optional target absent at this stage — nothing to scan.
  }
}

if (failures.length > 0) {
  console.error('Proof gate failed. Placeholder content must not ship:\n')
  for (const failure of failures) console.error('  ' + failure)
  process.exit(1)
}

console.log('Proof gate passed: no placeholder content found.')
