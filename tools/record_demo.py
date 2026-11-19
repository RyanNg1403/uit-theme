"""Record drafts/demo/index.html (tools/build_demo.mjs) into docs/demo.gif.

usage: uv run --with playwright python tools/record_demo.py [--width 720] [--fps 10]

Runs headless Chromium and grabs frames through the DevTools screencast, so nothing on
the screen is recorded. The frames are resampled to a fixed rate and turned into a GIF
with ffmpeg (needs ffmpeg on PATH).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import os
import shutil
import subprocess

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "drafts", "demo")
FRAMES = os.path.join(DEMO, "frames")
W, H = 1280, 768


async def capture() -> list[tuple[float, bytes]]:
    shots: list[tuple[float, bytes]] = []
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch()
        except Exception:  # no Playwright build of Chromium for this version: use the installed Chrome
            browser = await p.chromium.launch(channel="chrome")
        page = await browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        cdp = await page.context.new_cdp_session(page)

        async def on_frame(ev):
            shots.append((ev["metadata"]["timestamp"], base64.b64decode(ev["data"])))
            await cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})

        cdp.on("Page.screencastFrame", lambda ev: asyncio.ensure_future(on_frame(ev)))
        await page.goto(f"file://{DEMO}/index.html")
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(1500)
        await cdp.send("Page.startScreencast", {"format": "png", "maxWidth": W, "maxHeight": H, "everyNthFrame": 1})
        await page.evaluate("fetch = () => Promise.resolve({ ok: true })")
        await page.wait_for_function("document.title === 'done'", timeout=120_000, polling=500)
        await cdp.send("Page.stopScreencast")
        await browser.close()
    return sorted(shots)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "demo.gif"))
    a = ap.parse_args()

    shots = asyncio.run(capture())
    shutil.rmtree(FRAMES, ignore_errors=True)
    os.makedirs(FRAMES)
    t0, t1 = shots[0][0], shots[-1][0]
    n = int((t1 - t0) * a.fps)
    j = 0
    for i in range(n):
        t = t0 + i / a.fps
        while j + 1 < len(shots) and shots[j + 1][0] <= t:
            j += 1
        with open(os.path.join(FRAMES, f"f{i:05d}.png"), "wb") as f:
            f.write(shots[j][1])
    print(f"{len(shots)} screencast frames over {t1 - t0:.1f}s -> {n} frames at {a.fps} fps")

    graph = (
        f"scale={a.width}:-2:flags=lanczos,split[a][b];"
        "[a]palettegen=stats_mode=diff:max_colors=128[p];"
        "[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
    )
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(FRAMES, "f%05d.png"), "-filter_complex", graph, "-loop", "0", a.out],
        check=True,
    )
    print(a.out, os.path.getsize(a.out) // 1024, "KB")


if __name__ == "__main__":
    main()
