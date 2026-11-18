// The localhost gallery /uit-preview serves: every scene at a 16:10 window size, with an
// optional mock of the chat column's glass so you can judge what stays visible.

export interface PreviewTheme {
  id: string
  title: string
  blurb: string
  anchors: Record<string, string>
  roles: Record<string, string>
  tint: string
  opacity: number
  kind: 'scene' | 'still' | 'plain'
  gradient?: string[]
}

export function previewPage(input: { current: string; stillUri: string; themes: PreviewTheme[] }): string {
  const data = JSON.stringify(input).replace(/</g, '\\u003c')

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UIT Themes</title>
<style>
:root { --bg:#05070d; --panel:#0c111c; --line:#1d2536; --text:#e8ecf4; --muted:#8a94a8; --accent:#3f78e0; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--text); font:14px/1.45 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
header { display:flex; align-items:baseline; gap:12px; padding:18px 24px 6px; flex-wrap:wrap; }
h1 { font-size:18px; margin:0; letter-spacing:.02em; }
header p { margin:0; color:var(--muted); }
main { display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:20px; padding:12px 24px 24px; }
@media (max-width:900px) { main { grid-template-columns:1fr; } }
.stage { position:relative; aspect-ratio:16/10; border-radius:10px; overflow:hidden; border:1px solid var(--line); background:#000; }
.stage img, .stage .fill { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; image-rendering:pixelated; }
.glass { position:absolute; top:0; bottom:0; left:20.5%; width:59.5%; backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  display:flex; flex-direction:column; justify-content:flex-end; gap:10px; padding:18px; transition:opacity .2s; }
.glass.hidden { opacity:0; pointer-events:none; }
.msg { max-width:80%; padding:9px 12px; border-radius:10px; font-size:13px; }
.msg.user { align-self:flex-end; }
.msg code { font:12px ui-monospace, SFMono-Regular, Menlo, monospace; }
.prompt { border-radius:10px; padding:10px 12px; font-size:13px; display:flex; justify-content:space-between; }
.bar { display:flex; align-items:center; gap:10px; margin-top:12px; flex-wrap:wrap; }
.bar h2 { font-size:16px; margin:0; }
.bar .blurb { color:var(--muted); flex:1 1 240px; }
button { font:inherit; color:var(--text); background:var(--panel); border:1px solid var(--line); border-radius:7px; padding:6px 10px; cursor:pointer; }
button:hover { border-color:#34405a; }
.cmd { font:13px ui-monospace, Menlo, monospace; background:var(--panel); border:1px solid var(--line); border-radius:7px; padding:6px 10px; }
.list { display:flex; flex-direction:column; gap:8px; }
.item { display:grid; grid-template-columns:72px 1fr; gap:10px; align-items:center; text-align:left; padding:8px; }
.item.on { border-color:var(--accent); }
.item img, .item .thumb { width:72px; height:45px; object-fit:cover; border-radius:4px; image-rendering:pixelated; }
.item b { display:block; font-size:13px; }
.item small { color:var(--muted); }
.sw { display:flex; gap:4px; margin-top:4px; }
.sw i { width:12px; height:12px; border-radius:3px; display:block; border:1px solid #ffffff22; }
.now { font-size:11px; color:var(--accent); margin-left:6px; }
.keys { color:var(--muted); font-size:12px; margin-top:8px; }
.caption { display:none; }
/* ?kiosk: the stage alone, full window, with a caption. ?play=N advances every N seconds; ?glass=0 starts without the chat glass. */
body.kiosk header, body.kiosk aside, body.kiosk .bar, body.kiosk .keys { display:none; }
body.kiosk main { display:block; padding:0; }
body.kiosk .stage { aspect-ratio:auto; height:100vh; border:0; border-radius:0; }
body.kiosk .caption { display:flex; position:absolute; left:20px; bottom:18px; gap:10px; align-items:baseline;
  background:#0009; padding:8px 12px; border-radius:8px; backdrop-filter:blur(6px); }
.caption b { font-size:16px; }
.caption code { font:13px ui-monospace, Menlo, monospace; opacity:.8; }
</style>
</head>
<body>
<header><h1>UIT Themes</h1><p>Scenes for the uit-theme mod, at a 16:10 window. Apply one with the command shown.</p></header>
<main>
  <section>
    <div class="stage" id="stage"></div>
    <div class="bar">
      <h2 id="title"></h2><span class="blurb" id="blurb"></span>
      <span class="cmd" id="cmd"></span>
      <button id="glassBtn" type="button">Hide chat glass (G)</button>
    </div>
    <div class="keys">Left and right arrow keys switch scenes.</div>
  </section>
  <aside class="list" id="list"></aside>
</main>
<script>
const DATA = ${data};
const themes = DATA.themes;
let at = Math.max(0, themes.findIndex(t => t.id === DATA.current));
let glassOn = true;
const $ = id => document.getElementById(id);
const art = (t, cls) => t.kind === 'scene' ? '<img class="' + cls + '" src="' + t.id + '.svg" alt="">'
  : t.kind === 'still' && DATA.stillUri ? '<img class="' + cls + '" src="' + DATA.stillUri + '" alt="">'
  : '<div class="' + (cls || 'fill') + '" style="background:linear-gradient(180deg,' + (t.gradient || [t.anchors['surface-1'], t.anchors['surface-0']]).join(',') + ')"></div>';
const hexA = (hex, a) => hex + Math.round(a * 255).toString(16).padStart(2, '0');
function show() {
  const t = themes[at], a = t.anchors, r = t.roles;
  $('stage').innerHTML = art(t, '') +
    '<div class="glass' + (glassOn ? '' : ' hidden') + '" style="background:' + hexA(t.tint, t.kind === 'scene' ? t.opacity : 0.0) + ';color:' + a['text-primary'] + '">' +
      '<div class="msg user" style="background:' + a['surface-3'] + '">Switch to the ' + t.title + ' theme</div>' +
      '<div class="msg" style="color:' + a['text-secondary'] + '">Done. Run <code style="color:' + r.accent + '">/uit ' + t.id + '</code> any time. ' +
        '<span style="color:' + r.success + '">+12</span> <span style="color:' + r.danger + '">-3</span> <span style="color:' + r.warning + '">warn</span></div>' +
      '<div class="prompt" style="background:' + a['surface-1'] + ';color:' + a['text-muted'] + ';border:1px solid ' + a['surface-3'] + '"><span>Reply...</span><span style="color:' + r.accent + '">Send</span></div>' +
    '</div>' +
    '<div class="caption"><b>' + t.title + '</b><code>/uit ' + t.id + '</code></div>';
  $('title').textContent = t.title;
  $('blurb').textContent = t.blurb;
  $('cmd').textContent = '/uit ' + t.id;
  $('glassBtn').textContent = (glassOn ? 'Hide' : 'Show') + ' chat glass (G)';
  document.querySelectorAll('.item').forEach((el, i) => el.classList.toggle('on', i === at));
  history.replaceState(null, '', '#' + t.id);
}
$('list').innerHTML = themes.map((t, i) => '<button class="item" type="button" data-i="' + i + '">' + art(t, 'thumb') +
  '<span><b>' + t.title + (t.id === DATA.current ? '<span class="now">current</span>' : '') + '</b><small>/uit ' + t.id + '</small>' +
  '<span class="sw">' + ['surface-0', 'surface-3', 'text-primary'].map(k => '<i style="background:' + t.anchors[k] + '"></i>').join('') +
  ['accent', 'success', 'warning', 'danger', 'pro'].map(k => '<i style="background:' + t.roles[k] + '"></i>').join('') + '</span></span></button>').join('');
$('list').addEventListener('click', e => { const b = e.target.closest('.item'); if (b) { at = +b.dataset.i; show(); } });
$('glassBtn').addEventListener('click', () => { glassOn = !glassOn; show(); });
addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') { at = (at + 1) % themes.length; show(); }
  else if (e.key === 'ArrowLeft') { at = (at + themes.length - 1) % themes.length; show(); }
  else if (e.key.toLowerCase() === 'g') { glassOn = !glassOn; show(); }
});
const fromHash = themes.findIndex(t => '#' + t.id === location.hash);
if (fromHash >= 0) at = fromHash;
const query = new URLSearchParams(location.search);
if (query.has('kiosk')) document.body.classList.add('kiosk');
if (query.get('glass') === '0') glassOn = false;
const play = Number(query.get('play')) || 0;
if (play > 0) {
  // Autoplay cycles the animated scenes only.
  setInterval(() => {
    do { at = (at + 1) % themes.length; } while (themes[at].kind !== 'scene');
    show();
  }, play * 1000);
}
show();
</script>
</body>
</html>
`
}
