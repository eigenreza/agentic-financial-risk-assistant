"""
Record demo_01_dashboard.mp4

Content:
  - Start at very top of page
  - Single smooth uniform scroll all the way down
  - Stop just below the agent question input box
  - Cut. No pauses, no zooming, no font changes.
"""

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "http://localhost:8501"
OUT_DIR = Path("docs/screenshots")


async def record() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="demo01_mp4_"))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-extensions"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            record_video_dir=str(tmp),
            record_video_size={"width": 1280, "height": 900},
        )
        page = await ctx.new_page()

        print("Loading app...")
        await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(4)   # wait for full render, hold at top

        # Wait for charts to be present before scrolling
        await page.wait_for_selector("[data-testid='stPlotlyChart']", timeout=30_000)
        await asyncio.sleep(2)   # extra settle time so charts fully render

        # Move mouse to centre of main content area, then wheel-scroll uniformly
        print("Smooth uniform scroll...")
        await page.mouse.move(640, 450)   # centre of 1280x900 viewport
        agent_input = page.locator('input[placeholder*="volatility"]')

        step_px    = 8     # pixels per wheel step
        step_pause = 0.04  # seconds between steps — steady, natural pace
        max_steps  = 3000

        for i in range(max_steps):
            await page.mouse.wheel(0, step_px)
            await asyncio.sleep(step_pause)

            # Every 30 steps check if agent input is in view
            if i % 30 == 0:
                try:
                    box = await agent_input.bounding_box()
                    if box and box["y"] + box["height"] < 900:
                        # Input visible — scroll a little more to show just below it
                        for _ in range(50):
                            await page.mouse.wheel(0, step_px)
                            await asyncio.sleep(step_pause)
                        break
                except Exception:
                    pass

        await asyncio.sleep(1.5)  # hold at end before cut

        video_path = await page.video.path()
        await ctx.close()
        await browser.close()

    return Path(video_path)


def convert_to_mp4(webm_path: Path) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "demo_01_dashboard.mp4"

    print(f"Converting to MP4...")
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", str(webm_path),
        "-vcodec", "libx264",
        "-crf", "20",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out),
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("ffmpeg error:", result.stderr[-2000:])
        raise RuntimeError("ffmpeg failed")

    mb = out.stat().st_size / (1024 * 1024)
    print(f"Done: {out.name} ({mb:.1f} MB)")
    return out


if __name__ == "__main__":
    print("Recording...")
    webm = asyncio.run(record())
    print(f"WebM: {webm}")
    mp4 = convert_to_mp4(webm)
    print(f"MP4: {mp4}")
    shutil.rmtree(webm.parent, ignore_errors=True)
