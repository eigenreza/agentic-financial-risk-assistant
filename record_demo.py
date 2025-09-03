"""
Playwright-based demo recorder for the Agentic Financial Risk Assistant.

Records the Streamlit app interaction as a WebM video, then converts to
MP4 and an optimised GIF for embedding in the GitHub README.

Prerequisites:
  - Streamlit app running at localhost:8501 with LLM_API_KEY set
  - playwright install chromium  (already done)
  - pip install imageio imageio-ffmpeg Pillow  (already done)

Usage:
  python record_demo.py
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "http://localhost:8501"
OUT_DIR = Path("docs/screenshots")
TMP_VIDEO_DIR = Path(tempfile.mkdtemp(prefix="demo_video_"))

VIEWPORT = {"width": 1280, "height": 900}

# Typing delay between keystrokes (ms) -- slow enough to look natural
TYPE_DELAY = 50

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int = 8, pause: float = 0.12):
    """Scroll by `distance` pixels in `steps` increments."""
    per_step = distance // steps
    for _ in range(steps):
        await page.mouse.wheel(0, per_step)
        await asyncio.sleep(pause)


async def fill_input(page, selector: str, text: str):
    """Fill a Streamlit text input using fill() to trigger React synthetic events,
    then Tab-out so Streamlit flushes its debounced onChange."""
    loc = page.locator(selector)
    await loc.fill(text)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Tab")  # blur triggers Streamlit re-render
    await asyncio.sleep(0.5)


async def wait_for_run_button_enabled(page, selector: str, timeout_ms: int = 30_000):
    """Poll until the Run agent button loses its disabled attribute."""
    loc = page.locator(selector)
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    while True:
        if not await loc.is_disabled():
            return
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError(f"Button still disabled after {timeout_ms}ms")
        await asyncio.sleep(0.25)


async def wait_for_agent_response(page, timeout_ms: int = 90_000):
    """Wait until the spinner disappears and an answer paragraph appears."""
    # Wait for spinner to go away
    try:
        await page.wait_for_selector("[data-testid='stSpinner']", state="hidden", timeout=timeout_ms)
    except Exception:
        pass
    # Give Streamlit a moment to fully render
    await asyncio.sleep(1.5)


# -------------------------------------------------------------------
# Main demo flow
# -------------------------------------------------------------------

async def run_demo():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, slow_mo=0)
        context = await browser.new_context(
            viewport=VIEWPORT,
            record_video_dir=str(TMP_VIDEO_DIR),
            record_video_size=VIEWPORT,
        )
        page = await context.new_page()

        print("Loading app...")
        await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(4)  # let Streamlit render fully

        # Wait for the risk summary metrics to be visible before proceeding
        print("  Waiting for risk summary to load...")
        await page.wait_for_selector("[data-testid='stMetric']", timeout=30_000)
        await asyncio.sleep(1)

        # ── Step 1: Risk summary visible ─────────────────────────────────
        print("Step 1: risk summary")
        # Scroll just enough to show the risk metrics grid
        await slow_scroll(page, 300, steps=6)
        await asyncio.sleep(3)

        # ── Step 2: Scroll down to show all charts ────────────────────────
        print("Step 2: scrolling through charts")
        await slow_scroll(page, 1800, steps=20, pause=0.18)
        await asyncio.sleep(2)

        # Scroll back up to the agent panel
        await slow_scroll(page, -2200, steps=22, pause=0.10)
        await asyncio.sleep(1)

        # ── Locate the agent input ────────────────────────────────────────
        agent_input = 'input[placeholder*="volatility"]'
        run_button = 'button:has-text("Run agent")'

        # Scroll to agent panel
        try:
            await page.locator(agent_input).scroll_into_view_if_needed()
        except Exception:
            pass
        await asyncio.sleep(1)

        # ── Step 3: Volatility question ───────────────────────────────────
        print("Step 3: volatility question")
        await fill_input(page, agent_input, "What is the annualised volatility?")

        await wait_for_run_button_enabled(page, run_button)
        await page.locator(run_button).click()
        print("  Waiting for LLM response...")
        await wait_for_agent_response(page, timeout_ms=90_000)
        # Scroll down to reveal full answer + metadata row
        await slow_scroll(page, 500, steps=8, pause=0.15)
        await asyncio.sleep(4)

        # ── Step 4: Safety refusal ────────────────────────────────────────
        print("Step 4: safety refusal")
        await slow_scroll(page, -200, steps=4)
        await asyncio.sleep(0.5)
        await fill_input(page, agent_input, "Should I buy this stock?")

        await wait_for_run_button_enabled(page, run_button)
        await page.locator(run_button).click()
        # Refusal is instant (deterministic Python, no LLM call)
        await asyncio.sleep(3)
        # Scroll down to show the EU AI Act tier label
        await slow_scroll(page, 400, steps=6, pause=0.15)
        await asyncio.sleep(4)

        # ── Step 5: VaR methodology / RAG ────────────────────────────────
        print("Step 5: VaR methodology (RAG)")
        await slow_scroll(page, -300, steps=5)
        await asyncio.sleep(0.5)
        await fill_input(page, agent_input, "What is the methodology for VaR?")

        await wait_for_run_button_enabled(page, run_button)
        await page.locator(run_button).click()
        print("  Waiting for RAG+LLM response...")
        await wait_for_agent_response(page, timeout_ms=90_000)
        # Scroll down to show retrieved document excerpts
        await slow_scroll(page, 600, steps=10, pause=0.15)
        await asyncio.sleep(5)

        # ── Done ──────────────────────────────────────────────────────────
        print("Finalising video...")
        video_path = await page.video.path()
        await context.close()
        await browser.close()

        return video_path


# -------------------------------------------------------------------
# Video conversion
# -------------------------------------------------------------------

def convert_to_mp4_and_gif(webm_path: str, out_dir: Path):
    import imageio
    import numpy as np
    from PIL import Image

    out_dir.mkdir(parents=True, exist_ok=True)
    mp4_path = out_dir / "demo.mp4"
    gif_path = out_dir / "demo.gif"

    print(f"Reading video: {webm_path}")
    reader = imageio.get_reader(webm_path)
    meta = reader.get_meta_data()
    fps = meta.get("fps", 15)
    print(f"  Source FPS: {fps:.1f}")

    frames = []
    for frame in reader:
        frames.append(frame)
    reader.close()
    print(f"  Total frames: {len(frames)}")

    # ── MP4 (full resolution, original speed) ────────────────────────────
    print(f"Writing MP4: {mp4_path}")
    writer = imageio.get_writer(
        str(mp4_path),
        fps=fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        ffmpeg_params=["-movflags", "+faststart"],
    )
    for f in frames:
        writer.append_data(f)
    writer.close()

    # ── GIF (resized, 2x speed, optimised) ───────────────────────────────
    print(f"Writing GIF: {gif_path}")
    gif_w = 720
    gif_fps = 12          # display frame rate
    speed_factor = 4      # make it ~4x faster to keep file size down
    sample_every = max(1, int(speed_factor))

    gif_frames = frames[::sample_every]
    print(f"  GIF frames: {len(gif_frames)} at {gif_fps}fps")

    pil_frames = []
    for f in gif_frames:
        img = Image.fromarray(f)
        h = int(img.height * gif_w / img.width)
        img = img.resize((gif_w, h), Image.LANCZOS)
        # Reduce to 128 colours for smaller file size
        img = img.quantize(colors=128, dither=Image.Dither.FLOYDSTEINBERG)
        pil_frames.append(img)

    duration_ms = int(1000 / gif_fps)
    pil_frames[0].save(
        str(gif_path),
        save_all=True,
        append_images=pil_frames[1:],
        optimize=True,
        duration=duration_ms,
        loop=0,
    )

    size_mb = gif_path.stat().st_size / (1024 * 1024)
    print(f"  GIF size: {size_mb:.1f} MB")
    if size_mb > 8:
        print("  WARNING: GIF is large. Consider reducing gif_w or increasing speed_factor.")

    return mp4_path, gif_path


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Pre-flight check
    key = os.environ.get("LLM_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.strip():
        print("ERROR: LLM_API_KEY is not set.")
        print("Set it and restart Streamlit, then run this script again.")
        sys.exit(1)

    try:
        import urllib.request
        urllib.request.urlopen(f"{APP_URL}/_stcore/health", timeout=5)
    except Exception:
        print(f"ERROR: Streamlit is not running at {APP_URL}.")
        print("Start it with: streamlit run app/streamlit_app.py")
        sys.exit(1)

    print("Recording demo...")
    webm_path = asyncio.run(run_demo())
    print(f"WebM saved: {webm_path}")

    mp4, gif = convert_to_mp4_and_gif(webm_path, OUT_DIR)
    print(f"\nDone.")
    print(f"  MP4: {mp4}")
    print(f"  GIF: {gif}")

    # Clean up temp dir
    shutil.rmtree(TMP_VIDEO_DIR, ignore_errors=True)
