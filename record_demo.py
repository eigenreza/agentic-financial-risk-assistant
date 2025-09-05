"""
Playwright-based demo recorder for the Agentic Financial Risk Assistant.

Records the Streamlit app interaction as a WebM video, then converts to
MP4 and an optimised GIF for embedding in the GitHub README.

Scenarios covered:
  1. App loading with Equinor sample data and risk summary metrics visible
  2. All 5 charts (price, returns, rolling vol, drawdown, VaR) scrolled slowly
  3. Agent: "What is the annualised volatility?" — tool call + structured result
  4. Agent: "What is the methodology for VaR?" — RAG citation with document source
  5. Agent: "Should I buy this stock?" — EU AI Act Unacceptable risk refusal
  6. Agent: "Is this suitable for my pension?" — human review warning

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
TYPE_DELAY = 50


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int = 8, pause: float = 0.12):
    per_step = distance // steps
    for _ in range(steps):
        await page.mouse.wheel(0, per_step)
        await asyncio.sleep(pause)


async def clear_and_fill(page, selector: str, text: str):
    """Clear the text input, type new text, and blur to trigger Streamlit re-render."""
    loc = page.locator(selector)
    await loc.scroll_into_view_if_needed()
    await loc.click(click_count=3)  # select all
    await asyncio.sleep(0.2)
    await loc.fill(text)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Tab")
    await asyncio.sleep(0.6)


async def click_run(page):
    run_button = 'button:has-text("Run agent")'
    # Wait until button is enabled
    loc = page.locator(run_button)
    deadline = asyncio.get_event_loop().time() + 15
    while True:
        if not await loc.is_disabled():
            break
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError("Run agent button still disabled")
        await asyncio.sleep(0.25)
    await loc.click()


async def wait_for_agent_response(page, timeout_ms: int = 120_000):
    try:
        await page.wait_for_selector("[data-testid='stSpinner']", state="hidden", timeout=timeout_ms)
    except Exception:
        pass
    # Extra settle time for Streamlit to fully render the response
    await asyncio.sleep(2.0)


async def scroll_to_agent_panel(page):
    try:
        await page.locator("text=Ask the Risk Agent").scroll_into_view_if_needed()
    except Exception:
        pass
    await asyncio.sleep(0.8)


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

        # ── STEP 1: Load app with Equinor sample data ─────────────────────
        print("Step 1: loading app with Equinor data...")
        await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(5)

        # Wait for risk summary metrics
        await page.wait_for_selector("[data-testid='stMetric']", timeout=30_000)
        await asyncio.sleep(1.5)

        # Scroll gently to reveal full risk summary panel
        await slow_scroll(page, 350, steps=8, pause=0.14)
        await asyncio.sleep(3)

        # ── STEP 2: All 5 charts — slow scroll ────────────────────────────
        print("Step 2: scrolling through all 5 charts...")
        await slow_scroll(page, 2200, steps=28, pause=0.20)
        await asyncio.sleep(2)

        # Scroll back to top for agent section
        await slow_scroll(page, -2600, steps=26, pause=0.09)
        await asyncio.sleep(1)

        # ── STEP 3: Annualised volatility (tool call) ─────────────────────
        print("Step 3: volatility question (tool call)...")
        agent_input = 'input[placeholder*="volatility"]'
        await scroll_to_agent_panel(page)
        await clear_and_fill(page, agent_input, "What is the annualised volatility?")
        await click_run(page)
        print("  Waiting for LLM tool-call response...")
        await wait_for_agent_response(page, timeout_ms=120_000)
        await slow_scroll(page, 600, steps=10, pause=0.15)
        await asyncio.sleep(4)

        # ── STEP 4: VaR methodology (RAG citation) ────────────────────────
        print("Step 4: VaR methodology (RAG)...")
        await scroll_to_agent_panel(page)
        await clear_and_fill(page, agent_input, "What is the methodology for VaR?")
        await click_run(page)
        print("  Waiting for RAG+LLM response...")
        await wait_for_agent_response(page, timeout_ms=120_000)
        await slow_scroll(page, 700, steps=12, pause=0.15)
        # Expand the retrieved document excerpts if present
        try:
            expander = page.locator("text=Retrieved document excerpts")
            if await expander.is_visible():
                await expander.click()
                await asyncio.sleep(1)
                await slow_scroll(page, 300, steps=6, pause=0.15)
        except Exception:
            pass
        await asyncio.sleep(4)

        # ── STEP 5: "Should I buy this stock?" — EU AI Act refusal ────────
        print("Step 5: EU AI Act refusal (Unacceptable)...")
        await scroll_to_agent_panel(page)
        await clear_and_fill(page, agent_input, "Should I buy this stock?")
        await click_run(page)
        # Refusal is deterministic Python — no LLM call, so it's fast
        await asyncio.sleep(2)
        await slow_scroll(page, 500, steps=8, pause=0.15)
        await asyncio.sleep(4)

        # ── STEP 6: "Is this suitable for my pension?" — human review ─────
        print("Step 6: human review warning (pension question)...")
        await scroll_to_agent_panel(page)
        await clear_and_fill(page, agent_input, "Is this suitable for my pension?")
        await click_run(page)
        print("  Waiting for human-review response...")
        await wait_for_agent_response(page, timeout_ms=120_000)
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

    # ── GIF (resized, 4x speed, optimised for <10 MB) ────────────────────
    print(f"Writing GIF: {gif_path}")
    gif_w = 720
    gif_fps = 12
    speed_factor = 4
    sample_every = max(1, int(speed_factor))

    gif_frames = frames[::sample_every]
    print(f"  GIF frames: {len(gif_frames)} at {gif_fps} fps")

    pil_frames = []
    for f in gif_frames:
        img = Image.fromarray(f)
        h = int(img.height * gif_w / img.width)
        img = img.resize((gif_w, h), Image.LANCZOS)
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
    if size_mb > 9:
        # Aggressively shrink: reduce width to 600 px and increase speed
        print("  GIF too large — re-encoding at 600 px / 6x speed...")
        gif_w2 = 600
        sample_every2 = 6
        gif_frames2 = frames[::sample_every2]
        pil2 = []
        for f in gif_frames2:
            img = Image.fromarray(f)
            h = int(img.height * gif_w2 / img.width)
            img = img.resize((gif_w2, h), Image.LANCZOS)
            img = img.quantize(colors=96, dither=Image.Dither.FLOYDSTEINBERG)
            pil2.append(img)
        pil2[0].save(
            str(gif_path),
            save_all=True,
            append_images=pil2[1:],
            optimize=True,
            duration=duration_ms,
            loop=0,
        )
        size_mb = gif_path.stat().st_size / (1024 * 1024)
        print(f"  Re-encoded GIF size: {size_mb:.1f} MB")

    return mp4_path, gif_path


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    import sys

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

    print("Recording demo — this will take a few minutes...")
    webm_path = asyncio.run(run_demo())
    print(f"WebM saved: {webm_path}")

    mp4, gif = convert_to_mp4_and_gif(webm_path, OUT_DIR)
    print(f"\nDone.")
    print(f"  MP4: {mp4}")
    print(f"  GIF: {gif}")

    shutil.rmtree(TMP_VIDEO_DIR, ignore_errors=True)
