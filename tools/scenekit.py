"""Small kit for building an animated 384x216 pixel scene as one SVG.

Layers are drawn in code (tools/pixkit.py) and emitted as stroked 1px rows, the
encoding the other scenes use.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable


W, H = 384, 216
RGB = tuple[int, int, int]
Px = tuple[int, int]


def hexc(c: RGB) -> str:
    return "#%02x%02x%02x" % c


def rgb(h: str) -> RGB:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lum(c: RGB) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


# ---------------------------------------------------------------- pixel rows


def _runs(points: Iterable[Px], bridge: set[Px] | frozenset = frozenset()) -> list[tuple[int, int, int]]:
    """Row runs of the pixels; a run may stretch over `bridge` pixels (painted later
    anyway) when that joins it to the next run."""
    pts = sorted(set(points), key=lambda p: (p[1], p[0]))
    runs: list[tuple[int, int, int]] = []
    for x, y in pts:
        if runs and runs[-1][1] == y:
            rx, ry, n = runs[-1]
            end = rx + n
            if end == x or (end < x and all((g, y) in bridge for g in range(end, x))):
                runs[-1] = (rx, ry, x - rx + 1)
                continue
        runs.append((x, y, 1))
    return runs


def _num(v: float) -> str:
    s = f"{v:g}"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def _pair(a: float, b: float) -> str:
    """Two numbers with the least separator path syntax allows."""
    sa, sb = _num(a), _num(b)
    return sa + sb if sb[0] == "-" or (sb[0] == "." and "." in sa) else f"{sa} {sb}"


def _columns(pts: set[Px], bridge: set[Px] | frozenset) -> list[tuple[int, int, int]]:
    """Vertical runs (x, y, n) of two or more pixels that have no same-colour
    neighbour left or right: a 1px upright line costs a few characters as one `v`
    stroke against a full row command per pixel. A run may cross `bridge` pixels."""
    lone = {(x, y) for x, y in pts if (x - 1, y) not in pts and (x + 1, y) not in pts}
    cols = []
    for x, y in sorted(lone):
        if (x, y - 1) in lone:
            continue
        n = 1
        while True:
            if (x, y + n) in lone:
                n += 1
                continue
            g = n
            while (x, y + g) in bridge and (x, y + g) not in pts:
                g += 1
            if g > n and (x, y + g) in lone:
                n = g
                continue
            break
        if n >= 2:
            cols.append((x, y, n))
    return cols


def path_d(points: Iterable[Px], bridge: set[Px] | frozenset = frozenset()) -> str:
    """The pixels as one stroked path: rows as `h` runs on half-pixel lines, lone
    upright lines as `v` runs; the first move absolute, the rest relative."""
    pts = set(points)
    cols = _columns(pts, bridge)
    used = {(x, y + i) for x, y, n in cols for i in range(n)}
    segs = [(y + 0.5, x, x + n, y + 0.5, f"h{n}") for x, y, n in _runs(pts - used, bridge)]
    segs += [(y, x + 0.5, x + 0.5, y + n, f"v{n}") for x, y, n in cols]
    segs.sort(key=lambda s: (s[0], s[1]))
    out = []
    cx = cy = None
    for sy, sx, ex, ey, cmd in segs:
        out.append(f"M{_pair(sx, sy)}{cmd}" if cx is None else f"m{_pair(sx - cx, sy - cy)}{cmd}")
        cx, cy = ex, ey
    return "".join(out)


def fill_d(points: Iterable[Px]) -> str:
    """The pixels as filled outlines: every boundary loop of the region traced along
    the pixel edges (outer ones clockwise, holes the other way, so the nonzero rule
    leaves holes empty), each side one `h` or `v`. A solid block costs one short loop
    where rows would cost a command each."""
    pts = set(points)
    out_edges: dict[Px, list[Px]] = {}
    for x, y in pts:
        for (nx, ny), a, b in (
            ((x, y - 1), (x, y), (x + 1, y)),
            ((x + 1, y), (x + 1, y), (x + 1, y + 1)),
            ((x, y + 1), (x + 1, y + 1), (x, y + 1)),
            ((x - 1, y), (x, y + 1), (x, y)),
        ):
            if (nx, ny) not in pts:
                out_edges.setdefault(a, []).append(b)
    out = []
    cur = None
    for start in sorted(out_edges, key=lambda p: (p[1], p[0])):
        while out_edges.get(start):
            loop = [start]
            v = start
            while True:
                nxt = out_edges[v].pop()
                if nxt == start:
                    break
                loop.append(nxt)
                v = nxt
            # corners only: drop points in the middle of a straight side
            n = len(loop)
            corners = [loop[i] for i in range(n) if not (loop[i - 1][0] == loop[i][0] == loop[(i + 1) % n][0] or loop[i - 1][1] == loop[i][1] == loop[(i + 1) % n][1])]
            x0, y0 = corners[0]
            out.append(f"M{x0} {y0}" if cur is None else f"m{_pair(x0 - cur[0], y0 - cur[1])}")
            px, py = x0, y0
            for cx, cy in corners[1:]:
                out.append(f"h{cx - px}" if cy == py else f"v{cy - py}")
                px, py = cx, cy
            out.append("z")
            cur = (x0, y0)
    return "".join(out)


# Colours this close (per channel, out of 255) to one already in the scene are drawn as
# that one: shading and outline mixes land on many near-equal shades, and each costs a
# path of its own. Darks get more room, since the eye can't tell them apart.
SNAP, SNAP_DARK = 4, 12
_palette: dict[str, str] = {}


def new_palette() -> None:
    _palette.clear()


def snap(c: str) -> str:
    if c not in _palette:
        r = rgb(c)
        t = SNAP_DARK if max(r) < 64 else SNAP
        _palette[c] = next((k for k in dict.fromkeys(_palette.values()) if max(abs(a - b) for a, b in zip(r, rgb(k))) <= t), c)
    return _palette[c]


def paths(colored: dict[Px, str], attrs: str = "") -> str:
    """One path per colour, as stroked rows or filled outlines, whichever is shorter.
    Without attrs (so every stroke is opaque), the commonest colours go first and their
    rows bridge pixels the later colours paint over."""
    by: dict[str, list[Px]] = {}
    for p, c in colored.items():
        by.setdefault(snap(c), []).append(p)
    order = sorted(by, key=lambda c: -len(by[c])) if not attrs else list(by)
    later = set(colored)
    out = []
    a = f" {attrs}" if attrs else ""
    for c in order:
        later -= set(by[c])
        rows = path_d(by[c], later if not attrs else frozenset())
        fill = fill_d(by[c])
        out.append(f'<path fill="{c}"{a} d="{fill}"/>' if len(fill) + 2 < len(rows) else f'<path stroke="{c}"{a} d="{rows}"/>')
    return "".join(out)


def prune(defs: list[str], *uses: str) -> list[str]:
    """Drop the <g id> sprites in `defs` that nothing names with href (frames that only
    ever show as layers of a loop, say)."""
    import re

    kept = list(defs)
    while True:
        text = "".join(kept) + "".join(uses)
        named = set(re.findall(r'href="#([^"]+)"', text))
        nxt = [d for d in kept if not ((m := re.match(r'<g id="([^"]+)">', d)) and m.group(1) not in named)]
        if len(nxt) == len(kept):
            return kept
        kept = nxt


def tidy(svg: str) -> str:
    """Numbers to two decimals: timings and glow centres come out of float maths."""
    import re

    return re.sub(r"(?<![#\w])(\d+\.\d{3,})", lambda m: f"{round(float(m.group(1)), 2):g}", svg)


LIMIT = 131072  # the most characters Claude's Svg element draws (SvgProps.source)


def check_size(name: str, svg: str) -> None:
    if len(svg) > LIMIT:
        raise SystemExit(f"{name}: {len(svg)} characters, over the {LIMIT} the Svg element draws")


class Scene:
    def __init__(self, seed: int, bg: str, shade: str, roll: str, scan_opacity: float = 0.2):
        self.rng = random.Random(seed)
        new_palette()
        self.bg = bg
        self.shade = shade  # vignette and scanline colour
        self.roll = roll
        self.scan_opacity = scan_opacity
        self.css: list[str] = []
        self.defs: list[str] = []
        self.body: list[str] = []

    def style(self, *rules: str) -> None:
        self.css.extend(rules)

    def add(self, *svg: str) -> None:
        self.body.extend(svg)

    def r(self, a: float, b: float) -> float:
        return round(self.rng.uniform(a, b), 1)

    def render(self) -> str:
        css = "".join(self.css) + (
            f"svg{{background:{self.bg}}}.px{{shape-rendering:crispEdges}}"
            f".scan{{fill:{self.shade};opacity:{self.scan_opacity}}}"
            f".roll{{fill:{self.roll};opacity:.035;animation:roll 12s linear infinite}}"
            "@keyframes roll{from{transform:translateY(-30px)}to{transform:translateY(216px)}}"
            "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
        )
        defs = (
            '<pattern id="scanP" width="4" height="1" patternUnits="userSpaceOnUse"><rect class="scan" y=".5" width="4" height=".5"/></pattern>'
            f'<radialGradient id="vg" cx=".5" cy=".45" r=".8"><stop offset=".55" stop-color="{self.shade}" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="{self.shade}" stop-opacity=".55"/></radialGradient>' + "".join(prune(self.defs, *self.body))
        )
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 216" preserveAspectRatio="xMidYMid slice">'
            f"<style>{css}</style><defs>{defs}</defs>"
            f'<g class="px" fill="none" stroke-width="1">{"".join(self.body)}</g>'
            '<rect width="384" height="216" fill="url(#vg)"/><rect width="384" height="216" fill="url(#scanP)"/>'
            '<rect class="roll" width="384" height="22"/></svg>'
        )

    def write(self, name: str, header: str, draft_dir: str = "drafts/out") -> int:
        svg = tidy(self.render())
        check_size(name, svg)
        import os

        os.makedirs(draft_dir, exist_ok=True)
        with open(f"{draft_dir}/{name}.svg", "w") as f:
            f.write(svg)
        with open(f"hooks/scenes/{name}.ts", "w") as f:
            f.write(f"// Generated by tools/build_scenes.py: {header}, all vector.\nexport const SCENE = {json.dumps(svg)}\n")
        return len(svg)
