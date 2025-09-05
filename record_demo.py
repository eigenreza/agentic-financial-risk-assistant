"""
Playwright-based demo recorder for the Agentic Financial Risk Assistant.

Records the Streamlit app interaction as a WebM video, then converts to
MP4 and an optimised GIF for embedding in the GitHub README.

Scenarios covered:
  1. App loading with Equinor sample data and risk summary metrics visible
  2. All 5 charts scrolled one by one with a 2-3 s pause on each
  3. Agent: "What is the annualised volatility?" — tool call + structured result
  4. Agent: "What is the methodology for VaR?" — RAG citation with document source
  5. Agent: "Should I buy this stock?" — EU AI Act Unacceptable risk refusal
  6. Agent: "Is this suitable for my pension?" — human review warning

Prerequisites:
  - Streamlit app running at localhost:8501 with LLM_API_KEY set
  - playwright install chromium
  - pip install imageio imageio-ffmpeg Pillow

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


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int = 8, pause: float = 0.14):
    """Scroll by `distance` pixels in `steps` increments with a pause between steps."""
    per_step = distance // max(steps, 1)
    for _ in range(steps):
        await page.mouse.wheel(0, per_step)
        await asyncio.sleep(pause)


async def zoom_to(page, pct: int):
    """Apply CSS zoom to the entire page so text/UI is more readable in the recording."""
    await page.evaluate(f"document.body.style.zoom = '{pct}%'")
    await asyncio.sleep(0.4)


async def scroll_element_into_center(page, locator):
    """Scroll element into view then nudge so it sits in the middle of the viewport."""
    await locator.scroll_into_view_if_needed()
    await asyncio.sleep(0.6)
    # Small extra scroll to bring element away from the very top edge
    await page.mouse.wheel(0, 80)
    await asyncio.sleep(0.4)


async def clear_and_fill(page, selector: str, text: str):
    """Select-all, fill new text, then Tab-out to flush Streamlit's debounced onChange."""
    loc = page.locator(selector)
    await scroll_element_into_center(page, loc)
    await loc.click(click_count=3)
    await asyncio.sleep(0.2)
    await loc.fill(text)
    await asyncio.sleep(0.35)
    await page.keyboard.press("Tab")
    await asyncio.sleep(0.7)


async def click_run(page):
    """Wait until the Run agent button is enabled, then click it."""
    run_button = 'button:has-text("Run agent")'
    loc = page.locator(run_button)
    deadline = asyncio.get_event_loop().time() + 20
    while True:
        if not await loc.is_disabled():
            break
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError("Run agent button still disabled after 20 s")
        await asyncio.sleep(0.25)
    await loc.click()


async def wait_for_agent_response(page, timeout_ms: int = 120_000):
    """Wait for the spinner to vanish, then let Streamlit finish rendering."""
    try:
        await page.wait_for_selector("[data-testid='stSpinner']", state="hidden", timeout=timeout_ms)
    except Exception:
        pass
    await asyncio.sleep(2.0)


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

        # Wait for the risk summary metrics widget to appear
        await page.wait_for_selector("[data-testid='stMetric']", timeout=30_000)
        await asyncio.sleep(1.5)

        # Scroll gently to reveal the full risk summary metrics grid
        await slow_scroll(page, 400, steps=10, pause=0.16)
        await asyncio.sleep(3)  # hold on metrics so viewer can read them

        # ── STEP 2: All 5 charts — one by one ────────────────────────────
        print("Step 2: scrolling to each chart individually...")
        chart_locator = page.locator('[data-testid="stPlotlyChart"]')
        num_charts = await chart_locator.count()
        print(f"  Found {num_charts} Plotly chart(s)")

        if num_charts >= 1:
            for i in range(min(num_charts, 5)):
                chart = chart_locator.nth(i)
                print(f"  Chart {i+1}/{min(num_charts,5)}...")
                await chart.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                # Nudge scroll so chart sits comfortably in viewport
                await page.mouse.wheel(0, -60)
                await asyncio.sleep(0.3)
                await page.mouse.wheel(0, 40)
                await asyncio.sleep(2.5)  # pause so viewer can read the chart
        else:
            # Fallback: continuous slow scroll if selectors not found
            await slow_scroll(page, 2400, steps=30, pause=0.20)
            await asyncio.sleep(2)

        # Scroll back to the top before the agent section
        await slow_scroll(page, -3000, steps=30, pause=0.08)
        await asyncio.sleep(1)

        # Selector for the question text input
        agent_input = 'input[placeholder*="volatility"]'

        async def run_question(label: str, question: str, extra_scroll: int = 550, expand_rag: bool = False):
            """Type a question, run the agent, zoom in to show the answer clearly."""
            print(f"  Agent: {question!r}")

            # Scroll to and zoom into the agent panel input
            await zoom_to(page, 125)
            await asyncio.sleep(0.3)
            try:
                await page.locator("text=Ask the Risk Agent").scroll_into_view_if_needed()
                await asyncio.sleep(0.4)
            except Exception:
                pass
            await page.mouse.wheel(0, -80)
            await asyncio.sleep(0.4)

            # Type the question — at 125 % zoom it's clearly legible
            await clear_and_fill(page, agent_input, question)
            await asyncio.sleep(1.0)  # hold so viewer reads the question

            # Zoom back to 100 % before clicking Run (keeps spinner + answer full-width)
            await zoom_to(page, 100)
            await click_run(page)

            # Wait for response
            print(f"    Waiting for response...")
            await wait_for_agent_response(page, timeout_ms=120_000)

            # Zoom into the answer area so text is clearly readable
            await zoom_to(page, 130)
            await asyncio.sleep(0.5)

            # Scroll down slowly to reveal the full answer + metadata row
            await slow_scroll(page, extra_scroll, steps=12, pause=0.18)
            await asyncio.sleep(1.5)

            # If there's a RAG document expander, open it and scroll through
            if expand_rag:
                try:
                    expander = page.locator("text=Retrieved document excerpts")
                    if await expander.is_visible(timeout=3000):
                        await expander.click()
                        await asyncio.sleep(0.8)
                        await slow_scroll(page, 350, steps=8, pause=0.18)
                        await asyncio.sleep(1.5)
                except Exception:
                    pass

            await asyncio.sleep(3.5)  # hold so viewer reads the answer
            await zoom_to(page, 100)
            await asyncio.sleep(0.5)

        # ── STEP 3: Annualised volatility (tool call) ─────────────────────
        print("Step 3: volatility question (tool call)...")
        await run_question("volatility", "What is the annualised volatility?", extra_scroll=600)

        # ── STEP 4: VaR methodology (RAG citation) ────────────────────────
        print("Step 4: VaR methodology (RAG)...")
        await run_question("rag", "What is the methodology for VaR?", extra_scroll=700, expand_rag=True)

        # ── STEP 5: "Should I buy this stock?" — EU AI Act refusal ────────
        print("Step 5: EU AI Act refusal (Unacceptable)...")
        # Refusal is deterministic Python — no LLM call, completes instantly
        await zoom_to(page, 125)
        try:
            await page.locator("text=Ask the Risk Agent").scroll_into_view_if_needed()
        except Exception:
            pass
        await page.mouse.wheel(0, -80)
        await asyncio.sleep(0.4)
        await clear_and_fill(page, agent_input, "Should I buy this stock?")
        await asyncio.sleep(1.0)
        await zoom_to(page, 100)
        await click_run(page)
        await asyncio.sleep(2.5)
        await zoom_to(page, 130)
        await slow_scroll(page, 500, steps=10, pause=0.16)
        await asyncio.sleep(4.0)
        await zoom_to(page, 100)
        await asyncio.sleep(0.5)

        # ── STEP 6: "Is this suitable for my pension?" — human review ─────
        print("Step 6: human review warning (pension question)...")
        await run_question("pension", "Is this suitable for my pension?", extra_scroll=600)

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
    from PIL import Image

    out_dir.mkdir(parents=True, exist_ok=True)
    mp4_path = out_dir / "demo.mp4"
    gif_path = out_dir / "demo.gif"

    print(f"Reading video: {webm_path}")
    reader = imageio.get_reader(webm_path)
    meta = reader.get_meta_data()
    fps = meta.get("fps", 25)
    print(f"  Source FPS: {fps:.1f}")

    frames = []
    for frame in reader:
        frames.append(frame)
    reader.close()
    total = len(frames)
    print(f"  Total frames: {total}")

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
    print(f"  MP4 written: {mp4_path.stat().st_size / 1e6:.1f} MB")

    # ── GIF — keep width ≥ 960 px, adjust speed to stay under 10 MB ──────
    gif_w = 960
    gif_fps = 12

    def make_gif(speed: int, colors: int) -> float:
        """Write GIF at given speed factor and palette size; return file size in MB."""
        sampled = frames[::speed]
        print(f"  Trying speed={speed}, colors={colors}: {len(sampled)} frames @ {gif_fps} fps")
        pil_frames = []
        for f in sampled:
            img = Image.fromarray(f)
            h = int(img.height * gif_w / img.width)
            img = img.resize((gif_w, h), Image.LANCZOS)
            img = img.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
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
        print(f"  -> {size_mb:.1f} MB")
        return size_mb

    # Progressive attempts: increase speed (never reduce resolution)
    attempts = [
        (4, 128),
        (5, 128),
        (6, 128),
        (7, 112),
        (8, 96),
        (10, 96),
        (12, 80),
        (16, 72),
        (20, 64),
        (24, 56),
        (28, 48),
        (32, 48),
    ]
    size_mb = 99.0
    for speed, colors in attempts:
        size_mb = make_gif(speed, colors)
        if size_mb <= 9.8:
            break

    if size_mb > 9.8:
        print(f"  WARNING: GIF is {size_mb:.1f} MB — still above 10 MB target after all attempts.")
    else:
        print(f"  GIF size OK: {size_mb:.1f} MB at {gif_w} px wide")

    return mp4_path, gif_path


# -------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    key = os.environ.get("LLM_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.strip():
        print("ERROR: LLM_API_KEY is not set.")
        sys.exit(1)

    try:
        import urllib.request
        urllib.request.urlopen(f"{APP_URL}/_stcore/health", timeout=5)
    except Exception:
        print(f"ERROR: Streamlit is not running at {APP_URL}.")
        sys.exit(1)

    print("Recording demo — this will take several minutes...")
    webm_path = asyncio.run(run_demo())
    print(f"WebM saved: {webm_path}")

    mp4, gif = convert_to_mp4_and_gif(webm_path, OUT_DIR)
    print(f"\nDone.")
    print(f"  MP4: {mp4}")
    print(f"  GIF: {gif}")

    shutil.rmtree(TMP_VIDEO_DIR, ignore_errors=True)
