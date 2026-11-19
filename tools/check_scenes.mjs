// Checks every scene in hooks/scenes/ against what Claude's Svg element draws: the source
// must be one <svg> document of at most 131072 characters (SvgProps.source), or the app
// shows the palette with no scene. Exits non-zero naming each scene over the limit.
// Usage: node --experimental-strip-types tools/check_scenes.mjs
import { readdirSync } from 'node:fs'

const LIMIT = 131072
const dir = new URL('../hooks/scenes/', import.meta.url).pathname
let bad = 0
for (const f of readdirSync(dir).filter(f => f.endsWith('.ts')).sort()) {
  const svg = (await import(`${dir}${f}`)).SCENE
  const ok = svg.length <= LIMIT && svg.startsWith('<svg') && svg.endsWith('</svg>')
  if (!ok) bad++
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${f.replace('.ts', '').padEnd(12)} ${String(svg.length).padStart(7)} chars (${Math.round((100 * svg.length) / LIMIT)}% of ${LIMIT})`)
}
process.exit(bad ? 1 : 0)
