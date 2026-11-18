"""Pixel people from a tiny rig: limbs as capsules posed by angle, then shaded per body
part (light from the upper left) and given a selective outline. Any height, any pose,
side or front view, so a walk cycle or a wave is just a list of poses."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from pixkit import Canvas, mix

DARK = "#120c1c"


@dataclass
class Look:
    skin: str = "#e6b08a"
    hair: str = "#1c1622"
    hair_style: str = "short"  # short | long | pony | bob | helmet | bald
    shirt: str = "#f2f4fa"
    sleeves: str = "short"  # short | long
    pants: str = "#2a3050"
    shoes: str = "#1e1e2a"
    bag: str | None = None
    hold: str | None = None  # bouquet colour
    dress: str | None = None  # ao dai colour; pants then show as the white trousers
    gown: str | None = None  # graduation gown colour
    stole: str = "#5ac85a"
    cap: str | None = None  # mortarboard colour
    helmet: str | None = None
    skirt: str | None = None
    prop: str | None = None  # phone | camera | folder, in the near hand
    extra: dict = field(default_factory=dict)


@dataclass
class Pose:
    legs: tuple[float, float] = (0, 0)  # thigh angles, degrees forward (near, far)
    knees: tuple[float, float] = (4, 4)  # knee flex
    arms: tuple[float, float] = (0, 0)  # upper arm angles forward (near, far); front view: outward
    elbows: tuple[float, float] = (8, 8)
    bob: int = 0
    blink: bool = False
    lean: float = 0
    sway: float = 0  # upper body shifted sideways, for weight shifts


def walk(phase: float) -> Pose:
    """One moment of a relaxed walk; phase in turns (0..1)."""
    p = phase * 2 * math.pi

    def leg(a):
        return 24 * math.sin(a), 6 + 44 * max(0.0, math.cos(a)) ** 1.5

    (n_t, n_k), (f_t, f_k) = leg(p), leg(p + math.pi)
    return Pose(
        legs=(n_t, f_t),
        knees=(n_k, f_k),
        arms=(-24 * math.sin(p), 24 * math.sin(p)),
        elbows=(14 + 22 * max(0.0, -math.sin(p)), 14 + 22 * max(0.0, math.sin(p))),
        bob=-1 if abs(math.sin(p)) < 0.45 else 0,
        lean=2,
    )


# ---------------------------------------------------------------- drawing


class _Body:
    """Pixels labelled by part, painted back to front."""

    def __init__(self):
        self.part: dict[tuple[int, int], str] = {}
        self.color: dict[tuple[int, int], str] = {}
        self.flat: set[tuple[int, int]] = set()

    def put(self, x: int, y: int, part: str, color: str, flat: bool = False) -> None:
        self.part[(x, y)] = part
        self.color[(x, y)] = color
        if flat:
            self.flat.add((x, y))
        else:
            self.flat.discard((x, y))

    def capsule(self, a, b, r: float, part: str, color: str) -> None:
        (ax, ay), (bx, by) = a, b
        x0, x1 = math.floor(min(ax, bx) - r - 1), math.ceil(max(ax, bx) + r + 1)
        y0, y1 = math.floor(min(ay, by) - r - 1), math.ceil(max(ay, by) + r + 1)
        dx, dy = bx - ax, by - ay
        ll = dx * dx + dy * dy or 1e-9
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px, py = x + 0.5, y + 0.5
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ll))
                if (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2 <= r * r:
                    self.put(x, y, part, color)

    def disc(self, cx, cy, r: float, part: str, color: str, keep=None) -> None:
        for y in range(math.floor(cy - r - 1), math.ceil(cy + r + 1)):
            for x in range(math.floor(cx - r - 1), math.ceil(cx + r + 1)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r and (keep is None or keep(x + 0.5 - cx, y + 0.5 - cy)):
                    self.put(x, y, part, color)

    def poly(self, pts, part: str, color: str) -> None:
        c = Canvas()
        c.poly(pts, "#000000")
        for x, y in c.px:
            self.put(x, y, part, color)

    def render(self, c: Canvas, outline: bool = True, shade: float = 0.28, light: float = 0.22) -> None:
        out: dict[tuple[int, int], str] = {}
        for (x, y), part in self.part.items():
            col = self.color[(x, y)]
            if (x, y) in self.flat:
                out[(x, y)] = col
                continue
            same = lambda dx, dy: self.part.get((x + dx, y + dy)) == part  # noqa: E731
            if not same(1, 0) or not same(0, 1):
                col = mix(col, DARK, shade)
            elif not same(-1, 0) or not same(0, -1):
                col = mix(col, "#ffffff", light)
            out[(x, y)] = col
        if outline:
            edge: dict[tuple[int, int], str] = {}
            for (x, y) in self.part:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (x + dx, y + dy)
                    if n not in self.part and n not in edge:
                        edge[n] = mix(self.color[(x, y)], DARK, 0.72)
            for p, col in edge.items():
                c.set(*p, col)
        for p, col in out.items():
            c.set(*p, col)


def draw(c: Canvas, x: float, feet: float, h: int, look: Look, pose: Pose | None = None, facing: int = 1, outline: bool = True) -> None:
    """A person `h` pixels tall standing on `feet`. facing 1 or -1 is a side view walking
    that way; 0 is the front view; 2 is from behind."""
    pose = pose or Pose()
    xl, x = x, x + pose.sway  # legs stay planted; the rest follows the sway
    b = _Body()
    f = 1 if facing in (0, 2) else facing
    side = facing in (1, -1)
    top = feet - h + pose.bob
    R = max(2.2, h * 0.135)
    hx, hy = x + (0.6 * f if side else 0), top + R
    sh_y = top + 2 * R + 0.8
    hip_y = top + h * 0.53
    thigh, shin = h * 0.25, h * 0.215
    upper, fore = h * 0.17, h * 0.16
    rl = max(0.85, h * 0.052)
    ra = max(0.7, h * 0.042)
    tw = max(3.0, h * (0.19 if side else 0.27))
    lean = pose.lean * f * h / 26 if side else 0
    far = lambda col: mix(col, DARK, 0.22)  # noqa: E731

    def limb(base, a1, l1, a2, l2, dirx):
        # Angles from straight down, positive toward dirx.
        k = (base[0] + dirx * math.sin(math.radians(a1)) * l1, base[1] + math.cos(math.radians(a1)) * l1)
        e = (k[0] + dirx * math.sin(math.radians(a2)) * l2, k[1] + math.cos(math.radians(a2)) * l2)
        return k, e

    def leg(i: int, near: bool):
        if side:
            hip = (xl + (0 if near else -0.4 * f), hip_y)
            ang, kn = pose.legs[i], pose.knees[i]
            knee, ankle = limb(hip, ang, thigh, ang - kn, shin, f)
        else:
            sx = xl + (h * 0.06 if i == 0 else -h * 0.06)
            hip = (sx, hip_y)
            knee, ankle = (sx, hip_y + thigh), (sx, hip_y + thigh + shin)
        pc = look.pants if near else far(look.pants)
        shoe = look.shoes if near else far(look.shoes)
        part = f"leg{i}"
        b.capsule(hip, knee, rl * 1.08, part, pc)
        b.capsule(knee, ankle, rl, part, pc)
        if side:
            toe = (ankle[0] + f * h * 0.085, ankle[1] + 0.4)
            b.capsule((ankle[0] - f * 0.4, ankle[1]), toe, rl * 0.85, f"shoe{i}", shoe)
        else:
            b.capsule((ankle[0], ankle[1]), (ankle[0], ankle[1] + 0.6), rl * 1.05, f"shoe{i}", shoe)
        return ankle

    def arm(i: int, near: bool):
        if side:
            sp = (x + lean * 0.5 + (0 if near else -0.4 * f), sh_y + 1)
            a, e = pose.arms[i], pose.elbows[i]
            elbow, hand = limb(sp, a, upper, a + e, fore, f)
        else:
            dirx = 1 if i == 0 else -1
            sp = (x + dirx * (tw / 2 - 0.3), sh_y + 1)
            a, e = pose.arms[i], pose.elbows[i]
            elbow, hand = limb(sp, a, upper, a + e, fore, dirx)
        sleeve = look.dress or look.gown or look.shirt
        sl = sleeve if near else far(sleeve)
        sk = look.skin if near else far(look.skin)
        part = f"arm{i}"
        long_sleeve = look.sleeves == "long" or look.dress or look.gown
        b.capsule(sp, elbow, ra * (1.35 if look.gown else 1.12), part, sl)
        b.capsule(elbow, hand, ra * (1.25 if look.gown else 1), part, sl if long_sleeve else sk)
        b.disc(hand[0], hand[1], ra * 1.05, part, sk)
        return hand

    # Back to front.
    if side:
        arm(1, False)
        if look.bag:
            bx = x - f * (tw / 2 + 1.2) + lean * 0.4
            b.poly([(bx - 1.6, sh_y + 1), (bx + 1.6, sh_y + 1), (bx + 1.9, hip_y), (bx - 1.9, hip_y)], "bag", look.bag)
        leg(1, False)
    else:
        if look.bag and facing == 2:
            pass
        leg(0, True)
        leg(1, True)

    if look.hair_style == "long" or look.hair_style == "pony":
        if side:
            if look.hair_style == "long":
                b.capsule((hx - f * R * 0.5, hy), (x - f * (tw / 2 - 0.5) + lean * 0.5, sh_y + h * 0.16), R * 0.62, "hairback", far(look.hair))
            else:
                b.capsule((hx - f * R * 0.9, hy - R * 0.3), (hx - f * R * 1.6, hy + R * 0.9), R * 0.42, "hairback", far(look.hair))
        else:
            b.poly([(hx - R * 1.05, hy), (hx + R * 1.05, hy), (hx + R * 1.0, sh_y + h * 0.17), (hx - R * 1.0, sh_y + h * 0.17)], "hairback", far(look.hair))

    # Torso, or gown, or ao dai.
    if look.gown:
        hem = feet - h * 0.11
        b.poly([(x - tw / 2 - 0.6 + lean * 0.4, sh_y), (x + tw / 2 + 0.6 + lean * 0.4, sh_y), (x + tw / 2 + 2.2 + (0.6 if side else 0), hem), (x - tw / 2 - 2.2, hem)], "torso", look.gown)
        if side:
            b.capsule((x + f * (tw / 2 - 0.5) + lean * 0.4, sh_y + 0.5), (x + f * (tw / 2 + 0.6), hip_y + h * 0.05), 0.6, "stole", look.stole)
        else:
            for sx in (-1, 1):
                b.capsule((x + sx * 1.2, sh_y + 0.5), (x + sx * 1.3, hip_y + h * 0.08), 0.6, "stole", look.stole)
    elif look.dress:
        knee_y = hip_y + thigh * 1.15
        b.poly([(x - tw / 2 + lean * 0.4, sh_y), (x + tw / 2 + lean * 0.4, sh_y), (x + tw / 2, hip_y), (x - tw / 2, hip_y)], "torso", look.dress)
        if side:
            sway = pose.legs[0] * 0.08
            b.poly([(x, hip_y - 1), (x + f * tw / 2, hip_y - 1), (x + f * (tw / 2 + 1.2) + sway, knee_y + 2), (x + f * 0.2 + sway, knee_y + 2)], "panelf", look.dress)
            b.poly([(x - f * tw / 2, hip_y - 1), (x, hip_y - 1), (x - f * 0.6 - sway * 1.5, knee_y + 3), (x - f * (tw / 2 + 1.8) - sway * 1.5, knee_y + 3)], "panelb", far(look.dress))
        else:
            b.poly([(x - tw / 2, hip_y - 1), (x + tw / 2, hip_y - 1), (x + tw / 2 + 0.6, knee_y + 3), (x - tw / 2 - 0.6, knee_y + 3)], "panelf", look.dress)
    else:
        b.poly([(x - tw / 2 + lean * 0.5, sh_y), (x + tw / 2 + lean * 0.5, sh_y), (x + tw / 2 + 0.2, hip_y + 0.6), (x - tw / 2 - 0.2, hip_y + 0.6)], "torso", look.shirt)
        if look.skirt:
            b.poly([(x - tw / 2 - 0.2, hip_y - 0.4), (x + tw / 2 + 0.2, hip_y - 0.4), (x + tw / 2 + 1.4, hip_y + thigh * 0.95), (x - tw / 2 - 1.4, hip_y + thigh * 0.95)], "skirt", look.skirt)
        # Collar.
        if h >= 16:
            cx = x + lean * 0.5 + (f * (tw / 2 - 1.2) if side else 0)
            b.put(round(cx - (0 if side else 1)), round(sh_y), "collar", mix(look.shirt, "#ffffff", 0.5), flat=True)
            if not side:
                b.put(round(cx), round(sh_y), "collar", mix(look.shirt, "#ffffff", 0.5), flat=True)
    if facing == 2 and look.bag:
        b.poly([(x - tw / 2 + 0.6, sh_y + 1.5), (x + tw / 2 - 0.6, sh_y + 1.5), (x + tw / 2 - 0.4, hip_y - 0.2), (x - tw / 2 + 0.4, hip_y - 0.2)], "bag", look.bag)

    if side:
        leg(0, True)

    # Head: neck, face, hair, details.
    b.capsule((hx - 0.3 * f, top + 2 * R - 0.5), (x + lean * 0.5, sh_y + 0.5), max(0.8, R * 0.38), "neck", mix(look.skin, DARK, 0.15))
    b.disc(hx, hy, R, "head", look.skin)
    hs = look.hair_style
    if look.helmet:
        b.disc(hx, hy - 0.2, R + 0.55, "hair", look.helmet, keep=lambda dx, dy: dy < 0.4 or (side and dx * f < -0.3 and dy < R * 0.6))
        if side:
            b.capsule((hx + f * R * 0.2, hy + 0.3), (hx + f * (R + 0.6), hy + 0.3), 0.55, "visor", mix(look.helmet, DARK, 0.4))
    elif hs != "bald":
        if facing == 2:
            b.disc(hx, hy, R + 0.35, "hair", look.hair)
        elif side:
            b.disc(hx, hy - 0.15, R + 0.35, "hair", look.hair, keep=lambda dx, dy: dy < -R * 0.28 or dx * f < -R * 0.05 or (dy < R * 0.1 and dx * f > R * 0.55))
        else:
            b.disc(hx, hy - 0.15, R + 0.35, "hair", look.hair, keep=lambda dx, dy: dy < -R * 0.3 or abs(dx) > R * 0.72 or (dy < -R * 0.05 and abs(dx) < R * 0.5 and dx < 0))
        if h >= 30:
            # A sheen across the crown.
            for yy in range(math.floor(hy - R), math.ceil(hy)):
                for xx in range(math.floor(hx - R), math.ceil(hx + R)):
                    dx, dy = xx + 0.5 - hx, yy + 0.5 - hy
                    if b.part.get((xx, yy)) == "hair" and -0.62 * R < dy < -0.42 * R and -0.7 * R < dx * (f if side else 1) < 0.2 * R:
                        b.put(xx, yy, "hair", mix(look.hair, "#ffffff", 0.22), flat=True)
        if hs == "bob" and side:
            b.capsule((hx - f * R * 0.3, hy + R * 0.2), (hx - f * R * 0.9, hy + R * 0.95), R * 0.45, "hair", look.hair)
    if look.cap:
        b.poly([(hx - R - 1.6, hy - R - 0.6), (hx + R + 1.6, hy - R - 0.6), (hx + R + 1.6, hy - R + 0.4), (hx - R - 1.6, hy - R + 0.4)], "cap", look.cap)
        b.disc(hx, hy - R * 0.55, R * 0.82, "capb", look.cap, keep=lambda dx, dy: dy < 0)
        tx = hx + (R + 1.2) * (-f if side else 1)
        for k in range(2 + h // 14):
            b.put(math.floor(tx), math.floor(hy - R + 0.4 + k), "tassel", "#ffd34a", flat=True)

    # Front arm and what it holds.
    hands = []
    if side:
        hands.append(arm(0, True))
    else:
        hands.append(arm(0, True))
        hands.append(arm(1, True))
    if look.hold:
        hxh, hyh = hands[0]
        bx, by = hxh + (f * 1.5 if side else -tw / 2 + 0.5), hyh - 2.2
        b.poly([(bx - 1.6, by + 0.8), (bx + 1.6, by + 0.8), (bx, by + 5)], "wrap", "#f2e2c4")
        for dx, dy, k in ((-1.5, 0, 0), (0, -1, 1), (1.5, 0, 2), (-0.6, -2, 1), (0.8, -2.2, 0), (-2.2, -1.4, 2), (2.2, -1.4, 1)):
            col = [look.hold, mix(look.hold, "#ffffff", 0.35), mix(look.hold, "#ffd34a", 0.4)][k]
            b.disc(bx + dx, by + dy, 1.05, f"fl{k}", col)
        b.put(math.floor(bx - 2), math.floor(by + 0.5), "leaf", "#3a9a4a", flat=True)
        b.put(math.floor(bx + 2), math.floor(by + 1), "leaf", "#3a9a4a", flat=True)

    if look.prop:
        hxh, hyh = hands[0]
        px_, py_ = math.floor(hxh), math.floor(hyh)
        d = f if side else 1
        if look.prop == "phone":
            b.put(px_ + d, py_ - 1, "phone", "#1a1a2a", flat=True)
            b.put(px_ + d, py_, "phone", "#1a1a2a", flat=True)
            b.put(px_ + d, py_ - 2, "phone", "#8ad0ff", flat=True)
        elif look.prop == "camera":
            for dx in range(-1, 3):
                for dy in range(-1, 2):
                    b.put(px_ + d * dx, py_ + dy, "camera", "#2a2a3a", flat=True)
            b.put(px_ + d * 3, py_, "camera", "#8ab0d8", flat=True)
            b.put(px_ + d * 1, py_ - 2, "camera", "#3a3a4a", flat=True)
        elif look.prop == "lantern":
            # A star lantern on a stick held up and ahead.
            col = look.extra.get("lantern", "#ffb040")
            top_y = py_ - max(3, round(h * 0.3))
            for yy in range(top_y, py_ + 1):
                b.put(px_ + d * (1 if yy < (top_y + py_) // 2 else 0), yy, "stick", "#8a6a3a", flat=True)
            sx, sy = px_ + d, top_y - 2
            star = [(0, -2), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (-1, 2), (1, 2)]
            for dx, dy in star:
                b.put(sx + dx, sy + dy, "lantern", col, flat=True)
            b.put(sx, sy, "lantern", "#ffe9a0", flat=True)
            b.put(sx, sy + 1, "lantern", mix(col, "#ffffff", 0.4), flat=True)
        elif look.prop == "umbrella":
            col = look.extra.get("umbrella", "#d8473a")
            cx_ = px_ + d
            top_y = math.floor(top) - 1
            for yy in range(top_y, py_ + 1):
                b.put(cx_, yy, "stick", "#2a2a34", flat=True)
            half = max(4, round(h * 0.42))
            for dy in range(0, max(3, round(h * 0.2))):
                w = round(half * math.sqrt(min(1, (dy + 1.2) / max(3, round(h * 0.2)))))
                for dx in range(-w, w + 1):
                    shade = mix(col, "#ffffff", 0.3) if dy == 0 or dx * d < -w + 2 else (mix(col, DARK, 0.25) if dx * d > w - 2 else col)
                    b.put(cx_ + dx, top_y - max(3, round(h * 0.2)) + dy + 1, "umb", shade, flat=True)
        elif look.prop == "folder":
            fc = look.extra.get("folder", "#f4c84a")
            for dy in range(-1, 4):
                for dx in (0, 1):
                    b.put(px_ + d * dx, py_ + dy, "folder", fc)

    # Face.
    if facing != 2:
        ey = math.floor(hy + R * 0.12)
        eye = mix(look.skin, DARK, 0.45) if pose.blink else "#1a1222"
        if side:
            ex = math.floor(hx + f * R * 0.5)
            b.put(ex, ey, "eye", eye, flat=True)
            if h >= 20:
                b.put(ex - f, math.floor(ey + R * 0.5), "cheek", mix(look.skin, "#ff7a8a", 0.35), flat=True)
                b.put(math.floor(hx - f * R * 0.15), math.floor(hy + R * 0.1), "ear", mix(look.skin, DARK, 0.18), flat=True)
        else:
            for sx in (-1, 1):
                b.put(math.floor(hx + sx * R * 0.42), ey, "eye", eye, flat=True)
            if h >= 20:
                b.put(math.floor(hx), math.floor(hy + R * 0.62), "mouth", mix(look.skin, "#a03a4a", 0.45), flat=True)
                for sx in (-1, 1):
                    b.put(math.floor(hx + sx * R * 0.62), math.floor(hy + R * 0.48), "cheek", mix(look.skin, "#ff7a8a", 0.3), flat=True)

    b.render(c, outline=outline)


def sprite(x: float, feet: float, h: int, look: Look, pose: Pose | None = None, facing: int = 1, outline: bool = True) -> Canvas:
    c = Canvas()
    draw(c, x, feet, h, look, pose, facing, outline)
    return c
