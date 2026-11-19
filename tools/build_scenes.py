"""Build the code-drawn UIT scenes.

usage: uv run python tools/build_scenes.py [scene ...]

Every part of a scene is painted here in code (tools/pixkit.py), so every part can move:
clouds slide round, leaves glint, people walk, traffic passes. Writes hooks/scenes/<name>.ts
and a copy of the SVG under drafts/out/ for previewing.
"""

from __future__ import annotations

import math
import random
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from pixkit import Canvas, Motion, canopy, cloud, leaf_glints, mix, palm, streak, text_px, window_grid  # noqa: E402
from scenekit import H, W, Scene  # noqa: E402
from people import Cast, bicycle, bow, cheer, clap, idle, idle_side, offer, pedal, phone, present, ride, scooter, seat_feet, talk, wave  # noqa: E402
from rig import Look, Pose, walk  # noqa: E402

HAIR = ["#1a1626", "#2a1e1a", "#14121e", "#3a2618"]
SKIN = ["#e0a982", "#d39a74", "#c88a66", "#ecb894"]


# ---------------------------------------------------------------- UIT buildings


def tower_e(c: Canvas, x: int, top: int, base: int, glass_top: str, glass_bot: str, mull: str, slab: str, slab_dark: str, frame: str, lit=None, rng=None) -> list[tuple[int, int, int, int]]:
    """Tower E: a cream service slab on the left, the glass curtain wall, stacked balconies
    on the right and a pergola frame on the roof. Returns the glass panes."""
    # Service slab.
    c.rect(x, top + 6, 14, base - top - 6, slab)
    c.vline(x + 13, top + 6, base - top - 6, slab_dark)
    for y in range(top + 10, base - 4, 6):
        c.rect(x + 5, y, 4, 3, mull)
    # Glass.
    gx, gw = x + 14, 48
    panes = []
    c.grad(gx, top, gx + gw, base, [(top, glass_top), (base, glass_bot)], step=6)
    for y in range(top, base, 6):
        c.hline(gx, y, gw, frame)
    for xx in range(gx, gx + gw, 6):
        c.vline(xx, top, base - top, mull)
    for y in range(top + 1, base, 6):
        for xx in range(gx + 1, gx + gw, 6):
            panes.append((xx, y, 5, 5))
    # Diagonal sky reflections.
    for i in range(0, gw + 40, 17):
        for d in range(22):
            px, py = gx + i - d, top + 4 + d * 2
            if gx <= px < gx + gw and top < py < base and (py - top) % 6:
                c.set(px, py, mix(glass_top, "#ffffff", 0.35))
    # Balconies.
    bx = gx + gw
    c.rect(bx, top + 2, 3, base - top - 2, slab_dark)
    for y in range(top + 2, base - 2, 6):
        c.hline(bx, y, 12, frame)
        c.hline(bx + 1, y + 1, 11, slab_dark)
        for k in range(bx + 2, bx + 12, 2):
            c.set(k, y - 1, slab_dark)
    # Roof pergola.
    c.hline(gx - 2, top - 5, gw + 10, frame)
    for xx in range(gx - 2, gx + gw + 8, 7):
        c.vline(xx, top - 5, 5, slab_dark)
    c.hline(x, top + 5, 14, frame)
    if lit:
        for wx, wy, ww, wh in panes:
            if rng.random() < lit:
                c.rect(wx, wy, ww, wh - 1, rng.choice(["#ffd98a", "#ffe6a8", "#f6c66a"]))
    return panes


def hall(c: Canvas, x: int, y: int, w: int, h: int, wall: str, wall_dark: str, roof: str, roof_dark: str, win, rng, dome: tuple[str, str] | None = None) -> list[tuple[int, int, int, int]]:
    """A low UIT hall: white walls in window bands under a terracotta hip roof, maybe a green dome."""
    c.rect(x, y, w, h, wall)
    c.hline(x, y + h - 1, w, wall_dark)
    rh = max(5, h // 3)
    c.poly([(x - 3, y), (x + 6, y - rh), (x + w - 6, y - rh), (x + w + 3, y)], roof)
    for yy in range(y - rh + 2, y, 2):
        c.hline(x + 6 - (yy - y + rh), yy, w - 12 + 2 * (yy - y + rh) - 1, roof_dark)
    c.hline(x - 3, y, w + 6, roof_dark)
    wins = window_grid(c, x + 3, y + 3, (w - 4) // 6, max(1, (h - 5) // 6), 4, 3, 2, 3, win, rng)
    if dome:
        cx = x + w / 2
        c.ellipse(cx, y - rh, w * 0.18, rh * 1.15, dome[0], top_only=True)
        c.ellipse(cx - w * 0.05, y - rh - rh * 0.4, w * 0.06, rh * 0.45, dome[1], top_only=True)
        c.hline(round(cx - w * 0.18), y - rh, round(w * 0.36), roof_dark)
    return wins


def block(c: Canvas, x: int, y: int, w: int, h: int, wall: str, band: str, glass: str, rng, floors: int = 4) -> list[tuple[int, int, int, int]]:
    """A white lecture block: horizontal bands of windows."""
    c.rect(x, y, w, h, wall)
    c.hline(x, y, w, band)
    fh = h // floors
    wins = []
    for f in range(floors):
        fy = y + 3 + f * fh
        c.hline(x, fy + fh - 3, w, band)
        for xx in range(x + 3, x + w - 4, 7):
            c.rect(xx, fy, 5, fh - 5, glass)
            c.vline(xx + 2, fy, fh - 5, band)
            wins.append((xx, fy, 5, fh - 5))
    return wins


def plane(m: Motion, y: int, dur: float, delay: float, body: str, trail: str) -> None:
    c = Canvas()
    x = W + 6
    c.hline(x, y, 3, body)
    c.set(x + 1, y - 1, body)
    c.set(x + 1, y + 1, body)
    tr = "".join(f'<path stroke="{trail}" opacity="{op}" d="M{x + 3 + i * 8} {y}.5h8"/>' for i, op in enumerate((0.5, 0.32, 0.18, 0.08)))
    m.keyframed(tr + c.svg(), "0%{transform:translate(0,0)}60%,100%{transform:translate(-470px,12px)}", dur, delay)


def flock(m: Motion, y: int, birds, color: str, dur: float, delay: float, right: bool = False) -> None:
    a, b = Canvas(), Canvas()
    x0 = -30 if right else W + 10
    for bx, by in birds:
        x, yy = x0 + bx, y + by
        a.set(x, yy, color), a.set(x + 2, yy, color), a.set(x + 1, yy + 1, color)
        b.set(x, yy + 1, color), b.set(x + 1, yy, color), b.set(x + 2, yy + 1, color)
    dx = 470 if right else -470
    m.keyframed(f'<g class="la" style="animation-duration:.8s">{a.svg()}</g><g class="lb" style="animation-duration:.8s;animation-delay:-.4s">{b.svg()}</g>', f"0%{{transform:translate(0,0)}}70%,100%{{transform:translate({dx}px,-14px)}}", dur, delay)


def glint(m: Motion, rects, dur: float, delay: float) -> None:
    cid = m.clip(rects)
    x0 = min(r[0] for r in rects)
    x1 = max(r[0] + r[2] for r in rects)
    y0 = min(r[1] for r in rects)
    y1 = max(r[1] + r[3] for r in rects)
    h = y1 - y0
    name = m._name("gl")
    m.s.style(f"@keyframes {name}{{0%{{transform:translateX(0)}}35%,100%{{transform:translateX({x1 - x0 + 2 * h}px)}}}}")
    m.add(
        f'<g clip-path="url(#{cid})"><g style="animation:{name} {dur}s ease-in-out infinite;animation-delay:-{delay}s">'
        f'<path fill="#ffffff" opacity=".22" d="M{x0 - h - 8} {y1}l{h} -{h}h8l-{h} {h}z"/>'
        f'<path fill="#ffffff" opacity=".12" d="M{x0 - h - 20} {y1}l{h} -{h}h3l-{h} {h}z"/></g></g>'
    )


def rustle(m: Motion, pts, rng, color: str, dur=(4, 7), share: float = 0.07) -> None:
    """Bright leaves trading places: the crown seems to stir in a breeze."""
    m.xfade(leaf_glints(pts, rng, color, share), leaf_glints(pts, rng, color, share), rng.uniform(*dur), rng.uniform(0, 6))


def sky_clouds(m: Motion, rng, n: int, ys: tuple[int, int], ws: tuple[int, int], cols, dur: float, opacity: float = 1, right: bool = False) -> None:
    layer = Canvas(wrap=True)
    for i in range(n):
        cloud(layer, int(i * W / n + rng.uniform(0, W / n * 0.6)), rng.randint(*ys), rng.randint(*ws), rng, *cols)
    m.scroll(layer, dur, rng.uniform(0, dur), right=right, opacity=opacity)


# ---------------------------------------------------------------- Job Fair


def job_fair() -> int:
    rng = random.Random(23)
    s = Scene(seed=23, bg="#0b2a8e", shade="#020a24", roll="#cfe0ff")
    m = Motion(s)

    sky = Canvas()
    sky.grad(0, 0, W, 170, [(0, "#0a2688"), (50, "#1440b4"), (100, "#2564d8"), (150, "#5a9cf0"), (170, "#86bcf6")])
    m.static(sky)
    # Two decks of cloud sliding round at different speeds.
    sky_clouds(m, rng, 6, (22, 58), (14, 26), ("#d8e4ff", "#aec4f2", "#8aa6e4"), 420, opacity=0.85)
    flock(m, 44, [(0, 0), (5, 2), (9, -1), (14, 3), (18, 1)], "#dfe8ff", 90, 10)
    plane(m, 26, 140, 60, "#ffffff", "#e8f0ff")
    sky_clouds(m, rng, 4, (70, 112), (30, 52), ("#ffffff", "#dde8ff", "#b2c8f2"), 240)

    # Tower E on the left, a lecture block on the right.
    bld = Canvas()
    panes = tower_e(bld, 16, 58, 160, "#5cb4d4", "#2a78a8", "#86c4dc", "#e9eef4", "#b9c6d6", "#f4f8fc")
    block(bld, 290, 104, 94, 52, "#eef3f8", "#c4d0e0", "#3c88b4", rng)
    m.static(bld)
    glint(m, panes, 16, 3)

    # Trees behind the booths; their leaves stir.
    trees = Canvas()
    crowns = []
    for cx in range(96, 300, 22):
        crowns.append(canopy(trees, cx + rng.uniform(-4, 4), 140 + rng.uniform(-4, 3), rng.uniform(10, 14), rng, "#17582f", "#26803f", "#4fae55"))
    crowns.append(canopy(trees, 352, 152, 14, rng, "#17582f", "#26803f", "#4fae55"))
    m.static(trees)
    for pts in crowns:
        rustle(m, pts, rng, "#8ad46a")

    # The bougainvillea in front of the tower.
    bou = Canvas()
    bpts = canopy(bou, 26, 140, 26, rng, "#1a5a30", "#2c8040", "#52a852", blobs=9)
    bpts |= canopy(bou, 70, 152, 16, rng, "#1a5a30", "#2c8040", "#52a852")
    for x, y in bpts:
        if rng.random() < 0.16:
            bou.set(x, y, rng.choice(["#ff4fa0", "#e8338a", "#ff7ab8"]))
    bou.rect(30, 160, 3, 20, "#5a3a2a")
    m.static(bou)
    rustle(m, bpts, rng, "#ff8ac4", share=0.05)
    rustle(m, bpts, rng, "#86cf60", share=0.05)

    # Booth tents with striped peaked roofs and blank signboards.
    tents = Canvas()
    peaks = []
    counters = []
    for x0, x1, sign in [(126, 176, "#f39a2a"), (176, 230, "#2fb0b0"), (230, 290, "#e8384a"), (290, 342, "#2f6fe0"), (342, 400, "#e8384a")]:
        px, py, eave = (x0 + x1) / 2, 136 + (x1 - x0) // 12, 154
        peaks.append((px, py))
        for y in range(int(py), eave):
            t = (y - py) / (eave - py)
            half = (x1 - x0) / 2 * t + 1
            for x in range(math.floor(px - half), math.ceil(px + half)):
                ang = math.atan2(x + 0.5 - px, y + 0.5 - py + 2)
                tents.set(x, y, "#2f6fe0" if int((ang + 2) * 7) % 2 else "#f4f8ff")
        tents.hline(x0, eave, x1 - x0, "#c9d6f0")
        tents.rect(x0 + 2, eave + 1, x1 - x0 - 4, 22, "#e4eaf6")
        tents.rect(x0 + 6, eave + 2, x1 - x0 - 12, 6, sign)
        counters.append((x0, x1, eave, sign))
        tents.vline(x0 + 2, eave, 24, "#9aa8cc")
        tents.vline(x1 - 3, eave, 24, "#9aa8cc")
    m.static(tents)

    # Bunting between the peaks, fluttering.
    fa, fb = Canvas(), Canvas()
    for (ax, ay), (bx, by) in zip(peaks, peaks[1:]):
        n = int(bx - ax)
        for i in range(0, n, 2):
            t = i / n
            x, y = ax + i, ay + (by - ay) * t + 6 * math.sin(math.pi * t)
            fa.set(x, y, "#f4f8ff")
            fb.set(x, y, "#f4f8ff")
            if i % 6 == 2:
                col = ["#ff5a6a", "#ffd34a", "#4ad0c0", "#ffffff"][(i // 6) % 4]
                for c, off in ((fa, 0), (fb, 1)):
                    c.set(x + off, y + 1, col), c.set(x + 1 + off, y + 1, col), c.set(x + off, y + 2, col), c.set(x + off * 2, y + 3, col)
    m.xfade(fa, fb, 1.8)

    # Feather flags on poles, rippling.
    for fx in (120, 236, 334):
        a, b = Canvas(), Canvas()
        col = rng.choice(["#2f6fe0", "#ffffff", "#4ad0c0"])
        for c, ph in ((a, 0), (b, math.pi)):
            c.vline(fx, 128, 48, "#d8dee8")
            for y in range(130, 158):
                wv = round(math.sin((y - 130) / 5 + ph))
                c.hline(fx + 1, y, 5 + wv, col)
        m.xfade(a, b, rng.uniform(1.6, 2.4), rng.uniform(0, 2))

    # The plaza.
    plaza = Canvas()
    plaza.grad(0, 176, W, H, [(176, "#b9c2e2"), (216, "#8e9ad0")])
    for y in (184, 194, 206):
        plaza.hline(0, y, W, "#a4aed8")
    m.static(plaza)

    # Recruiters behind the counters, explaining; students queueing, chatting, on phones.
    cast = Cast(m, "j")
    uni = ["#f4f6fa", "#ffffff", "#2f6fe0", "#dfe8ff", "#7ab0ff"]

    def student(**kw) -> Look:
        base = dict(skin=rng.choice(SKIN), hair=rng.choice(HAIR), shirt=rng.choice(uni), pants=rng.choice(["#22263e", "#2a2f50", "#3a3f5e"]))
        base.update(kw)
        return Look(**base)

    staff = [Look(skin=SKIN[1], hair="#1a1626", shirt="#ffffff", sleeves="long"), Look(skin=SKIN[3], hair="#2a1e1a", hair_style="bob", shirt="#2f6fe0", sleeves="long")]
    desk = Canvas()
    for x0, x1, eave, sign in counters:
        for k, rx in enumerate(range(x0 + 14, x1 - 8, 22)):
            cast.stay(staff[(x0 // 50 + k) % 2], 14, rx, eave + 19, present(), rng.uniform(3, 4.5), rng.uniform(0, 4))
        desk.rect(x0 + 5, eave + 13, x1 - x0 - 10, 10, "#f4f8ff")
        desk.hline(x0 + 5, eave + 13, x1 - x0 - 10, "#ffffff")
        desk.rect(x0 + 5, eave + 17, x1 - x0 - 10, 2, sign)
        desk.hline(x0 + 5, eave + 22, x1 - x0 - 10, "#c4cce4")
        for px in range(x0 + 9, x1 - 9, 9):
            desk.rect(px, eave + 11, 4, 2, rng.choice(["#ffd34a", "#ffffff", "#ff8fb3", "#7ab0ff"]))
    m.static(desk)

    q_looks = [student(), student(hair_style="long", bag="#2f5fb0"), student(hair_style="pony", skirt="#2a3a6a"), student(hair_style="bob", bag="#b04a3a")]
    for bx in (136, 192, 250, 306, 358):
        x = bx + rng.randint(-3, 3)
        for k in range(rng.randint(2, 4)):
            look = rng.choice(q_looks)
            r = rng.random()
            feet = 182 + rng.randint(0, 2)
            if r < 0.45:
                cast.stay(look, 13, x, feet, idle(sway=0.6, blink=False), rng.uniform(4, 7), rng.uniform(0, 7), facing=2)
            elif r < 0.75:
                cast.stay(look, 13, x, feet, talk(), rng.uniform(3.5, 5), rng.uniform(0, 5), facing=rng.choice([1, -1]))
            else:
                cast.stay(Look(**{**look.__dict__, "prop": "phone"}), 13, x, feet, phone(), rng.uniform(4, 6), rng.uniform(0, 6), facing=rng.choice([1, -1]))
            x += rng.randint(6, 9)

    # The balloon arch, each balloon nodding.
    n = 30
    for half in (0, 1):
        c = Canvas()
        for i in range(half, n + 1, 2):
            a = i * math.pi / n
            for rr, k in ((34, 0), (39, 1)):
                bx, by = 70 + rr * math.cos(a), 186 - rr * 1.15 * math.sin(a)
                col = ["#2f6fe0", "#f4f8ff", "#6aa4ff"][(i + k) % 3]
                c.ellipse(bx, by, 2.8, 2.8, col)
                c.set(bx - 1, by - 1, "#ffffff" if col != "#f4f8ff" else "#cfe0ff")
        m.wrap("bob", c.svg(), 2.4 + half * 0.5, half * 1.2)

    # Loose balloons drifting up from the arch.
    for i in range(6):
        c = Canvas()
        col = rng.choice(["#2f6fe0", "#ffffff", "#4a8cff", "#ff6a8a"])
        bx, by = rng.randint(40, 100), rng.randint(140, 160)
        c.ellipse(bx, by, 2.5, 3, col)
        c.set(bx - 1, by - 1, "#ffffff")
        c.line(bx, by + 3, bx + 1, by + 8, "#c4cce4")
        m.wrap("rise", f'<g {m.st("sw", rng.uniform(2.5, 4), rng.uniform(0, 3))}>{c.svg()}</g>', rng.uniform(34, 50), i * 7 + rng.uniform(0, 3), f"--d:-{rng.randint(150, 175)}px;--dx:{rng.randint(-20, 20)}px")

    # Petals.
    for _ in range(8):
        c = Canvas()
        c.set(rng.randint(2, 80), rng.randint(118, 160), rng.choice(["#ff4fa0", "#e8338a", "#ff7ab8"]))
        m.wrap("fall", f'<g {m.st("sw", rng.uniform(2, 3.5), rng.uniform(0, 3))}>{c.svg()}</g>', rng.uniform(10, 16), rng.uniform(0, 16), f"--d:{rng.randint(40, 60)}px;--dx:{rng.randint(6, 18)}px")

    # Students crossing the plaza at three depths, CVs and bags in hand.
    for feet, hh, n, gap, k, frames in [(193, 14, 4, 80, 2, 6), (202, 17, 4, 60, 2, 6), (214, 22, 4, 40, 3, 8)]:
        looks = [student(bag=rng.choice(["#2f5fb0", "#1a2a5a", "#b04a3a", "#3a8a6a"])), student(hair_style="long", prop="folder"), student(prop="folder", sleeves="long", shirt="#ffffff", pants="#1e2238")][3 - k:]
        for i in range(n):
            look = looks[i % len(looks)]
            kw = {"arms": (6, -14), "elbows": (24, 16)} if look.prop == "folder" else {}
            cast.walker(look, hh, feet + rng.randint(-1, 1), i % 2 == 0, i / n + rng.uniform(0, 0.5 / n), gap=gap, n=frames, **kw)

    return s.write("jobfair", "UIT job fair day")


# ---------------------------------------------------------------- After School


def after_school() -> int:
    rng = random.Random(11)
    s = Scene(seed=11, bg="#0c0d36", shade="#05061a", roll="#ffd2c2")
    m = Motion(s)
    s.style(
        ".dusk{animation:dusk 70s ease-in-out infinite alternate}@keyframes dusk{from{opacity:0}to{opacity:.34}}",
        ".late{animation:late 70s ease-in-out infinite alternate}@keyframes late{0%,40%{opacity:0}100%{opacity:.95}}",
        ".shim{animation:shim ease-in-out infinite alternate}@keyframes shim{from{opacity:.15}to{opacity:.7}}",
    )

    sky = Canvas()
    sky.grad(0, 0, W, 172, [(0, "#0c0d36"), (40, "#1a1d5c"), (80, "#3a2f7e"), (108, "#7a3f8a"), (130, "#c4567e"), (150, "#f08a6a"), (166, "#ffb878")])
    m.static(sky)
    m.add('<rect class="dusk" width="384" height="172" fill="#08062a"/>')

    # Stars: some there all along, more as the dusk deepens.
    for i in range(46):
        c = Canvas()
        x, y = rng.randint(0, W - 1), rng.randint(2, 84)
        col = rng.choice(["#fff6dc", "#d6e0ff", "#ffffff"])
        c.set(x, y, col)
        if rng.random() < 0.15:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.set(x + dx, y + dy, mix(col, "#1a1d5c", 0.5))
        if i < 24:
            m.wrap("tw", c.svg(), rng.uniform(3, 8), rng.uniform(0, 8))
        else:
            m.add(f'<g class="late" style="animation-delay:-{rng.uniform(0, 30):.1f}s">{c.svg()}</g>')

    moon = Canvas()
    moon.ellipse(332, 18, 7, 7, "#fff1c4")
    for (x, y) in list(moon.px):
        if (x + 0.5 - 335) ** 2 + (y + 0.5 - 15.5) ** 2 < 36:
            del moon.px[(x, y)]
    m.glow(332, 18, 18, "#fff1c4", "br", 9, 0, peak=0.3)
    m.static(moon)

    # Long dusk clouds sliding past, two decks.
    far = Canvas(wrap=True)
    for i in range(7):
        streak(far, int(i * 55 + rng.uniform(0, 30)), rng.randint(40, 80), rng.randint(20, 46), "#6a3f8a", "#4a2f78")
    m.scroll(far, 420, rng.uniform(0, 400), opacity=0.8)
    near = Canvas(wrap=True)
    for i in range(6):
        streak(near, int(i * 64 + rng.uniform(0, 30)), rng.randint(90, 128), rng.randint(30, 64), "#ffa07a", "#c4588a")
    m.scroll(near, 260, rng.uniform(0, 250))
    flock(m, 60, [(0, 0), (5, 3), (9, -2), (13, 4), (17, 1)], "#1b1238", 100, 20)
    flock(m, 96, [(0, 0), (6, 2), (10, -1)], "#24163f", 120, 80, right=True)

    # Far trees.
    far_trees = Canvas()
    for x in range(0, W, 7):
        far_trees.ellipse(x + rng.uniform(-2, 2), 158 + rng.uniform(-2, 2), rng.uniform(5, 8), rng.uniform(4, 6), "#2a1f4e")
    far_trees.rect(0, 158, W, 14, "#2a1f4e")
    m.static(far_trees)

    # Building A and the halls with their domes, Tower E on the right; their windows lit.
    win_lit = lambda r: r.choice(["#ffd27a", "#ffe2a0", "#f6c060", "#5b6a9e", "#ffd27a"])  # noqa: E731
    bld = Canvas()
    wins = hall(bld, 20, 132, 88, 34, "#b9b6e6", "#8b88c4", "#e0785a", "#b55a48", win_lit, rng, dome=("#3aa8a8", "#7ad8d0"))
    wins += hall(bld, 122, 142, 98, 26, "#aeaade", "#8480bc", "#d8705a", "#a85048", win_lit, rng, dome=("#3a9a9a", "#6acac0"))
    panes = tower_e(bld, 292, 76, 172, "#2a8aa0", "#1a5070", "#3a9ab0", "#c8c4ec", "#8a86c0", "#dcdaf6", lit=0.45, rng=rng)
    m.static(bld)
    for wx, wy, ww, wh in wins + panes:
        if rng.random() < 0.22:
            c = Canvas()
            c.rect(wx, wy, ww, wh - (1 if (wx, wy, ww, wh) in panes else 0), "#4a5888")
            m.wrap("off", c.svg(), rng.uniform(26, 50), rng.uniform(0, 50))
    m.glow(326, 66, 5, "#ff4a3a", "br", 3.2, 0, peak=0.95)
    beacon = Canvas()
    beacon.rect(325, 66, 2, 2, "#ff5a4a")
    m.static(beacon)
    glint(m, panes, 22, 8)

    # Trees along the road, leaves stirring; palms swaying.
    trees = Canvas()
    crowns = []
    for cx in range(110, 290, 20):
        crowns.append(canopy(trees, cx + rng.uniform(-3, 3), 166 + rng.uniform(-3, 2), rng.uniform(8, 11), rng, "#173a3a", "#245048", "#3a7a5e"))
    flame = canopy(trees, 14, 150, 18, rng, "#7a1e2e", "#b8323a", "#e8503e", blobs=8)
    flame |= canopy(trees, 374, 156, 14, rng, "#7a1e2e", "#b8323a", "#e8503e")
    trees.rect(12, 160, 3, 14, "#3a2230")
    trees.rect(373, 164, 3, 10, "#3a2230")
    m.static(trees)
    for pts in crowns:
        rustle(m, pts, rng, "#5aa07a", share=0.06)
    rustle(m, flame, rng, "#ff8a5a", share=0.06)
    for px, base, h, lean in [(44, 172, 44, 0.4), (104, 172, 36, -0.3), (230, 170, 40, 0.3), (272, 172, 44, -0.2)]:
        a, b = Canvas(), Canvas()
        palm(a, px, base, h, lean, "#6a4a5a", "#4a3248", "#1e3a34", "#3a6a4a", sway=-0.06)
        palm(b, px, base, h, lean, "#6a4a5a", "#4a3248", "#1e3a34", "#3a6a4a", sway=0.06)
        m.xfade(a, b, rng.uniform(3.5, 5), rng.uniform(0, 4))

    # Sidewalk, lamps, the wet road.
    ground = Canvas()
    ground.rect(0, 172, W, 8, "#4a4880")
    ground.hline(0, 172, W, "#6a68a0")
    ground.grad(0, 180, W, H, [(180, "#2c2a64"), (216, "#1c1a48")], step=6)
    for x in range(0, W, 24):
        ground.hline(x, 197, 12, "#5a5890")
    lamps = [20, 84, 148, 212, 276, 340]
    for lx in lamps:
        ground.vline(lx, 152, 20, "#262444")
        ground.hline(lx - 1, 151, 4, "#262444")
        ground.rect(lx + 2, 151, 2, 2, "#ffe6a0")
    m.static(ground)
    for lx in lamps:
        m.glow(lx + 3, 152, 9, "#ffd27a", "br", rng.uniform(5, 8), rng.uniform(0, 8), peak=0.6)
        ref = Canvas()
        for y in range(182, 214, 2):
            ref.hline(lx + 2 + rng.randint(-1, 1), y, rng.randint(1, 3), "#c09060")
        m.wrap("shim", ref.svg(), rng.uniform(1.8, 3.2), rng.uniform(0, 3))

    cast = Cast(m, "a")
    # Students walking home along the sidewalk: alone, in pairs, one reading a phone.
    def student(**kw) -> Look:
        base = dict(skin=rng.choice(SKIN), hair=rng.choice(HAIR), shirt=rng.choice(["#eef2fa", "#dfe6f5", "#ffffff"]), pants=rng.choice(["#22263e", "#2a3050"]), bag=rng.choice(["#2f5fb0", "#b04a3a", "#3a8a6a", "#222838"]))
        base.update(kw)
        return Look(**base)

    walkers = [
        (student(), 15, True, 0.05, {}),
        (student(hair_style="long", skirt="#2a3a6a"), 14, False, 0.3, {}),
        (student(prop="phone", bag="#222838"), 15, True, 0.55, {"arms": (38, -4), "elbows": (98, 10)}),
        (student(hair_style="bob"), 14, False, 0.8, {}),
    ]
    for look, hh, right, ph, kw in walkers:
        cast.walker(look, hh, 178, right, ph, gap=60, **kw)
    # A pair walking together, the second a step behind.
    a_, b_ = student(), student(hair_style="pony", shirt="#f4c4d4")
    for look, off in ((a_, 0), (b_, 0.012)):
        cast.walker(look, 15, 178 + (1 if off else 0), False, 0.62 + off, gap=60)

    # Traffic: scooters both ways with their lights, a cyclist, the campus bus now and then.
    head = m.glow_def("#fff2b8", 0.7)
    tail = m.glow_def("#ff3b30", 0.6)
    lights = f'<circle cx="11" cy="-14" r="5" fill="url(#{head})"/><circle cx="-13" cy="-8.5" r="3" fill="url(#{tail})"/>'
    bikes = []
    for col in ["#e8e8f4", "#c83a3a", "#2a5ab0", "#1e1e2a", "#e8a030"]:
        bk, fr = scooter(col)
        bikes.append((cast.raw(f"sb{col}", bk), cast.raw(f"sf{col}", fr)))
    helmets = ["#c83a3a", "#f4f4fa", "#2a5ab0", "#ffd34a", "#1e1e2a", "#e86aa0"]
    tops = ["#3a5ab0", "#eef2fa", "#e86a5a", "#2a2f50", "#7a9a5a", "#dfe6f5"]
    for feet, right, n, speed in [(192, False, 5, (20, 26)), (209, True, 6, (16, 21))]:
        for i in range(n):
            bk, fr = rng.choice(bikes)
            hh = 15
            rid = Look(skin=rng.choice(SKIN), helmet=rng.choice(helmets), shirt=rng.choice(tops), sleeves="long", pants=rng.choice(["#22263e", "#3a3f5e"]))
            people = []
            if rng.random() < 0.45:
                pas = Look(skin=rng.choice(SKIN), helmet=rng.choice(helmets), hair_style="long", shirt=rng.choice(["#eef2fa", "#ffffff", "#f4c4d4"]), pants="#2a3050", bag=rng.choice(["#b04a3a", "#2f5fb0", None]))
                people.append(f'<g transform="translate(-8 {seat_feet(hh, -13):.1f})"><use href="#{cast.sid(pas, hh, ride(arms=25, elbows=50))}"/></g>')
            people.append(f'<g transform="translate(-3 {seat_feet(hh, -13):.1f})"><use href="#{cast.sid(rid, hh, ride())}"/></g>')
            dur = rng.uniform(*speed)
            cast.vehicle(bk, people, fr, feet, right, dur, i / n + rng.uniform(0, 0.6 / n), glow=lights)
    cyc = bicycle("#2f6fe0")
    cl = Look(skin=SKIN[3], hair_style="pony", shirt="#ffffff", pants="#22263e", bag="#2f5fb0")
    pedals = cast.steps([cast.sid(cl, 16, pedal(k)) for k in range(4)], 0.8, 0)
    cast.vehicle(cast.raw("cyc", cyc), [f'<g transform="translate(-4 {seat_feet(16, -13):.1f})">{pedals}</g>'], None, 210, True, 46, 0.2)
    bus = Canvas()
    bx = W + 4
    bus.rect(bx, 179, 46, 14, "#f2b830")
    bus.hline(bx, 179, 46, "#ffd860")
    bus.rect(bx, 189, 46, 2, "#c88a20")
    for k in range(6):
        bus.rect(bx + 3 + k * 7, 181, 5, 5, "#ffe8a8" if k % 2 else "#fff2c4")
    bus.rect(bx, 181, 2, 8, "#fff2b8")
    for wx in (bx + 8, bx + 36):
        bus.rect(wx, 192, 5, 3, "#14142a")
    m.keyframed(f'<circle cx="{bx}" cy="186" r="9" fill="url(#{head})"/>' + bus.svg(), "0%{transform:translateX(0)}45%,100%{transform:translateX(-460px)}", 90, 30)

    # Flame-tree petals.
    for _ in range(8):
        c = Canvas()
        c.set(rng.choice([rng.randint(0, 34), rng.randint(360, 383)]), rng.randint(136, 160), rng.choice(["#e8433a", "#ff6a4a"]))
        m.wrap("fall", f'<g {m.st("sw", rng.uniform(2, 3.5), rng.uniform(0, 3))}>{c.svg()}</g>', rng.uniform(9, 14), rng.uniform(0, 14), f"--d:{rng.randint(30, 50)}px;--dx:{rng.randint(4, 14)}px")

    return s.write("afterschool", "UIT after school at dusk")


# ---------------------------------------------------------------- Graduation Day

CAP = ([".nnnnn.", "nnnnnnn", "..nnn.l", "......l"], ["..nnnn.", "nnnnnnn", ".nnnn..", "..l...."])
BUTTERFLY = (["yy.yy", "yybyy", ".y.y."], [".y.y.", ".yby.", "..b.."])


def graduation() -> int:
    rng = random.Random(37)
    s = Scene(seed=37, bg="#3d9cf4", shade="#f2ece0", roll="#ffffff")
    m = Motion(s)
    s.style(
        ".rays{animation:rays 14s ease-in-out infinite alternate}@keyframes rays{from{opacity:.03}to{opacity:.18}}",
        ".flash{animation:flash 17s ease-out infinite}@keyframes flash{0%,93%{opacity:0}95%{opacity:.8}100%{opacity:0}}",
        ".bf{animation:bf ease-in-out infinite}@keyframes bf{0%{transform:translate(0,0)}25%{transform:translate(9px,-7px)}50%{transform:translate(15px,1px)}75%{transform:translate(6px,6px)}100%{transform:translate(0,0)}}",
        ".ba,.bb{animation:st .5s steps(1) infinite}.bb{animation-delay:-.25s}",
        ".hop{animation:hop ease-in-out infinite}@keyframes hop{0%,70%,100%{transform:translateY(0)}78%{transform:translateY(-4px)}86%{transform:translateY(0)}}",
    )

    sky = Canvas()
    sky.grad(0, 0, W, 170, [(0, "#3d9cf4"), (60, "#5ab0f8"), (110, "#8ccaf9"), (160, "#c8e6fb")])
    m.static(sky)
    m.glow(18, 10, 46, "#fffbe0", "br", 10, 0, peak=0.7)
    m.add('<g class="rays" fill="#fffbe8"><path d="M0 0h40l70 140h-26z"/><path d="M58 0h18l60 120h-12z"/><path d="M96 0h10l46 96h-8z"/></g>')
    sky_clouds(m, rng, 6, (18, 50), (16, 30), ("#ffffff", "#e6f2fe", "#c4dcf6"), 380, opacity=0.9)
    flock(m, 34, [(0, 0), (6, 3), (11, -1), (16, 4), (21, 1)], "#ffffff", 100, 30)
    sky_clouds(m, rng, 4, (60, 100), (30, 56), ("#ffffff", "#eef6ff", "#cfe2f8"), 220)

    bld = Canvas()
    block(bld, -2, 92, 96, 64, "#f2f6fa", "#c8d4e2", "#6ab0d8", rng, floors=5)
    hall(bld, 70, 128, 74, 28, "#f6f2ea", "#d4ccc0", "#e8744a", "#c0583a", "#6aa8d0", rng, dome=("#3a9a6a", "#7acc9a"))
    hall(bld, 150, 132, 70, 24, "#f6f2ea", "#d4ccc0", "#e8744a", "#c0583a", "#6aa8d0", rng, dome=("#3a9a6a", "#7acc9a"))
    panes = tower_e(bld, 290, 62, 162, "#86d6e6", "#3a9ab8", "#a8e2ee", "#f0ead8", "#c8c0a8", "#ffffff")
    m.static(bld)
    glint(m, panes, 20, 9)

    trees = Canvas()
    crowns = []
    for cx in range(60, 300, 18):
        crowns.append(canopy(trees, cx + rng.uniform(-3, 3), 156 + rng.uniform(-3, 2), rng.uniform(9, 12), rng, "#2a7a3a", "#3e9a46", "#6cc05a"))
    m.static(trees)
    for pts in crowns:
        rustle(m, pts, rng, "#a6e27a", share=0.06)
    for px, base, h, lean in [(16, 172, 54, 0.3), (370, 172, 50, -0.3)]:
        a, b = Canvas(), Canvas()
        palm(a, px, base, h, lean, "#a07a5a", "#7a5a40", "#2a7a3a", "#5ab04a", sway=-0.06)
        palm(b, px, base, h, lean, "#a07a5a", "#7a5a40", "#2a7a3a", "#5ab04a", sway=0.06)
        m.xfade(a, b, rng.uniform(3.5, 5), rng.uniform(0, 4))

    # Banners on poles, rippling.
    for fx, col in [(30, "#2c4196"), (44, "#f08a3a"), (340, "#f08a3a"), (354, "#2c4196")]:
        a, b = Canvas(), Canvas()
        for c, ph in ((a, 0), (b, math.pi)):
            c.vline(fx, 138, 36, "#e6e6ee")
            for y in range(140, 164):
                wv = round(math.sin((y - 140) / 4 + ph))
                c.hline(fx + 1, y, 6 + wv, col)
        m.xfade(a, b, rng.uniform(1.8, 2.6), rng.uniform(0, 2))

    lawn = Canvas()
    lawn.grad(0, 168, W, H, [(168, "#7ccc56"), (216, "#4aa03a")], step=8)
    for _ in range(260):
        lawn.set(rng.randint(0, W - 1), rng.randint(170, H - 1), rng.choice(["#5ab040", "#94d86a"]))
    m.static(lawn)

    # The class in gowns and caps: a back row and a front row, waving, clapping, cheering.
    cast = Cast(m, "g")

    def grad(**kw) -> Look:
        base = dict(skin=rng.choice(SKIN), hair=rng.choice(HAIR), gown="#26387a", cap="#18224e", pants="#26387a", shoes="#14142a")
        base.update(kw)
        return Look(**base)

    def acts(look: Look, h: int, x: int, feet: int) -> None:
        r = rng.random()
        if r < 0.4:
            cast.stay(look, h, x, feet, idle(blink_at=rng.choice([3, 7])), rng.uniform(5, 8), rng.uniform(0, 8), facing=0)
        elif r < 0.6:
            cast.stay(look, h, x, feet, wave(), rng.uniform(0.9, 1.3), rng.uniform(0, 2), facing=0)
        elif r < 0.85:
            cast.stay(look, h, x, feet, clap(), rng.uniform(0.7, 0.9), rng.uniform(0, 2), facing=0)
        else:
            cast.stay(look, h, x, feet, cheer(), rng.uniform(1.1, 1.5), rng.uniform(0, 2), facing=0)

    back = [grad(), grad(hair_style="long")]
    for x in range(62, 336, 10):
        if rng.random() < 0.9:
            acts(rng.choice(back), 15, x + rng.randint(-1, 1), 174 + rng.randint(0, 1))
    front = [grad(), grad(hair_style="long", skin=SKIN[3])]
    bare = grad(cap=None, hair_style="short")
    tosses = []
    for x in range(68, 332, 15):
        if rng.random() < 0.9:
            feet = 190 + rng.randint(0, 2)
            if len(tosses) < 6 and rng.random() < 0.3:
                cast.stay(bare, 20, x, feet, cheer(), rng.uniform(1.1, 1.4), rng.uniform(0, 2), facing=0)
                tosses.append((x - 3, feet - 24))
            else:
                acts(rng.choice(front), 20, x, feet)

    # Caps tossed high: a slow rise, a hang, a slow fall.
    cmap = {"n": "#141e48", "l": "#ffd34a"}
    for i, (x, y) in enumerate(tosses):
        dx = rng.choice([-8, -5, 5, 8])
        hgt = rng.randint(40, 60)
        a, b = Canvas(), Canvas()
        a.sprite(CAP[0], cmap, x, y)
        b.sprite(CAP[1], cmap, x, y)
        m.keyframed(
            f'<g class="la" style="animation-duration:.9s">{a.svg()}</g><g class="lb" style="animation-duration:.9s;animation-delay:-.45s">{b.svg()}</g>',
            f"0%{{transform:translate(0,0);opacity:0;animation-timing-function:ease-out}}4%{{opacity:1}}26%{{transform:translate({dx // 2}px,-{hgt}px);animation-timing-function:ease-in}}"
            f"50%{{transform:translate({dx}px,0);opacity:1}}54%,100%{{transform:translate({dx}px,0);opacity:0}}",
            rng.uniform(13, 17),
            i * 2.6 + rng.uniform(0, 1),
        )

    for _ in range(26):
        c = Canvas()
        x = rng.randint(0, 383)
        col = rng.choice(["#a6e22e", "#ffd34a", "#ffffff", "#ff8fb3", "#5aa0ff"])
        c.set(x, 0, col)
        c.set(x + 1, 0, col) if rng.random() < 0.5 else c.set(x, 1, col)
        m.wrap("fall", f'<g {m.st("sw", rng.uniform(2.5, 4), rng.uniform(0, 3))}>{c.svg()}</g>', rng.uniform(18, 28), rng.uniform(0, 28), f"--d:{rng.randint(160, 210)}px;--dx:{rng.randint(-10, 20)}px")

    for bx, by, col in [(334, 186, "#ffd34a"), (40, 192, "#ffffff")]:
        bm = {"y": col, "b": "#3a2a1a"}
        a, b = Canvas(), Canvas()
        a.sprite(BUTTERFLY[0], bm, bx, by)
        b.sprite(BUTTERFLY[1], bm, bx, by)
        m.add(f'<g {m.st("bf", rng.uniform(8, 11), rng.uniform(0, 8))}><g class="ba">{a.svg()}</g><g class="bb">{b.svg()}</g></g>')

    # Family coming over with flowers.
    for i, (look, hh) in enumerate([
        (Look(skin=SKIN[1], hair="#2a1e1a", hair_style="bob", shirt="#f4c4d4", sleeves="long", pants="#3a4a6a", hold="#ff5a7a"), 22),
        (Look(skin=SKIN[0], hair="#1a1626", shirt="#b8d4f4", pants="#2a2f50", hold="#ffd34a"), 23),
    ]):
        cast.walker(look, hh, 210, i == 0, 0.15 + i * 0.5, gap=120, arms=(30, -18), elbows=(70, 20))

    # The photographer, lining up shots; now and then the flash.
    shoot = Pose(arms=(80, 70), elbows=(118, 120), lean=1)
    rest = Pose(arms=(40, 10), elbows=(70, 14))
    ph = Look(skin=SKIN[2], hair="#1a1626", shirt="#ffffff", pants="#3a4a6a", bag="#2a2a3a", prop="camera")
    cast.stay(ph, 24, 354, 212, [shoot] * 5 + [rest] * 2 + [shoot], 17, 12, facing=-1)
    m.glow(343, 192, 10, "#ffffff", "flash", 17, 5, peak=0.95)

    return s.write("graduation", "UIT graduation day, light")


# ---------------------------------------------------------------- Teachers' Day

HEART = [".x.x.", "xxxxx", ".xxx.", "..x.."]
SMALL_HEART = ["x.x", "xxx", ".x."]
INK_HEART = [".xx...xx.", "x..x.x..x", "x...x...x", "x.......x", ".x.....x.", "..x...x..", "...x.x...", "....x...."]


def ceiling_fan(m: Motion, cx: int, y: int, r: int, blade: str, back: str, rod: str) -> None:
    rodc = Canvas()
    rodc.vline(cx, 0, y, rod)
    rodc.rect(cx - 2, y, 5, 3, rod)
    m.static(rodc)
    svgs = []
    for f in range(6):
        c = Canvas()
        for k in range(3):
            a = f * (2 * math.pi / 3) / 6 + k * 2 * math.pi / 3
            tx, ty = cx + r * math.cos(a), y + 1.5 + 2.2 * math.sin(a)
            col = back if math.sin(a) < 0 else blade
            c.line(cx, y + 1, tx, ty, col)
            c.line(cx, y + 2, tx, ty + 1, col)
        svgs.append(c.svg())
    m.frames(svgs, 0.9)


def ink_doodle(m: Motion, pts: list[tuple[int, int]], color: str, start: float, write: float, cycle: float) -> None:
    """Marker strokes appear in order over `write` seconds from `start`, stay, then fade."""
    name = m._name("ink")
    m.s.style(f"@keyframes {name}{{0%{{opacity:0}}1%,70%{{opacity:1}}76%,100%{{opacity:0}}}}")
    by: dict[int, list] = {}
    for i, p in enumerate(pts):
        by.setdefault(i * 12 // max(1, len(pts)) if len(pts) < 12 else i // max(1, len(pts) // 40), []).append(p)
    keys = sorted(by)
    for j, k in enumerate(keys):
        c = Canvas()
        for x, y in by[k]:
            c.set(x, y, color)
        t = start + write * j / len(keys)
        m.add(f'<g style="opacity:0;animation:{name} {cycle}s linear infinite;animation-delay:{round(t - cycle, 2)}s">{c.svg()}</g>')


def teachers() -> int:
    rng = random.Random(41)
    s = Scene(seed=41, bg="#2e2a5a", shade="#0e0a1e", roll="#ffd9c2")
    m = Motion(s)

    room = Canvas()
    room.grad(0, 0, W, 150, [(0, "#3a366e"), (40, "#4e4a8a"), (150, "#6a64a6")], step=10)
    room.rect(0, 0, W, 5, "#26224e")
    room.rect(0, 150, W, 30, "#4a4682")
    room.hline(0, 150, W, "#7a74b4")
    room.rect(0, 180, W, 36, "#3a3466")
    m.static(room)

    # The window: night outside, Tower E lit, clouds passing, trees stirring.
    wx, wy, ww, wh = 8, 20, 70, 100
    out = Canvas()
    out.grad(wx, wy, wx + ww, wy + wh, [(wy, "#0a0f3a"), (wy + wh, "#24306e")], step=8)
    m.static(out)
    cid = m.clip([(wx, wy, ww, wh)])
    stars = Canvas()
    for _ in range(14):
        stars.set(rng.randint(wx, wx + ww - 1), rng.randint(wy, wy + 50), "#fff6dc")
    m.add(f'<g clip-path="url(#{cid})">')
    for p, col in stars.px.items():
        c = Canvas()
        c.set(*p, col)
        m.wrap("tw", c.svg(), rng.uniform(3, 7), rng.uniform(0, 6))
    cl = Canvas(wrap=True)
    for i in range(3):
        streak(cl, i * 128 + rng.randint(0, 40), rng.randint(wy + 14, wy + 40), rng.randint(20, 36), "#3a4a8a", "#2a3672")
    m.scroll(cl, 160, 20)
    tw_ = Canvas()
    tpanes = tower_e(tw_, 24, 54, 124, "#2a6a8a", "#1a4060", "#2a7090", "#6a6aa0", "#4a4a80", "#8a8ac0", lit=0.5, rng=rng)
    m.static(tw_)
    for r in tpanes:
        if rng.random() < 0.25:
            c = Canvas()
            c.rect(r[0], r[1], r[2], r[3] - 1, "#22406a")
            m.wrap("off", c.svg(), rng.uniform(20, 40), rng.uniform(0, 40))
    ta, tb = Canvas(), Canvas()
    for c, sh in ((ta, 0), (tb, 1)):
        for x in range(wx - 4, wx + ww + 4, 9):
            c.ellipse(x + sh, wy + wh - 6, 8, 9, "#0e1a2e")
    m.xfade(ta, tb, 4.5)
    m.add("</g>")
    frame = Canvas()
    frame.rect(wx - 3, wy - 3, ww + 6, 3, "#c8c8e8")
    frame.rect(wx - 3, wy + wh, ww + 6, 4, "#c8c8e8")
    frame.rect(wx - 3, wy, 3, wh, "#c8c8e8")
    frame.rect(wx + ww, wy, 3, wh, "#c8c8e8")
    frame.rect(wx + ww // 2 - 1, wy, 2, wh, "#c8c8e8")
    frame.rect(wx, wy + 42, ww, 2, "#c8c8e8")
    m.static(frame)

    # The whiteboard, with the date and doodles writing themselves.
    board = Canvas()
    board.rect(98, 18, 236, 98, "#9a96c4")
    board.grad(100, 20, 332, 114, [(20, "#f4f4fa"), (114, "#e2e0f0")], step=12)
    board.rect(98, 116, 236, 3, "#7a76a8")
    board.rect(140, 6, 150, 5, "#e6e4f4")
    board.hline(140, 11, 150, "#a8a4cc")
    m.static(board)
    date = text_px("20/11", 172, 42, scale=4)
    date.sort(key=lambda p: (p[0] // 4, p[1]))
    ink_doodle(m, date, "#e8507a", 0.5, 6, 24)
    for (hx, hy, col, st) in [(116, 30, "#e8608a", 7), (300, 32, "#5a7ad8", 8.5), (126, 84, "#5a7ad8", 10), (292, 80, "#e8608a", 11.5)]:
        pts = [(hx + dx * 2 + sx, hy + dy * 2 + sy) for dy, row in enumerate(INK_HEART) for dx, ch in enumerate(row) if ch == "x" for sx in (0, 1) for sy in (0, 1)]
        cxh, cyh = hx + 8, hy + 7
        pts.sort(key=lambda p: (math.atan2(p[0] - cxh, p[1] - cyh) + 2 * math.pi) % (2 * math.pi))
        ink_doodle(m, pts, col, st, 2.5, 24)
    under = [(x, 78 + (1 if x % 7 < 3 else 0)) for x in range(170, 262)]
    ink_doodle(m, under, "#5a7ad8", 6.6, 1.5, 24)

    # Ceiling fans.
    ceiling_fan(m, 120, 9, 22, "#e8e6f4", "#a8a4cc", "#2a264e")
    ceiling_fan(m, 310, 9, 22, "#e8e6f4", "#a8a4cc", "#2a264e")

    # Fairy lights under the board: a wave of warmth running along.
    wire = Canvas()
    bulbs = []
    for x in range(100, 334):
        t = (x - 100) / 234
        y = 124 + 8 * math.sin(math.pi * ((t * 3) % 1))
        wire.set(x, y, "#2a264e")
        if x % 9 == 4:
            bulbs.append((x, y + 1))
    m.static(wire)
    for i, (bx, by) in enumerate(bulbs):
        c = Canvas()
        c.rect(bx, by, 2, 2, rng.choice(["#ffd27a", "#ffb0c0", "#ffe6a0"]))
        m.glow(bx + 1, by + 1, 6, "#ffcf6a", "tw", 3, i * 0.25, peak=0.75)
        m.static(c)

    # The lecturer's desk: laptop, coffee, flowers.
    desk = Canvas()
    desk.rect(262, 150, 116, 6, "#c07a4a")
    desk.rect(266, 156, 108, 26, "#a0603a")
    desk.hline(266, 156, 108, "#7a4428")
    desk.rect(286, 140, 20, 10, "#2a2e4a")
    desk.rect(287, 141, 18, 8, "#4a6aa8")
    desk.rect(320, 144, 5, 6, "#f4f0ff")
    m.static(desk)
    m.glow(296, 145, 16, "#8ab8ff", "br", 6, 0, peak=0.3)
    for i, x in enumerate((321, 322, 323)):
        c = Canvas()
        c.set(x, 143, "#f4f0ff")
        c.set(x, 142, "#f4f0ff")
        m.wrap("rise", f'<g {m.st("sw", 1.6, i * 0.5)}><g opacity=".5">{c.svg()}</g></g>', rng.uniform(3.5, 4.5), i * 1.3, "--d:-14px")
    fa, fb = Canvas(), Canvas()
    for c, sh in ((fa, 0), (fb, 1)):
        c.rect(344, 138, 8, 12, "#e8f0ff")
        for (fx, fy, col) in [(342, 128, "#ffd34a"), (350, 126, "#e83a4a"), (356, 131, "#ffd34a"), (346, 133, "#ff8fb3"), (338, 134, "#e83a4a"), (354, 121, "#c890e0")]:
            c.line(348, 138, fx + 1 + sh * (1 if fx > 348 else 0), fy + 3, "#3a8a4a")
            c.ellipse(fx + 1 + sh * (1 if fx > 348 else 0), fy + 1, 2.4, 2.4, col)
            c.set(fx + 1 + sh * (1 if fx > 348 else 0), fy + 1, "#7a4a1a" if col == "#ffd34a" else mix(col, "#ffffff", 0.4))
    m.xfade(fa, fb, 3.5)

    # Hearts drifting up from the flowers.
    for i in range(7):
        art = HEART if rng.random() < 0.5 else SMALL_HEART
        col = rng.choice(["#ff6b8a", "#ff9ab0", "#e84a6a"])
        x, y = rng.randint(300, 370), rng.randint(118, 134)
        c = Canvas()
        c.sprite(art, {"x": col}, x, y)
        m.wrap("rise", f'<g {m.st("sw", rng.uniform(2, 3), rng.uniform(0, 3))}>{c.svg()}</g>', rng.uniform(9, 13), i * 1.9 + rng.uniform(0, 1), f"--d:-{rng.randint(40, 60)}px")

    # The lecturer in an ao dai holding flowers; students lined up with theirs.
    cast = Cast(m, "t")
    hug = [Pose(arms=(34, -6), elbows=(96, 10), blink=i == 5, sway=0.6 if i in (2, 3, 4) else 0) for i in range(8)]
    lec = Look(skin="#ecb894", hair="#14121e", hair_style="long", dress="#6aa4ec", pants="#f4f2fa", shoes="#2a2a3a", hold="#e83a4a")
    cast.stay(lec, 40, 242, 178, hug, 6, 0, facing=-1)
    for x, hh, hold, style in [(178, 36, "#ffd34a", "short"), (152, 34, "#ff8fb3", "long"), (126, 37, "#e83a4a", "bob")]:
        look = Look(skin=rng.choice(SKIN), hair=rng.choice(HAIR), hair_style=style, shirt="#eef4ff", pants="#1e2446", shoes="#14142a", hold=hold)
        poses = [Pose(arms=(34, -6), elbows=(96, 10), blink=i == rng.randint(3, 7), sway=0.6 if i >= 4 else 0) for i in range(8)]
        cast.stay(look, hh, x, 178, poses, rng.uniform(5, 7), rng.uniform(0, 6))

    # A student walking up with a bouquet, offering it with a bow, and walking back.
    giver = Look(skin="#d9a07c", hair="#1a1626", shirt="#eef4ff", pants="#1e2446", shoes="#14142a", hold="#ffd34a", bag="#2f5fb0")
    empty = Look(**{**giver.__dict__, "hold": None})
    hh, P = 38, 1.05
    walk_in = [cast.sid(giver, hh, Pose(**{**walk(i / 8).__dict__, "arms": (34, -14), "elbows": (96, 20)}), 1) for i in range(8)]
    walk_out = [cast.sid(empty, hh, walk(i / 8), 1) for i in range(8)]
    give = [cast.sid(giver, hh, p, 1) for p in [offer(), offer(), offer(), bow(), bow(), offer()]]
    dist = 250
    cyc = round(2 * dist / (0.7 * hh / P) / 0.48, 1)
    m.s.style(
        "@keyframes gv{0%{transform:translateX(0)}24%,50%{transform:translateX(250px)}74%,100%{transform:translateX(0)}}",
        "@keyframes gva{0%,23.9%{opacity:1}24%,100%{opacity:0}}",
        "@keyframes gvs{0%,23.9%{opacity:0}24%,49.9%{opacity:1}50%,100%{opacity:0}}",
        "@keyframes gvb{0%,49.9%{opacity:0}50%,100%{opacity:1}}",
    )
    m.add(
        f'<g transform="translate(-40 183)"><g style="animation:gv {cyc}s linear infinite;animation-delay:-{round(cyc * 0.1, 1)}s">'
        f'<g style="animation:gva {cyc}s steps(1,end) infinite;animation-delay:-{round(cyc * 0.1, 1)}s">{cast.steps(walk_in, P, 0)}</g>'
        f'<g style="opacity:0;animation:gvs {cyc}s steps(1,end) infinite;animation-delay:-{round(cyc * 0.1, 1)}s">{cast.steps(give, cyc * 0.26 / 2, 0)}</g>'
        f'<g style="opacity:0;animation:gvb {cyc}s steps(1,end) infinite;animation-delay:-{round(cyc * 0.1, 1)}s"><g transform="scale(-1 1)">{cast.steps(walk_out, P, 0)}</g></g></g></g>'
    )

    # Classmates in the front row, seen from behind, shifting in their seats.
    row = [Look(skin=SKIN[k], hair=HAIR[k], hair_style=st, shirt=sh, pants="#1e2446") for k, (st, sh) in enumerate([("short", "#eef4ff"), ("long", "#ffffff"), ("bob", "#dfe8ff"), ("pony", "#ffffff")])]
    for i, x in enumerate(range(10, W + 10, 34)):
        x += rng.randint(-4, 4)
        look = row[(i * 3) % 4] if i % 5 else row[i % 4]
        poses = [Pose(sway=0), Pose(sway=0), Pose(sway=1), Pose(sway=1)]
        cast.stay(look, 64, x, 216 + 36, poses, rng.uniform(6, 10), rng.uniform(0, 10), facing=2, outline=True)

    # Dust in the light.
    for _ in range(18):
        c = Canvas()
        c.set(rng.randint(60, 340), rng.randint(40, 170), "#fff2d8")
        m.wrap("mote", c.svg(), rng.uniform(14, 24), rng.uniform(0, 24), f"--dx:{rng.randint(-20, 30)}px;--d:-{rng.randint(20, 50)}px")

    return s.write("teachers", "Teachers' Day at UIT")


SCENES = {"jobfair": job_fair, "afterschool": after_school, "graduation": graduation, "teachers": teachers}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        print(name, SCENES[name]() // 1024, "KB")
