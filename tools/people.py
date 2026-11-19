"""Rig people placed in a scene.

Each distinct (look, height, pose) is drawn once and placed with <use>, so a crowd of
fifty costs a handful of sprites. A frame loop is split into layers by the frames each
pixel shows in (the head that never moves is one layer, a blinking eye another), and each
layer steps its opacity on a keyframe made for that set of frames; the loop's period and
offset ride on CSS variables, so every instance keeps its own timing. Walkers move whole
pixels per step so they stay crisp. Sprites no loop or <use> ends up naming are dropped
(scenekit.prune).
"""

from __future__ import annotations

import math

from pixkit import Canvas, Motion, mix
from rig import DARK, Look, Pose, sprite, walk

W = 384

WALK_CSS = ".wk{animation:wk linear infinite}@keyframes wk{to{transform:translateX(var(--wd))}}"
LOOP_CSS = ".fl>[class]{animation-duration:var(--p);animation-delay:var(--o);animation-timing-function:steps(1,end);animation-iteration-count:infinite}"

# A set of frames gets its own layer when that saves more than it costs: roughly, when
# its pixels times the extra frames that would otherwise repeat them pass this.
LAYER_MIN = 60


class Cast:
    def __init__(self, m: Motion, tag: str = "p"):
        self.m = m
        self.tag = tag
        self.ids: dict[tuple, str] = {}
        self.px: dict[str, dict] = {}
        self.layers: dict[frozenset, str] = {}
        self.count = 0
        m.s.style(WALK_CSS, LOOP_CSS)

    # ------------------------------------------------------------ sprites

    def _new(self) -> str:
        self.count += 1
        return f"{self.tag}{self.count - 1}"

    def sid(self, look: Look, h: int, pose: Pose, facing: int = 1, outline: bool = True, below: int | None = None) -> str:
        """`below`: drop rows from this local y down (hidden under the frame edge)."""
        key = (repr(look), h, repr(pose), facing, outline, below)
        if key not in self.ids:
            i = self._new()
            c = sprite(0, 0, h, look, pose, facing, outline)
            if below is not None:
                c.px = {p: col for p, col in c.px.items() if p[1] < below}
            self.m.s.defs.append(f'<g id="{i}">{c.svg(clip=False)}</g>')
            self.ids[key] = i
            self.px[i] = c.px
        return self.ids[key]

    def layer(self, px: dict) -> str:
        key = frozenset(px.items())
        if key not in self.layers:
            i = self._new()
            c = Canvas()
            c.px = dict(px)
            self.m.s.defs.append(f'<g id="{i}">{c.svg(clip=False)}</g>')
            self.layers[key] = i
        return self.layers[key]

    def raw(self, key: str, c: Canvas) -> str:
        """A hand-drawn sprite (vehicles) kept in defs."""
        if key not in self.ids:
            i = self._new()
            self.m.s.defs.append(f'<g id="{i}">{c.svg(clip=False)}</g>')
            self.ids[key] = i
        return self.ids[key]

    def steps(self, ids: list[str], period: float, delay: float) -> str:
        """Frames shown in turn, each for an equal share of the period, as layers. A
        frame may line up with the first one shifted a pixel (the body rising on a
        step); its layers are then drawn shifted, so the head is still shared."""
        if len(set(ids)) == 1:
            return f'<use href="#{ids[0]}"/>'
        frames = [self.px[i] for i in ids]
        plain = _layers(frames, [(0, 0)] * len(frames))
        shifted = _layers(frames, _offsets(frames))
        groups = min(plain, shifted, key=_cost)
        n = len(ids)
        full = (1 << n) - 1
        out = []
        for (mask, (dx, dy)), px in sorted(groups.items(), key=lambda g: (g[0][0] != full, g[0])):
            lid = self.layer(px)
            at = (f' x="{dx}"' if dx else "") + (f' y="{dy}"' if dy else "")
            out.append(f'<use href="#{lid}"{at}/>' if mask == full else f'<use class="{self.keyframe(n, mask)}" href="#{lid}"{at}/>')
        return f'<g class="fl" style="--p:{period}s;--o:{-round(delay % period, 3)}s">{"".join(out)}</g>'

    def keyframe(self, n: int, mask: int) -> str:
        """Opacity 1 in the frames of `mask`, else 0. Without animation (reduced motion)
        the first frame stays."""
        name = f"q{n}_{mask:x}"
        if not any(f"@keyframes {name}{{" in r for r in self.m.s.css):
            on = [mask >> i & 1 for i in range(n)]
            keys = [(round(100 * i / n, 3), on[i]) for i in range(n) if i == 0 or on[i] != on[i - 1]]
            body = "".join(f"{p}%{{opacity:{v}}}" for p, v in keys[:-1]) + f"{keys[-1][0]}%,100%{{opacity:{keys[-1][1]}}}"
            self.m.s.style(f".{name}{{animation-name:{name}{'' if on[0] else ';opacity:0'}}}@keyframes {name}{{{body}}}")
        return name

    # ------------------------------------------------------------ placing

    def place(self, look: Look, h: int, x: int, feet: int, poses: list[Pose], period: float = 1, delay: float = 0, facing: int = 1, cls: str = "", outline: bool = True, crop: int | None = None) -> str:
        """Someone staying put, looping through poses; facing -1 is a mirrored side view.
        `crop`: nothing drawn from this screen row down (hidden behind a desk, say)."""
        fc = 1 if facing == -1 else facing
        crop = crop if crop is not None else (217 if feet > 216 else None)
        below = crop - feet if crop is not None else None
        ids = [self.sid(look, h, p, fc, outline, below) for p in poses]
        flip = ' transform="scale(-1 1)"' if facing == -1 else ""
        body = f"<g{flip}>{self.steps(ids, period, delay)}</g>"
        if cls:
            body = f"<g {self.m.st(cls, *cls_timing(cls, delay))}>{body}</g>"
        return f'<g transform="translate({x} {feet})">{body}</g>'

    def stay(self, *a, **kw) -> None:
        self.m.add(self.place(*a, **kw))

    def walker(
        self,
        look: Look,
        h: int,
        feet: int,
        right: bool,
        phase: float,
        period: float = 1.05,
        stride: float = 0.7,
        gap: float = 0,
        n: int | None = None,
        arms: tuple[float, float] | None = None,
        elbows: tuple[float, float] | None = None,
        lead: str = "",
    ) -> float:
        """Someone crossing the whole width, feet matched to the ground: one gait cycle
        covers stride*h pixels. `gap` adds that many pixels of offscreen wait. `phase`
        (0..1) places them along their crossing. Returns the crossing time."""
        n = n or (6 if h < 18 else 8)
        poses = []
        for i in range(n):
            p = walk(i / n)
            if arms is not None:
                p.arms, p.elbows = arms, elbows or p.elbows
            poses.append(p)
        ids = [self.sid(look, h, p, 1) for p in poses]
        v = stride * h / period
        margin = h // 2 + 6
        dist = W + 2 * margin + gap
        dur = round(dist / v, 1)
        x0 = -margin if right else W + margin
        wd = dist if right else -dist
        flip = "" if right else ' transform="scale(-1 1)"'
        delay = phase * dur
        self.m.add(
            f'<g transform="translate({x0} {feet})"><g class="wk" style="--wd:{wd}px;animation-duration:{dur}s;animation-delay:-{round(delay, 2)}s;animation-timing-function:steps({int(dist)})">'
            f"{lead}<g{flip}>{self.steps(ids, period, delay)}</g></g></g>"
        )
        return dur

    def vehicle(self, back: str, people: list[str], front: str | None, feet: int, right: bool, dur: float, phase: float, gap: float = 0, glow: str = "") -> None:
        """A vehicle (wheels on y 0) with riders between its back and front parts,
        crossing at a steady speed."""
        margin = 26
        dist = W + 2 * margin + gap
        x0 = -margin if right else W + margin
        wd = dist if right else -dist
        flip = "" if right else ' transform="scale(-1 1)"'
        body = f'<use href="#{back}"/>' + "".join(people) + (f'<use href="#{front}"/>' if front else "")
        self.m.add(
            f'<g transform="translate({x0} {feet})"><g class="wk" style="--wd:{wd}px;animation-duration:{round(dur, 1)}s;animation-delay:-{round(phase * dur, 2)}s;animation-timing-function:steps({int(dist)})">'
            f"<g{flip}>{glow}{body}</g></g></g>"
        )


def _offsets(frames: list[dict]) -> list[tuple[int, int]]:
    """For each frame, the shift (within a pixel) that best lines it up with the first."""
    ref = set(frames[0].items())
    out = []
    for f in frames:
        best = max(
            ((dx, dy) for dy in (0, -1, 1) for dx in (0, -1, 1)),
            key=lambda o: sum(((x - o[0], y - o[1]), c) in ref for (x, y), c in f.items()),
        )
        out.append(best)
    return out


def _layers(frames: list[dict], offs: list[tuple[int, int]]) -> dict[tuple, dict]:
    """Pixels grouped by the frames that show them, once each frame is shifted back by
    its offset: {(frame mask, offset): pixels}. A group with too few pixels to pay for
    its own <use> is folded into its frames' own layers."""
    n = len(frames)
    masks: dict[tuple, int] = {}
    for i, f in enumerate(frames):
        dx, dy = offs[i]
        for (x, y), col in f.items():
            k = ((x - dx, y - dy), col)
            masks[k] = masks.get(k, 0) | 1 << i
    groups: dict[int, dict] = {}
    for (p, col), mask in masks.items():
        groups.setdefault(mask, {})[p] = col
    full = (1 << n) - 1
    for mask in [m for m in groups if m != full and m.bit_count() > 1]:
        if len(groups[mask]) * (mask.bit_count() - 1) <= LAYER_MIN:
            for i in range(n):
                if mask >> i & 1:
                    groups.setdefault(1 << i, {}).update(groups[mask])
            del groups[mask]
    # one <use> per offset among a group's frames
    out: dict[tuple, dict] = {}
    for mask, px in groups.items():
        by: dict[tuple, int] = {}
        for i in range(n):
            if mask >> i & 1:
                by[offs[i]] = by.get(offs[i], 0) | 1 << i
        for o, sub in by.items():
            out[(sub, o)] = {**out[(sub, o)], **px} if (sub, o) in out else px
    return out


def _cost(groups: dict[tuple, dict]) -> int:
    """Rough characters: pixels drawn once per distinct layer, plus a <use> each."""
    seen = {id(px): len(px) for px in groups.values()}
    return 6 * sum(seen.values()) + 40 * len(groups)


def cls_timing(cls: str, delay: float) -> tuple[float, float]:
    return {"bob": (2.6, delay), "hop": (6, delay)}.get(cls, (3, delay))


# ---------------------------------------------------------------- pose library


def idle(blink_at: int = 6, n: int = 8, sway: float = 0, blink: bool = True) -> list[Pose]:
    """Standing, a weight shift half way through and one blink (none from behind)."""
    return [Pose(arms=(3, -3), elbows=(10, 10), blink=blink and i == blink_at, sway=sway if i >= n // 2 else 0) for i in range(n)]


def idle_side(n: int = 8, blink_at: int = 5) -> list[Pose]:
    return [Pose(arms=(4, -6), elbows=(14, 10), blink=i == blink_at, sway=0.6 if i >= n // 2 else 0) for i in range(n)]


def talk() -> list[Pose]:
    """Side view, chatting with a hand: rest, lift, gesture, lift, rest, rest."""
    g = [(8, 20), (30, 80), (40, 100), (30, 80), (8, 20), (8, 20)]
    return [Pose(arms=(a, -4), elbows=(e, 10)) for a, e in g]


def phone() -> list[Pose]:
    """Side view, reading a phone held at chest height; a thumb scroll now and then."""
    return [Pose(arms=(41 if i == 2 else 38, -4), elbows=(98, 10)) for i in range(6)]


def present() -> list[Pose]:
    """Front view, explaining something with one hand, the other resting."""
    g = [(18, 30), (40, 70), (55, 85), (40, 70), (18, 30), (18, 30)]
    return [Pose(arms=(a, 4), elbows=(e, 8), blink=i == 5) for i, (a, e) in enumerate(g)]


def wave(n: int = 4) -> list[Pose]:
    """Front view, one hand waving."""
    e = [30, 0, -24, 0]
    return [Pose(arms=(150, 4), elbows=(e[i % 4], 8)) for i in range(n)]


def clap(n: int = 4) -> list[Pose]:
    return [Pose(arms=(-12, -12), elbows=(-70 if i % 2 else -48, -70 if i % 2 else -48), blink=i == 3) for i in range(n)]


def cheer(n: int = 4) -> list[Pose]:
    """Front view, both arms up, a little hop."""
    out = []
    for i in range(n):
        up = i % 2 == 0
        out.append(Pose(arms=(165, 165) if up else (130, 130), elbows=(10, 10) if up else (30, 30), bob=-1 if up else 0, blink=not up))
    return out


def offer() -> Pose:
    """Side view, both hands held out."""
    return Pose(arms=(70, 60), elbows=(10, 14), lean=3)


def bow() -> Pose:
    return Pose(arms=(10, 10), elbows=(10, 10), lean=5)


def ride(arms: float = 72, elbows: float = 12, legs: float = 80, knees: float = 78) -> Pose:
    """Seated with the hands forward on a handlebar."""
    return Pose(legs=(legs, legs - 6), knees=(knees, knees - 4), arms=(arms, arms - 6), elbows=(elbows, elbows))


def pedal(i: int, n: int = 4) -> Pose:
    a = 2 * math.pi * i / n
    l1 = 62 + 18 * math.sin(a)
    l2 = 62 - 18 * math.sin(a)
    return Pose(legs=(l1, l2), knees=(70 + 30 * math.cos(a), 70 - 30 * math.cos(a)), arms=(58, 52), elbows=(18, 18))


# ---------------------------------------------------------------- vehicles


def wheel(c: Canvas, cx: float, cy: float, r: float, tyre: str, rim: str, hub: str) -> None:
    c.ellipse(cx, cy, r, r, tyre)
    c.ellipse(cx, cy, r - 1.2, r - 1.2, rim)
    c.set(cx, cy, hub)


def seat_feet(h: int, seat_y: float) -> float:
    """Where to put the feet of a seated rider of height h so the hips sit on seat_y."""
    return seat_y + 0.47 * h


def scooter(body: str, seat: str = "#1a1a24", lamp: str = "#fff2b8") -> tuple[Canvas, Canvas]:
    """A side-view scooter facing right, wheels on y 0, about 26px long: the part behind
    the riders and the leg shield and bars in front of them."""
    back, front = Canvas(), Canvas()
    dark = mix(body, DARK, 0.4)
    light = mix(body, "#ffffff", 0.45)
    for cx in (-8, 9):
        back.ellipse(cx, -3.5, 3.6, 3.6, "#14141c")
        back.ellipse(cx, -3.5, 2.2, 2.2, "#5a5a6a")
        back.set(cx, -4, "#c8c8d8")
    # Rear cowl over the back wheel, the floorboard, the exhaust.
    back.poly([(-13, -10), (-2, -11), (0, -6), (-3, -5), (-13, -5.5)], body)
    back.hline(-12, -10, 10, light)
    back.hline(-12, -6, 9, dark)
    back.rect(-4, -6, 10, 2, dark)
    back.hline(-12, -3, 6, "#9a9aaa")
    back.set(-13, -9, "#ff3b30")
    back.set(-13, -8, "#c82a24")
    back.rect(-11, -13, 10, 2, seat)
    back.hline(-10, -13, 8, mix(seat, "#ffffff", 0.22))
    # Leg shield, front fender, steering column, bars, mirror, headlamp.
    front.poly([(4, -5), (6, -13), (8.5, -13), (8, -5)], body)
    front.vline(6, -12, 7, light)
    front.vline(8, -11, 5, dark)
    front.poly([(6, -8), (12, -8), (13.5, -6), (6, -6)], body)
    front.hline(7, -8, 5, light)
    front.vline(8, -16, 3, "#3a3a4a")
    front.hline(4, -16, 6, "#24242e")
    front.set(5, -18, "#24242e")
    front.set(5, -17, "#24242e")
    front.rect(8, -14, 2, 2, lamp)
    return back, front


def bicycle(frame: str) -> Canvas:
    """A side-view bicycle facing right, wheels on y 0; the seat top is at y -13."""
    out = Canvas()
    for cx in (-7, 7):
        for y in range(-9, 1):
            for x in range(cx - 5, cx + 5):
                d = (x + 0.5 - cx) ** 2 + (y + 0.5 + 4) ** 2
                if 9 <= d <= 17:
                    out.set(x, y, "#1a1a24")
        out.set(cx, -4, "#9a9aaa")
    out.line(-7, -4, -1, -4, frame)
    out.line(-1, -4, -3, -11, frame)
    out.line(-3, -11, 5, -11, frame)
    out.line(5, -11, -1, -4, frame)
    out.line(5, -11, 7, -4, frame)
    out.line(5, -11, 4, -15, frame)
    out.hline(3, -15, 3, "#2a2a34")
    out.hline(-5, -12, 4, "#1a1a24")
    out.rect(4, -10, 3, 2, "#8a6a3a")
    return out
