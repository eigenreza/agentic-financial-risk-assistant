"""
Playwright-based demo recorder for the Agentic Financial Risk Assistant.

Produces 6 separate GIFs, one per scenario, each at 960px and under 10 MB:

  demo_01_dashboard.gif   - app loading, risk summary, all 5 charts
  demo_02_volatility.gif  - annualised volatility (tool call)
  demo_03_rag.gif         - VaR methodology (RAG citation)
  demo_04_refusal.gif     - "Should I buy this stock?" (EU AI Act refusal)
  demo_05_humanreview.gif - "Is this suitable for my pension?" (human review)
  demo_06_datasource.gif  - "Where did the data come from?" (data_readme RAG)

Also writes demo.mp4 (full combined recording for reference).

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

APP_URL  = "http://localhost:8501"
OUT_DIR  = Path("docs/screenshots")
VIEWPORT = {"width": 1280, "height": 900}
GIF_W    = 960
GIF_FPS  = 12


# ---------------------------------------------------------------------------
# Low-level page helpers
# ---------------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int = 10, pause: float = 0.16):
    per = distance // max(steps, 1)
    for _ in range(steps):
        await page.mouse.wheel(0, per)
        await asyncio.sleep(pause)


async def zoom_to(page, pct: int):
    await page.evaluate(f"document.body.style.zoom = '{pct}%'")
    await asyncio.sleep(0.3)


async def wait_ready(page):
    """Wait for the risk summary metric widget to appear."""
    await page.wait_for_selector("[data-testid='stMetric']", timeout=40_000)
    await asyncio.sleep(1.5)


async def clear_and_fill(page, selector: str, text: str):
    loc = page.locator(selector)
    await loc.scroll_into_view_if_needed()
    await asyncio.sleep(0.3)
    await loc.click(click_count=3)
    await asyncio.sleep(0.2)
    await loc.fill(text)
    await asyncio.sleep(0.4)
    await page.keyboard.press("Tab")
    await asyncio.sleep(0.7)


async def click_run(page, timeout_s: int = 20):
    loc = page.locator('button:has-text("Run agent")')
    deadline = asyncio.get_event_loop().time() + timeout_s
    while True:
        if not await loc.is_disabled():
            break
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError("Run agent button still disabled")
        await asyncio.sleep(0.25)
    await loc.click()


async def wait_response(page, timeout_ms: int = 120_000):
    try:
        await page.wait_for_selector("[data-testid='stSpinner']", state="hidden",
                                     timeout=timeout_ms)
    except Exception:
        pass
    await asyncio.sleep(2.0)


async def scroll_to_agent(page):
    try:
        await page.locator("text=Ask the Risk Agent").scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await page.mouse.wheel(0, -60)
        await asyncio.sleep(0.3)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Context factory
# ---------------------------------------------------------------------------

async def new_recording_context(pw, tmp_dir: Path):
    browser = await pw.chromium.launch(headless=True, slow_mo=0)
    context = await browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(tmp_dir),
        record_video_size=VIEWPORT,
    )
    page = await context.new_page()
    return browser, context, page


# ---------------------------------------------------------------------------
# Scenario 1 – Dashboard (loading + risk summary + all 5 charts)
# ---------------------------------------------------------------------------

async def record_dashboard(pw) -> Path:
    print("=== Scenario 1: dashboard ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo01_"))
    browser, context, page = await new_recording_context(pw, tmp)

    print("  Loading app...")
    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    # Show risk summary at normal zoom
    await slow_scroll(page, 420, steps=10, pause=0.18)
    await asyncio.sleep(3)           # hold so viewer reads the metrics

    # Scroll to each chart individually
    charts = page.locator('[data-testid="stPlotlyChart"]')
    n = await charts.count()
    print(f"  Found {n} charts")
    chart_names = ["Price series", "Daily returns", "Rolling volatility", "Drawdown", "VaR"]
    for i in range(min(n, 5)):
        print(f"  Chart {i+1}/5: {chart_names[i]}")
        await charts.nth(i).scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await page.mouse.wheel(0, -80)   # nudge so chart isn't clipped at top
        await asyncio.sleep(0.3)
        await page.mouse.wheel(0, 50)
        await asyncio.sleep(2.8)         # pause for viewer to read the chart

    await asyncio.sleep(1)
    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario 2 – Annualised volatility (tool call)
# ---------------------------------------------------------------------------

async def record_volatility(pw) -> Path:
    print("=== Scenario 2: volatility (tool call) ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo02_"))
    browser, context, page = await new_recording_context(pw, tmp)

    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    await scroll_to_agent(page)
    agent_input = 'input[placeholder*="volatility"]'

    # Zoom in so typing is clearly legible
    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await clear_and_fill(page, agent_input, "What is the annualised volatility?")
    await asyncio.sleep(1.5)   # hold so viewer reads the question

    await zoom_to(page, 100)
    await click_run(page)
    print("  Waiting for tool-call response...")
    await wait_response(page, timeout_ms=120_000)

    # Zoom in on the answer
    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await slow_scroll(page, 650, steps=14, pause=0.20)
    await asyncio.sleep(4)     # hold so viewer reads basis/tools/tier row

    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario 3 – VaR methodology (RAG citation)
# ---------------------------------------------------------------------------

async def record_rag(pw) -> Path:
    print("=== Scenario 3: VaR methodology (RAG) ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo03_"))
    browser, context, page = await new_recording_context(pw, tmp)

    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    await scroll_to_agent(page)
    agent_input = 'input[placeholder*="volatility"]'

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await clear_and_fill(page, agent_input, "What is the methodology for VaR?")
    await asyncio.sleep(1.5)

    await zoom_to(page, 100)
    await click_run(page)
    print("  Waiting for RAG+LLM response...")
    await wait_response(page, timeout_ms=120_000)

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await slow_scroll(page, 700, steps=14, pause=0.20)
    await asyncio.sleep(2)

    # Open and scroll through the retrieved document excerpts
    try:
        expander = page.locator("text=Retrieved document excerpts")
        if await expander.is_visible(timeout=4000):
            await expander.click()
            await asyncio.sleep(0.8)
            await slow_scroll(page, 400, steps=10, pause=0.18)
            await asyncio.sleep(3)
    except Exception:
        pass

    await asyncio.sleep(1)
    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario 4 – "Should I buy this stock?" (EU AI Act refusal)
# ---------------------------------------------------------------------------

async def record_refusal(pw) -> Path:
    print("=== Scenario 4: EU AI Act refusal ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo04_"))
    browser, context, page = await new_recording_context(pw, tmp)

    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    await scroll_to_agent(page)
    agent_input = 'input[placeholder*="volatility"]'

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await clear_and_fill(page, agent_input, "Should I buy this stock?")
    await asyncio.sleep(1.5)

    await zoom_to(page, 100)
    await click_run(page)
    # Refusal is instant (pure Python, no LLM call)
    await asyncio.sleep(2.5)

    await zoom_to(page, 130)
    await slow_scroll(page, 550, steps=12, pause=0.18)
    await asyncio.sleep(4.5)   # hold on EU AI Act tier label

    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario 5 – "Is this suitable for my pension?" (human review warning)
# ---------------------------------------------------------------------------

async def record_humanreview(pw) -> Path:
    print("=== Scenario 5: human review warning ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo05_"))
    browser, context, page = await new_recording_context(pw, tmp)

    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    await scroll_to_agent(page)
    agent_input = 'input[placeholder*="volatility"]'

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await clear_and_fill(page, agent_input, "Is this suitable for my pension?")
    await asyncio.sleep(1.5)

    await zoom_to(page, 100)
    await click_run(page)
    print("  Waiting for human-review response...")
    await wait_response(page, timeout_ms=120_000)

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await slow_scroll(page, 650, steps=14, pause=0.20)
    await asyncio.sleep(4.5)   # hold on "Human review required: Yes" warning

    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario 6 – "Where did the data come from?" (data_readme RAG)
# ---------------------------------------------------------------------------

async def record_datasource(pw) -> Path:
    print("=== Scenario 6: data source (RAG data_readme) ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo06_"))
    browser, context, page = await new_recording_context(pw, tmp)

    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await wait_ready(page)

    await scroll_to_agent(page)
    agent_input = 'input[placeholder*="volatility"]'

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await clear_and_fill(page, agent_input, "Where did the data come from?")
    await asyncio.sleep(1.5)

    await zoom_to(page, 100)
    await click_run(page)
    print("  Waiting for RAG data_readme response...")
    await wait_response(page, timeout_ms=120_000)

    await zoom_to(page, 130)
    await asyncio.sleep(0.5)
    await slow_scroll(page, 700, steps=14, pause=0.20)
    await asyncio.sleep(2)

    # Open retrieved document excerpts to show data_readme source
    try:
        expander = page.locator("text=Retrieved document excerpts")
        if await expander.is_visible(timeout=4000):
            await expander.click()
            await asyncio.sleep(0.8)
            await slow_scroll(page, 400, steps=10, pause=0.18)
            await asyncio.sleep(3)
    except Exception:
        pass

    await asyncio.sleep(1)
    video_path = await page.video.path()
    await context.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# GIF encoder – natural speed, 960 px, under 10 MB
# ---------------------------------------------------------------------------

def webm_to_gif(webm_path: str, gif_path: Path) -> float:
    """
    Convert a WebM recording to an optimised GIF.

    Starts at speed=2 (near-natural) and steps up until file < 10 MB.
    Resolution is always GIF_W px wide.  Returns final size in MB.
    """
    import imageio
    from PIL import Image

    print(f"  Reading {webm_path}")
    reader = imageio.get_reader(webm_path)
    fps    = reader.get_meta_data().get("fps", 25)
    frames = [f for f in reader]
    reader.close()
    print(f"  {len(frames)} frames @ {fps:.0f} fps")

    attempts = [
        (2, 128), (3, 128), (4, 128), (5, 112),
        (6, 96),  (7, 96),  (8, 80),  (10, 72),
        (12, 64), (16, 56), (20, 48),
    ]

    size_mb = 99.0
    for speed, colors in attempts:
        sampled = frames[::speed]
        print(f"  speed={speed} colors={colors}: {len(sampled)} frames", end="", flush=True)
        pil_frames = []
        for f in sampled:
            img = Image.fromarray(f)
            h   = int(img.height * GIF_W / img.width)
            img = img.resize((GIF_W, h), Image.LANCZOS)
            img = img.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
            pil_frames.append(img)
        dur = int(1000 / GIF_FPS)
        pil_frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=pil_frames[1:],
            optimize=True,
            duration=dur,
            loop=0,
        )
        size_mb = gif_path.stat().st_size / (1024 * 1024)
        print(f" -> {size_mb:.1f} MB")
        if size_mb <= 9.8:
            break

    if size_mb > 9.8:
        print(f"  WARNING: {gif_path.name} is {size_mb:.1f} MB (above 10 MB target)")
    return size_mb


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_all():
    async with async_playwright() as pw:
        results: dict[str, Path] = {}

        results["01_dashboard"]   = await record_dashboard(pw)
        results["02_volatility"]  = await record_volatility(pw)
        results["03_rag"]         = await record_rag(pw)
        results["04_refusal"]     = await record_refusal(pw)
        results["05_humanreview"] = await record_humanreview(pw)
        results["06_datasource"]  = await record_datasource(pw)

    return results


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

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Recording 6 scenarios — this will take several minutes...")
    webm_paths = asyncio.run(run_all())

    print("\nConverting to GIFs...")
    for key, webm in webm_paths.items():
        out_gif = OUT_DIR / f"demo_{key}.gif"
        print(f"\n--- {out_gif.name} ---")
        size = webm_to_gif(str(webm), out_gif)
        # Clean up temp dir
        try:
            shutil.rmtree(Path(webm).parent, ignore_errors=True)
        except Exception:
            pass

    print("\nAll done.")
    for key in webm_paths:
        p = OUT_DIR / f"demo_{key}.gif"
        mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name}: {mb:.1f} MB")
