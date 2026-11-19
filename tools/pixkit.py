"""Paint pixel scenes in code and give every part of them its own slow motion.

A Canvas is a sparse map of pixels. Shapes paint onto it; each canvas becomes stroked 1px
rows (scenekit.paths), the encoding the other scenes use. The motion helpers wrap those
rows in groups that drift, sway, cross-fade or step through frames, all in CSS.
"""

from __future__ import annotations

import math
import random

from scenekit import H, W, Px, Scene, paths

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def mix(a: str, b: str, t: float) -> str:
    pa = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % round(x + (y - x) * t) for x, y in zip(pa, pb))


class Canvas:
    def __init__(self, wrap: bool = False):
        self.px: dict[Px, str] = {}
        self.wrap = wrap  # x wraps at W, for layers that scroll round
        self.seams: list[tuple[int, int, int, str]] = []  # (x, y, w, colour): 2 rows of 50% checker

    # ------------------------------------------------------------ points

    def set(self, x: float, y: float, c: str) -> None:
        x, y = math.floor(x), math.floor(y)
        if self.wrap:
            x %= W
        if -W <= x < 2 * W and -H <= y < 2 * H:
            self.px[(x, y)] = c

    def get(self, x: int, y: int) -> str | None:
        return self.px.get((x % W if self.wrap else x, y))

    def rect(self, x: float, y: float, w: int, h: int, c: str) -> None:
        x, y = math.floor(x), math.floor(y)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x: int, y: int, n: int, c: str) -> None:
        self.rect(x, y, n, 1, c)

    def vline(self, x: int, y: int, n: int, c: str) -> None:
        self.rect(x, y, 1, n, c)

    def line(self, x0: float, y0: float, x1: float, y1: float, c: str) -> None:
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(int(n) + 1):
            t = i / n
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: str, top_only: bool = False) -> None:
        for y in range(math.floor(cy - ry), math.ceil(cy + ry) + 1):
            if top_only and y > cy:
                break
            for x in range(math.floor(cx - rx), math.ceil(cx + rx) + 1):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.set(x, y, c)

    def poly(self, pts: list[tuple[float, float]], c: str) -> None:
        """Even-odd fill sampled at pixel centres."""
        ys = [p[1] for p in pts]
        for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
            yc = y + 0.5
            xs = []
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 <= yc < y1) or (y1 <= yc < y0):
                    xs.append(x0 + (yc - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(math.ceil(a - 0.5), math.floor(b - 0.5) + 1):
                    self.set(x, y, c)

    def grad(self, x0: int, y0: int, x1: int, y1: int, stops: list[tuple[int, str]], step: int = 9) -> None:
        """Vertical gradient through colour stops in solid bands; each seam is a 2-row checker
        of the next band's colour (drawn as a pattern, so it costs one rect)."""
        prev = None
        for y in range(y0, y1):
            if y <= stops[0][0]:
                col = stops[0][1]
            elif y >= stops[-1][0]:
                col = stops[-1][1]
            else:
                for (sa, ca), (sb, cb) in zip(stops, stops[1:]):
                    if sa <= y < sb:
                        k = max(1, (sb - sa) // step)
                        col = mix(ca, cb, math.floor((y - sa) / (sb - sa) * k) / k)
                        break
            self.hline(x0, y, x1 - x0, col)
            if prev is not None and col != prev and y - 2 >= y0:
                self.seams.append((x0, y - 2, x1 - x0, col))
            prev = col

    def sprite(self, art: list[str], cmap: dict[str, str], x: int, y: int, flip: bool = False) -> None:
        for dy, row in enumerate(art):
            row = row[::-1] if flip else row
            for dx, ch in enumerate(row):
                if ch not in ". ":
                    self.set(x + dx, y + dy, cmap[ch])

    def merge(self, other: "Canvas") -> "Canvas":
        self.px.update(other.px)
        return self

    def recolor(self, fn) -> "Canvas":
        out = Canvas(self.wrap)
        out.px = {p: fn(p, c) for p, c in self.px.items()}
        return out

    def svg(self, attrs: str = "", clip: bool = True) -> str:
        """Pixel rows as paths; `clip` drops what lies well off the screen (not for
        sprites drawn around a local origin)."""
        px = {p: c for p, c in self.px.items() if -8 <= p[0] < W + 8 and -8 <= p[1] < H + 8} if clip else self.px
        out = paths(px, attrs)
        for col in dict.fromkeys(c for *_, c in self.seams):
            pid = f"ck{col[1:]}"
            out += (
                f'<defs><pattern id="{pid}" width="2" height="2" patternUnits="userSpaceOnUse">'
                f'<rect width="1" height="1" fill="{col}"/><rect x="1" y="1" width="1" height="1" fill="{col}"/></pattern></defs>'
            )
        out += "".join(f'<rect x="{x}" y="{y}" width="{w}" height="2" fill="url(#ck{c[1:]})"/>' for x, y, w, c in self.seams)
        return out


# ---------------------------------------------------------------- shapes


def cloud(c: Canvas, x: int, y: int, w: int, rng: random.Random, light: str, mid: str, shade: str, h: int | None = None) -> None:
    """A cumulus: overlapping puffs over a flat base, lit from above."""
    h = h or max(5, w // 3)
    puffs = []
    n = max(2, w // 9)
    for i in range(n):
        px = x + (i + 0.5) * w / n + rng.uniform(-2, 2)
        r = rng.uniform(0.55, 1) * h * (1.1 if 0 < i < n - 1 else 0.75)
        puffs.append((px, y - r * 0.55, r))
    pts: set[Px] = set()
    for px, py, r in puffs:
        for yy in range(math.floor(py - r), y + 1):
            for xx in range(math.floor(px - r * 1.2), math.ceil(px + r * 1.2) + 1):
                if ((xx + 0.5 - px) / (r * 1.2)) ** 2 + ((yy + 0.5 - py) / r) ** 2 <= 1:
                    pts.add((xx, yy))
    top = min(p[1] for p in pts)
    span = max(1, y - top)
    for xx, yy in pts:
        t = (yy - top) / span
        col = light if t < 0.5 else mid if t < 0.8 else shade
        if 0.45 < t < 0.55 and BAYER[yy % 4][xx % 4] > 8:
            col = mid
        c.set(xx, yy, col)


def streak(c: Canvas, x: int, y: int, w: int, top: str, bottom: str) -> None:
    """A long thin dusk cloud, brighter underneath."""
    c.hline(x + 4, y, w - 10, top)
    c.hline(x, y + 1, w, bottom)
    if w > 24:
        c.hline(x + 8, y + 2, w - 20, bottom)


def canopy(c: Canvas, cx: float, cy: float, r: float, rng: random.Random, dark: str, mid: str, light: str, blobs: int = 6) -> set[Px]:
    """A rounded tree crown of a few blobs, light from the upper left. Returns its pixels."""
    centres = [(cx, cy, r)] + [
        (cx + rng.uniform(-r, r) * 0.8, cy + rng.uniform(-r, r * 0.4) * 0.7, r * rng.uniform(0.5, 0.75)) for _ in range(blobs)
    ]
    pts: set[Px] = set()
    for bx, by, br in centres:
        for y in range(math.floor(by - br), math.ceil(by + br) + 1):
            for x in range(math.floor(bx - br), math.ceil(bx + br) + 1):
                if (x + 0.5 - bx) ** 2 + (y + 0.5 - by) ** 2 <= br * br:
                    pts.add((x, y))
    for x, y in pts:
        # Light falls on the upper left of each blob.
        k = min(((x + 0.5 - bx) + (y + 0.5 - by)) / br for bx, by, br in centres if (x + 0.5 - bx) ** 2 + (y + 0.5 - by) ** 2 <= br * br)
        col = light if k < -0.5 else mid if k < 0.35 else dark
        if -0.65 < k < -0.35 and BAYER[y % 4][x % 4] > 7:
            col = mid
        c.set(x, y, col)
    return pts


def leaf_glints(pts: set[Px], rng: random.Random, color: str, share: float, below: float | None = None) -> Canvas:
    """A random scatter of bright leaves over a crown, for rustling."""
    out = Canvas()
    for x, y in pts:
        if rng.random() < share and (below is None or y < below):
            out.set(x, y, color)
    return out


def palm(c: Canvas, x: float, base: int, h: int, lean: float, trunk: str, trunk_dark: str, dark: str, light: str, sway: float = 0) -> None:
    """A coconut palm: a ringed trunk curving up, fronds drooping from the crown."""
    tx = ty = 0.0
    for i in range(h):
        t = i / h
        tx = x + lean * t * t * h * 0.25
        ty = base - i
        c.set(tx, ty, trunk)
        c.set(tx + 1, ty, trunk_dark if i % 3 else trunk)
    for k, a in enumerate((-2.8, -2.35, -1.9, -1.25, -0.75, -0.3, 0.15)):
        a += sway * (0.6 if abs(a + 1.5) > 0.8 else 0.3)
        ln = h * (0.42 if abs(a + 1.5) < 0.4 else 0.55)
        for i in range(int(ln)):
            t = i / ln
            fx = tx + 0.5 + math.cos(a) * i
            fy = ty + math.sin(a) * i + 7 * t * t
            c.set(fx, fy, light if k % 2 else dark)
            c.set(fx, fy + 1, dark)
            if 0.25 < t < 0.85:
                c.set(fx, fy + 2, dark if (i % 2) else light)


def window_grid(c: Canvas, x: int, y: int, cols: int, rows: int, cw: int, ch: int, gx: int, gy: int, colors, rng: random.Random) -> list[tuple[int, int, int, int]]:
    """Rows of windows; colours picked per window. Returns each window's rect."""
    out = []
    for r in range(rows):
        for k in range(cols):
            wx, wy = x + k * (cw + gx), y + r * (ch + gy)
            col = colors(rng) if callable(colors) else colors
            c.rect(wx, wy, cw, ch, col)
            out.append((wx, wy, cw, ch))
    return out


FONT = {
    "0": ["0110", "1001", "1001", "1001", "1001", "1001", "0110"],
    "1": ["0010", "0110", "0010", "0010", "0010", "0010", "0111"],
    "2": ["0110", "1001", "0001", "0010", "0100", "1000", "1111"],
    "/": ["0001", "0001", "0010", "0010", "0100", "0100", "1000"],
}


def text_px(s: str, x: int, y: int, scale: int = 1) -> list[Px]:
    out = []
    cx = x
    for ch in s:
        g = FONT[ch]
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == "1":
                    for sx in range(scale):
                        for sy in range(scale):
                            out.append((cx + gx * scale + sx, y + gy * scale + sy))
        cx += (len(g[0]) + 1) * scale
    return out


class Motion:
    """CSS for the shared motions, added to a scene once."""

    CSS = [
        ".tw{animation:tw ease-in-out infinite alternate}@keyframes tw{from{opacity:.15}to{opacity:1}}",
        ".br{animation:br ease-in-out infinite alternate}@keyframes br{from{opacity:.35}to{opacity:.85}}",
        ".xa{animation:xa ease-in-out infinite alternate}@keyframes xa{0%,38%{opacity:1}62%,100%{opacity:0}}",
        ".xb{animation:xb ease-in-out infinite alternate}@keyframes xb{0%,38%{opacity:0}62%,100%{opacity:1}}",
        ".sx{animation:sx linear infinite}@keyframes sx{from{transform:translateX(0)}to{transform:translateX(-384px)}}",
        ".sxr{animation:sxr linear infinite}@keyframes sxr{from{transform:translateX(-384px)}to{transform:translateX(0)}}",
        ".bob{animation:bob ease-in-out infinite alternate}@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-1px)}}",
        ".sw{animation:sw ease-in-out infinite alternate}@keyframes sw{from{transform:translateX(-2px)}to{transform:translateX(2px)}}",
        ".la,.lb{animation:st .56s steps(1) infinite}.lb{animation-delay:-.28s}@keyframes st{50%{opacity:0}}",
        ".fall{animation:fall linear infinite}@keyframes fall{0%{transform:translate(0,0);opacity:0}8%{opacity:1}85%{opacity:.9}100%{transform:translate(var(--dx,8px),var(--d,40px));opacity:0}}",
        ".rise{animation:rise linear infinite}@keyframes rise{0%{transform:translate(0,0);opacity:0}10%{opacity:1}75%{opacity:.85}100%{transform:translate(var(--dx,0px),var(--d,-60px));opacity:0}}",
        ".off{animation:off ease-in-out infinite}@keyframes off{0%,36%{opacity:0}44%,82%{opacity:1}90%,100%{opacity:0}}",
        ".mote{animation:mote linear infinite}@keyframes mote{0%{transform:translate(0,0);opacity:0}20%{opacity:.7}80%{opacity:.6}100%{transform:translate(var(--dx,20px),var(--d,-30px));opacity:0}}",
    ]

    def __init__(self, scene: Scene):
        self.s = scene
        self.n = 0
        scene.style(*self.CSS)

    def _name(self, p: str) -> str:
        self.n += 1
        return f"{p}{self.n}"

    def st(self, cls: str, dur: float, delay: float, extra: str = "") -> str:
        return f'class="{cls}" style="animation-duration:{dur}s;animation-delay:-{round(delay, 2)}s{";" + extra if extra else ""}"'

    def add(self, svg: str) -> None:
        self.s.add(svg)

    def static(self, c: Canvas) -> None:
        self.add(c.svg())

    def scroll(self, c: Canvas, dur: float, delay: float = 0, right: bool = False, opacity: float = 1) -> None:
        """A wrapped layer that slides round forever."""
        body = c.svg()
        op = f' opacity="{opacity}"' if opacity < 1 else ""
        self.add(f'<g{op}><g {self.st("sxr" if right else "sx", dur, delay)}>{body}<g transform="translate(384 0)">{body}</g></g></g>')

    def xfade(self, a: Canvas | str, b: Canvas | str, dur: float, delay: float = 0) -> None:
        """Two frames easing into each other and back."""
        sa = a if isinstance(a, str) else a.svg()
        sb = b if isinstance(b, str) else b.svg()
        self.add(f'<g {self.st("xa", dur, delay)}>{sa}</g><g {self.st("xb", dur, delay)}>{sb}</g>')

    def wrap(self, cls: str, svg: str, dur: float, delay: float = 0, extra: str = "") -> None:
        self.add(f"<g {self.st(cls, dur, delay, extra)}>{svg}</g>")

    def frames(self, svgs: list[str], period: float, delay: float = 0) -> None:
        """Step through frames, each shown for an equal share of the period."""
        n = len(svgs)
        name = f"fr{n}"
        if not any(f"@keyframes {name}{{" in r for r in self.s.css):
            cut = round(100 / n, 3)
            self.s.style(f"@keyframes {name}{{0%,{cut}%{{opacity:1}}{round(cut + 0.001, 3)}%,100%{{opacity:0}}}}")
        for i, svg in enumerate(svgs):
            d = round(i * period / n - period - delay, 3)
            self.add(f'<g style="opacity:0;animation:{name} {period}s steps(1,end) infinite;animation-delay:{d}s">{svg}</g>')

    def keyframed(self, svg: str, frames: str, dur: float, delay: float = 0, timing: str = "linear") -> None:
        """A one-off movement; `frames` is the body of an @keyframes rule."""
        name = self._name("k")
        self.s.style(f"@keyframes {name}{{{frames}}}")
        self.add(f'<g style="animation:{name} {dur}s {timing} infinite;animation-delay:-{round(delay, 2)}s">{svg}</g>')

    def glow_def(self, color: str, peak: float = 1) -> str:
        gid = f"g{color[1:]}{int(peak * 100)}"
        if not any(f'id="{gid}"' in d for d in self.s.defs):
            self.s.defs.append(
                f'<radialGradient id="{gid}"><stop offset="0" stop-color="{color}" stop-opacity="{peak}"/>'
                f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            )
        return gid

    def glow(self, x: float, y: float, r: float, color: str, cls: str = "br", dur: float = 6, delay: float = 0, peak: float = 1) -> None:
        gid = self.glow_def(color, peak)
        attrs = self.st(cls, dur, delay) if cls else ""
        self.add(f'<circle {attrs} cx="{x}" cy="{y}" r="{r}" fill="url(#{gid})"/>')

    def clip(self, rects: list[tuple[int, int, int, int]]) -> str:
        cid = f"c{len(self.s.defs)}"
        d, cx, cy = [], 0, 0
        for x, y, w, h in rects:
            d.append(f"{'m' if d else 'M'}{x - cx} {y - cy}h{w}v{h}h{-w}z")
            cx, cy = x, y
        self.s.defs.append(f'<clipPath id="{cid}"><path d="{"".join(d).replace(" -", "-")}"/></clipPath>')
        return cid
