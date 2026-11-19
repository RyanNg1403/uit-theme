"""Re-encode a generated scene's plain pixel paths in the shorter forms scenekit writes.

usage: uv run python tools/repack.py navy [metro ...]

For scenes whose generators are not in this repo (navy, metro, silicon). Every
`<path stroke="#c" d="...">` drawn only of `h` rows on half-pixel lines is decoded to
its pixels and written again as scenekit.paths would: rows, upright `v` runs or a
filled outline, whichever is shortest. Pixels stay exactly the same; paths with any
other attribute (classes, opacity, dashes) are left alone. Rewrites hooks/scenes/<name>.ts.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from scenekit import check_size, fill_d, path_d  # noqa: E402

PATH = re.compile(r'<path stroke="(#[0-9a-f]{6})" d="([^"]*)"/>')
TOKEN = re.compile(r"[Mmh]|-?(?:\d+(?:\.\d*)?|\.\d+)")


def rows(d: str) -> set[tuple[int, int]] | None:
    """The pixels of a path of moves and `h` runs on half-pixel lines; None if it is
    anything else."""
    toks = TOKEN.findall(d)
    if "".join(toks).replace("-", "") != re.sub(r"[\s-]", "", d):
        return None
    px: set[tuple[int, int]] = set()
    x = y = 0.0
    i = 0
    try:
        while i < len(toks):
            t = toks[i]
            if t in "Mm":
                a, b = float(toks[i + 1]), float(toks[i + 2])
                x, y = (a, b) if t == "M" else (x + a, y + b)
                i += 3
            elif t == "h":
                n = float(toks[i + 1])
                if n <= 0 or n % 1 or x % 1 or y % 1 != 0.5:
                    return None
                px.update((int(x) + k, int(y - 0.5)) for k in range(int(n)))
                x += n
                i += 2
            else:
                return None
    except (IndexError, ValueError):
        return None
    return px


def repack(svg: str) -> str:
    def one(m: re.Match) -> str:
        col, d = m.groups()
        px = rows(d)
        if not px:
            return m.group(0)
        stroke, fill = path_d(px), fill_d(px)
        best = f'<path fill="{col}" d="{fill}"/>' if len(fill) + 2 < len(stroke) else f'<path stroke="{col}" d="{stroke}"/>'
        return best if len(best) < len(m.group(0)) else m.group(0)

    return PATH.sub(one, svg)


def main() -> None:
    for name in sys.argv[1:]:
        path = f"hooks/scenes/{name}.ts"
        src = open(path).read()
        head = src[: src.index("export const SCENE = ")]
        svg = json.loads(src[len(head) + len("export const SCENE = ") :].strip())
        out = repack(svg)
        check_size(name, out)
        if "repacked by tools/repack.py" not in head:
            head = head.rstrip("\n") + " Pixel paths repacked by tools/repack.py.\n"
        with open(path, "w") as f:
            f.write(f"{head}export const SCENE = {json.dumps(out)}\n")
        print(name, len(svg), "->", len(out))


if __name__ == "__main__":
    main()
