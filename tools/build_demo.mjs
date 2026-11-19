// Builds drafts/demo/index.html: a mock of the desktop app's Code tab with the UIT themes,
// scripted for the README demo. A conversation sits in the glass chat column; /uit commands
// are typed into the prompt and each one switches the scene and the palette. The theme list
// (titles, blurbs, glass tint) is read from hooks/register.tsx; palettes and scenes are
// imported from hooks/. Record it with tools/record_demo.py.
// Usage: node --experimental-strip-types tools/build_demo.mjs
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'

const root = new URL('../', import.meta.url).pathname
const out = `${root}drafts/demo/`
mkdirSync(out, { recursive: true })
const P = await import(`${root}hooks/palettes.ts`)
const src = readFileSync(`${root}hooks/register.tsx`, 'utf8')
const field = (block, key) => {
  const m = block.match(new RegExp(`${key}: (?:(['"])(.*?)\\1|([\\w.#]+))`))
  return m && (m[2] ?? m[3])
}
const THEMES = []
for (const block of src.split(/\n  \{\n/).slice(1)) {
  const id = field(block, 'id')
  if (!id) continue
  const svg = (await import(`${root}hooks/scenes/${id}.ts`)).SCENE
  writeFileSync(`${out}${id}.svg`, svg)
  const p = P[field(block, 'palette')]
  const m = p.dark ?? p.light
  THEMES.push({ id, title: field(block, 'title'), blurb: field(block, 'blurb'), tint: field(block, 'tint'), opacity: Number(field(block, 'opacity')), a: m.gray.anchors, r: p.roles, g: m.git })
}
console.log(THEMES.map(t => t.id).join(' '))

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>UIT Themes demo</title>
<style>
:root { --s0:#04102a; --s1:#081734; --s2:#0c1d3e; --s3:#112447; --t0:#eaf0fb; --t1:#c3cfe6; --t2:#94a6c8;
  --accent:#3f78e0; --ok:#26a146; --bad:#ee583a; --warn:#f6c445; --tint:#04102aB8; --add:#52cf74; --del:#f07a5f; }
* { box-sizing:border-box; }
html, body { margin:0; height:100%; overflow:hidden; background:#000; }
body { font:14px/1.5 ui-sans-serif, -apple-system, "SF Pro Text", system-ui, sans-serif; color:var(--t0); }
.win, .win * { transition: background-color .7s ease, color .7s ease, border-color .7s ease; }
.win { position:fixed; inset:0; display:flex; flex-direction:column; }
.title { height:38px; flex:none; display:flex; align-items:center; gap:8px; padding:0 14px; background:var(--s1); border-bottom:1px solid var(--s3); position:relative; z-index:3; }
.dot { width:12px; height:12px; border-radius:50%; }
.title .name { margin-left:14px; font-size:13px; color:var(--t1); font-weight:600; }
.title .tabs { margin-left:auto; display:flex; gap:4px; font-size:12px; color:var(--t2); }
.title .tabs span { padding:3px 10px; border-radius:6px; }
.title .tabs .on { background:var(--s3); color:var(--t0); }
.body { position:relative; flex:1; overflow:hidden; }
.bd { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0; transition:opacity .9s ease; }
.bd.on { opacity:1; }
.rail { position:absolute; left:0; top:0; bottom:0; width:54px; background:var(--s1); border-right:1px solid var(--s3); display:flex; flex-direction:column; align-items:center; gap:14px; padding-top:14px; z-index:2; }
.rail i { width:28px; height:28px; border-radius:8px; display:block; border:1.5px solid var(--t2); opacity:.75; }
.rail i.plus { border-radius:50%; position:relative; }
.rail i.plus::before, .rail i.plus::after { content:''; position:absolute; left:50%; top:50%; background:var(--t1); transform:translate(-50%,-50%); }
.rail i.plus::before { width:12px; height:1.5px; } .rail i.plus::after { width:1.5px; height:12px; }
.rail i.sq { border-radius:6px; } .rail i.ln { border:0; border-top:1.5px solid var(--t2); border-bottom:1.5px solid var(--t2); height:12px; margin:8px 0; }
.chat { position:absolute; top:0; bottom:0; left:21%; right:21%; backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); background:var(--tint); display:flex; flex-direction:column; z-index:1; }
.log { flex:1; overflow:hidden; padding:28px 40px 8px; display:flex; flex-direction:column; justify-content:flex-end; gap:14px; }
.msg { animation:in .35s ease both; }
@keyframes in { from { opacity:0; transform:translateY(8px); } }
.user { align-self:flex-end; background:var(--s3); color:var(--t0); padding:9px 14px; border-radius:14px; max-width:78%; }
.asst { color:var(--t0); max-width:92%; }
.asst p { margin:0 0 6px; }
code { font:12.5px ui-monospace, "SF Mono", Menlo, monospace; color:var(--accent); }
.tool { display:flex; gap:10px; align-items:center; font:12.5px ui-monospace, Menlo, monospace; color:var(--t1); background:var(--s2); border:1px solid var(--s3); border-radius:8px; padding:7px 10px; width:max-content; }
.tool .ok { color:var(--ok); } .tool .add { color:var(--add); } .tool .del { color:var(--del); }
.cmd { font:12.5px ui-monospace, Menlo, monospace; color:var(--t2); }
.cmd .in { color:var(--t1); }
.cmd .outl { white-space:pre-wrap; margin-top:3px; padding-left:12px; border-left:2px solid var(--accent); color:var(--t1); }
.prompt-wrap { position:relative; padding:0 28px 22px; }
.pop { position:absolute; left:28px; right:28px; bottom:calc(100% - 14px); background:var(--s2); border:1px solid var(--s3); border-radius:10px; padding:6px; font-size:13px; opacity:0; transform:translateY(6px); transition:opacity .15s, transform .15s; pointer-events:none; box-shadow:0 10px 30px #0007; }
.pop.on { opacity:1; transform:none; }
.pop div { display:flex; gap:14px; padding:6px 10px; border-radius:6px; }
.pop div.sel { background:var(--s3); }
.pop b { font:600 12.5px ui-monospace, Menlo, monospace; color:var(--t0); min-width:96px; }
.pop span { color:var(--t2); }
.prompt { background:var(--s1); border:1px solid var(--s3); border-radius:14px; padding:12px 14px 10px; }
.field { min-height:22px; color:var(--t0); font-size:14px; }
.field .ph { color:var(--t2); }
.field .caret { display:inline-block; width:1.5px; height:17px; background:var(--accent); vertical-align:-3px; margin-left:1px; animation:blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity:0; } }
.row { display:flex; align-items:center; gap:10px; margin-top:8px; font-size:12px; color:var(--t2); }
.row .send { margin-left:auto; width:28px; height:28px; border-radius:8px; background:var(--accent); display:grid; place-items:center; color:#fff; font-weight:700; }
.chip { border:1px solid var(--s3); border-radius:6px; padding:2px 8px; }
</style></head>
<body>
<div class="win">
  <div class="title"><i class="dot" style="background:#ff5f57"></i><i class="dot" style="background:#febc2e"></i><i class="dot" style="background:#28c840"></i>
    <span class="name">uit-campus-app</span><span class="tabs"><span>Chat</span><span class="on">Code</span></span></div>
  <div class="body" id="body">
    ${THEMES.map((t, i) => `<img class="bd${i === 0 ? ' on' : ''}" data-id="${t.id}" src="${t.id}.svg" alt="">`).join('')}
    <div class="rail"><i class="plus"></i><i class="sq"></i><i class="ln"></i><i class="sq" style="border-radius:50%"></i></div>
    <div class="chat">
      <div class="log" id="log">
        <div class="user msg">Make the course schedule page load faster</div>
        <div class="asst msg"><p>The schedule was fetching every section one request at a time. I batched them into a single query and cached the room lookups.</p></div>
        <div class="tool msg"><span class="ok">&#10003;</span> Edit src/schedule.ts <span class="add">+42</span> <span class="del">-17</span></div>
        <div class="asst msg"><p>Load time drops from 2.4s to 310ms. Tests pass.</p></div>
      </div>
      <div class="prompt-wrap">
        <div class="pop" id="pop"><div class="sel"><b>/uit</b><span>UIT themes: ${THEMES.map(t => t.id).join(', ')}</span></div><div><b>/uit-preview</b><span>Open a localhost gallery of the UIT theme scenes</span></div></div>
        <div class="prompt"><div class="field" id="field"><span class="ph">Reply...</span></div>
          <div class="row"><span class="chip">Opus 5.5</span><span>uit-campus-app</span><span class="send">&#8593;</span></div></div>
      </div>
    </div>
  </div>
</div>
<script>
const THEMES = ${JSON.stringify(THEMES)};
const $ = id => document.getElementById(id);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const root = document.documentElement.style;
function apply(t) {
  const v = { s0:t.a['surface-0'], s1:t.a['surface-1'], s2:t.a['surface-2'], s3:t.a['surface-3'], t0:t.a['text-primary'], t1:t.a['text-secondary'], t2:t.a['text-muted'],
    accent:t.r.accent, ok:t.r.success, bad:t.r.danger, warn:t.r.warning, add:t.g.added, del:t.g.removed,
    tint: t.tint + Math.round(t.opacity * 255).toString(16).padStart(2, '0') };
  for (const [k, c] of Object.entries(v)) root.setProperty('--' + k, c);
  document.querySelectorAll('.bd').forEach(img => img.classList.toggle('on', img.dataset.id === t.id));
}
const field = $('field');
const show = text => { field.innerHTML = text ? text.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '<span class="caret"></span>' : '<span class="ph">Reply...</span>'; };
async function type(text, speed = 70) {
  for (let i = 1; i <= text.length; i++) {
    show(text.slice(0, i));
    $('pop').classList.toggle('on', text.slice(0, i).startsWith('/') && !text.slice(0, i).includes(' '));
    await sleep(speed + Math.random() * 40);
  }
}
function add(html) {
  const log = $('log');
  log.insertAdjacentHTML('beforeend', html);
  while (log.children.length > 9) log.firstElementChild.remove();
}
async function command(id, speed) {
  const t = THEMES.find(x => x.id === id);
  await type('/uit ' + id, speed);
  await sleep(450);
  $('pop').classList.remove('on');
  show('');
  add('<div class="cmd msg"><span class="in">&gt; /uit ' + id + '</span><div class="outl">uit-theme: UIT theme: ' + t.title + '. ' + t.blurb + '.</div></div>');
  await sleep(250);
  apply(t);
}
async function run() {
  apply(THEMES[0]);
  await sleep(1600);
  await command('monsoon', 80);
  await sleep(2600);
  await command('metro', 50);
  await sleep(2200);
  add('<div class="user msg">Nice. Add a dark mode toggle to settings too</div>');
  await sleep(600);
  add('<div class="tool msg"><span class="ok">&#10003;</span> Edit src/settings.tsx <span class="add">+18</span> <span class="del">-2</span></div>');
  await sleep(450);
  add('<div class="asst msg"><p>Added <code>useTheme()</code> and a toggle under Appearance.</p></div>');
  await sleep(1000);
  for (const id of ['silicon', 'tet', 'trungthu', 'exam', 'dawn', 'jobfair', 'afterschool', 'graduation']) { await command(id, 45); await sleep(2500); }
  await command('teachers', 45);
  await sleep(3800);
  document.title = 'done';
}
async function waitGo() {
  if (location.search.includes('now')) return;
  for (;;) { try { const r = await fetch('go?' + Date.now(), { cache:'no-store' }); if (r.ok) return; } catch {} await sleep(100); }
}
apply(THEMES[0]);
waitGo().then(run);
</script>
</body></html>
`
writeFileSync(`${out}index.html`, html)
console.log('wrote', `${out}index.html`)
