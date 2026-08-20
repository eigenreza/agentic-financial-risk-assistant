"""
Playwright demo recorder — Agentic Financial Risk Assistant.

Produces 6 GIFs (split into _part_a / _part_b if > 10 MB):
  demo_01_dashboard.gif      app loading, risk summary, all 5 charts
  demo_02_volatility.gif     annualised volatility — tool call
  demo_03_rag.gif            VaR methodology — RAG citation
  demo_04_refusal.gif        "Should I buy this stock?" — EU AI Act refusal
  demo_05_humanreview.gif    "Is this suitable for my pension?" — human review
  demo_06_datasource.gif     "Where did the data come from?" — data_readme RAG

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

VIEWPORT     = {"width": 1920, "height": 1080}
GIF_W        = 1280
GIF_FPS      = 12
MAX_GIF_MB   = 9.8


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int = 12, pause: float = 0.18):
    per = distance // max(steps, 1)
    for _ in range(steps):
        await page.mouse.wheel(0, per)
        await asyncio.sleep(pause)


async def instant_scroll_to(page, selector: str):
    """Scroll element into view instantly (no animation) using JS."""
    try:
        await page.evaluate(
            f"document.querySelector('{selector}').scrollIntoView({{behavior:'instant',block:'start'}})"
        )
    except Exception:
        try:
            await page.locator(selector).scroll_into_view_if_needed()
        except Exception:
            pass
    await asyncio.sleep(0.4)


async def apply_base_zoom(page):
    """Apply 150 % browser zoom and inject larger font sizes."""
    await page.evaluate("document.body.style.zoom = '150%'")
    # Increase main content font size for readability
    await page.evaluate("""
        const main = document.querySelector('[data-testid="stMain"]')
                  || document.querySelector('section.main')
                  || document.querySelector('.main');
        if (main) main.style.fontSize = '18px';
    """)
    await asyncio.sleep(0.3)


async def zoom_input(page):
    """Make the text input font larger so typed text is clearly visible."""
    await page.evaluate("""
        const inp = document.querySelector('.stTextInput input');
        if (inp) { inp.style.fontSize = '24px'; inp.style.padding = '10px'; }
    """)
    await asyncio.sleep(0.2)


async def zoom_answer(page, pct: int = 175):
    """Scale the answer / response area to make text more readable."""
    await page.evaluate(f"""
        const ans = document.querySelector('[data-testid="stMarkdownContainer"]');
        if (ans) ans.style.fontSize = '{pct - 100 + 18}px';
        document.body.style.zoom = '{pct}%';
    """)
    await asyncio.sleep(0.3)


async def reset_zoom(page, pct: int = 150):
    await page.evaluate(f"document.body.style.zoom = '{pct}%'")
    await asyncio.sleep(0.2)


async def wait_ready(page):
    """Wait for the risk summary metrics to appear."""
    await page.wait_for_selector("[data-testid='stMetric']", timeout=45_000)
    await asyncio.sleep(1.5)


async def type_question(page, selector: str, text: str):
    """Click the input, type slowly (100 ms / char), then Tab-out to flush Streamlit."""
    loc = page.locator(selector)
    await loc.scroll_into_view_if_needed()
    await asyncio.sleep(0.3)
    await loc.click(click_count=3)
    await asyncio.sleep(0.3)
    await page.keyboard.type(text, delay=100)
    await asyncio.sleep(0.4)
    # Tab-out so Streamlit's debounced onChange fires and enables the Run button
    await page.keyboard.press("Tab")
    await asyncio.sleep(0.8)


async def click_run(page, timeout_s: int = 35):
    loc = page.locator('button:has-text("Run agent")')
    deadline = asyncio.get_event_loop().time() + timeout_s
    while True:
        if not await loc.is_disabled():
            break
        if asyncio.get_event_loop().time() > deadline:
            raise TimeoutError("Run agent button still disabled")
        await asyncio.sleep(0.3)
    await loc.click()


async def wait_response(page, timeout_ms: int = 90_000):
    try:
        await page.wait_for_selector("[data-testid='stSpinner']", state="hidden",
                                     timeout=timeout_ms)
    except Exception:
        pass
    await asyncio.sleep(2.0)


async def pause(secs: float):
    await asyncio.sleep(secs)


# ---------------------------------------------------------------------------
# Recording context factory
# ---------------------------------------------------------------------------

async def new_context(pw, tmp_dir: Path):
    browser = await pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-extensions"],
    )
    ctx = await browser.new_context(
        viewport=VIEWPORT,
        record_video_dir=str(tmp_dir),
        record_video_size=VIEWPORT,
    )
    page = await ctx.new_page()
    return browser, ctx, page


async def load_app(page):
    """Load the app, apply zoom + font injection, wait for metrics."""
    print("  Loading app...")
    await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
    await asyncio.sleep(4)
    await apply_base_zoom(page)
    await wait_ready(page)
    await asyncio.sleep(0.5)


# ---------------------------------------------------------------------------
# Scenario 1 — Dashboard
# ---------------------------------------------------------------------------

async def record_dashboard(pw) -> Path:
    print("=== Scenario 1: dashboard ===")
    tmp = Path(tempfile.mkdtemp(prefix="demo01_"))
    browser, ctx, page = await new_context(pw, tmp)

    await load_app(page)

    # Scroll gently to show the full risk summary metrics
    await slow_scroll(page, 300, steps=8, pause=0.20)
    await pause(4)   # hold on metrics — reader can see all values

    # Scroll one chart at a time
    chart_loc = page.locator('[data-testid="stPlotlyChart"]')
    n = await chart_loc.count()
    chart_names = ["Price series", "Daily returns", "Rolling volatility", "Drawdown", "VaR chart"]
    for i in range(min(n, 5)):
        print(f"  Chart {i+1}/5: {chart_names[i]}")
        await chart_loc.nth(i).scroll_into_view_if_needed()
        await pause(0.4)
        await page.mouse.wheel(0, -60)  # small nudge so chart is not clipped
        await pause(0.3)
        await page.mouse.wheel(0, 30)
        await pause(4)                  # hold so viewer reads the chart

    # Scroll back up for a brief dashboard overview
    await slow_scroll(page, -600, steps=10, pause=0.12)
    await pause(2)

    video_path = await page.video.path()
    await ctx.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Shared agent-interaction helper
# ---------------------------------------------------------------------------

async def run_agent_scenario(
    pw, scenario_label: str, question: str, expand_rag: bool = False
) -> Path:
    print(f"=== {scenario_label} ===")
    tmp = Path(tempfile.mkdtemp(prefix=f"demo_{scenario_label[:4]}_"))
    browser, ctx, page = await new_context(pw, tmp)

    await load_app(page)

    # Jump straight to the agent panel (instant, no slow scroll)
    await instant_scroll_to(page, "[data-testid='stVerticalBlock']")
    # Scroll down until we see the agent heading
    for _ in range(6):
        visible = await page.locator("text=Ask the Risk Agent").is_visible()
        if visible:
            break
        await page.mouse.wheel(0, 300)
        await asyncio.sleep(0.3)
    await page.locator("text=Ask the Risk Agent").scroll_into_view_if_needed()
    await page.mouse.wheel(0, -40)
    await asyncio.sleep(0.8)

    agent_input = 'input[placeholder*="volatility"]'

    # Zoom input area so typed text is clearly visible
    await zoom_input(page)
    await asyncio.sleep(0.3)

    # Type question slowly
    await type_question(page, agent_input, question)
    await pause(2)   # hold so viewer reads the full question

    # Return to 150% zoom before clicking Run
    await reset_zoom(page, 150)
    await asyncio.sleep(0.3)
    await click_run(page)

    is_refusal = question.strip().lower().startswith("should i buy")
    if is_refusal:
        await pause(2.5)  # refusal is instant
    else:
        print(f"  Waiting for LLM response...")
        await wait_response(page, timeout_ms=90_000)

    # Zoom in on the answer section
    await zoom_answer(page, 175)
    await asyncio.sleep(0.5)

    # Scroll slowly through the full response, pausing at each section
    # Answer text
    await slow_scroll(page, 200, steps=6, pause=0.20)
    await pause(3)

    # Basis / Tools / Documents row
    await slow_scroll(page, 200, steps=6, pause=0.20)
    await pause(3)

    # EU AI Act tier / Human review row
    await slow_scroll(page, 200, steps=6, pause=0.20)
    await pause(3)

    # RAG document excerpts expander
    if expand_rag:
        try:
            exp = page.locator("text=Retrieved document excerpts")
            if await exp.is_visible(timeout=3000):
                await exp.click()
                await asyncio.sleep(0.8)
                await slow_scroll(page, 350, steps=8, pause=0.20)
                await pause(3)
        except Exception:
            pass

    await pause(3)   # final hold before GIF loops

    video_path = await page.video.path()
    await ctx.close()
    await browser.close()
    return video_path


# ---------------------------------------------------------------------------
# Scenario dispatcher
# ---------------------------------------------------------------------------

async def run_all(pw) -> dict[str, Path]:
    results = {}
    results["01_dashboard"]   = await record_dashboard(pw)
    results["02_volatility"]  = await run_agent_scenario(
        pw, "Scenario 2: volatility (tool call)",
        "What is the annualised volatility?")
    results["03_rag"]         = await run_agent_scenario(
        pw, "Scenario 3: VaR methodology (RAG)",
        "What is the methodology for VaR?", expand_rag=True)
    results["04_refusal"]     = await run_agent_scenario(
        pw, "Scenario 4: EU AI Act refusal",
        "Should I buy this stock?")
    results["05_humanreview"] = await run_agent_scenario(
        pw, "Scenario 5: human review warning",
        "Is this suitable for my pension?")
    results["06_datasource"]  = await run_agent_scenario(
        pw, "Scenario 6: data source RAG",
        "Where did the data come from?", expand_rag=True)
    return results


# ---------------------------------------------------------------------------
# GIF encoder with palette reduction + split support
# ---------------------------------------------------------------------------

def _build_pil_frames(raw_frames, gif_w: int, colors: int):
    from PIL import Image
    out = []
    for f in raw_frames:
        img = Image.fromarray(f)
        h   = int(img.height * gif_w / img.width)
        img = img.resize((gif_w, h), Image.LANCZOS)
        img = img.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
        out.append(img)
    return out


def _write_pil_gif(pil_frames, path: Path, gif_fps: int):
    dur = int(1000 / gif_fps)
    pil_frames[0].save(
        str(path),
        save_all=True,
        append_images=pil_frames[1:],
        optimize=True,
        duration=dur,
        loop=0,
    )
    return path.stat().st_size / (1024 * 1024)


def encode_gif(raw_frames, out_name: str, gif_w: int, gif_fps: int,
               max_mb: float = MAX_GIF_MB) -> list[Path]:
    """
    Encode raw frames to GIF(s).

    Strategy (in order, speed_factor never exceeds 1.5):
      1. Sample to gif_fps from source fps (natural speed at gif_fps display rate)
      2. Try palette sizes 128 -> 96 -> 64 -> 48 colors
      3. If still > max_mb: split into _part_a and _part_b at 128 colors

    Returns list of Path objects that were written.
    """
    import imageio

    gif_base = OUT_DIR / out_name
    print(f"  {len(raw_frames)} source frames")

    # Sample to GIF_FPS (natural speed — no temporal skipping beyond fps downconversion)
    # Source is 25 fps; sample every 2 frames to get ~12.5 fps, displayed at gif_fps
    source_fps = 25
    sample_step = max(1, round(source_fps / gif_fps))
    frames = raw_frames[::sample_step]
    print(f"  Sampled {len(frames)} frames (step={sample_step}, display {gif_fps} fps)")

    for colors in [128, 96, 64, 48]:
        print(f"  Trying colors={colors}...", end=" ", flush=True)
        pil = _build_pil_frames(frames, gif_w, colors)
        size = _write_pil_gif(pil, gif_base, gif_fps)
        print(f"{size:.1f} MB")
        if size <= max_mb:
            print(f"  -> {gif_base.name}: {size:.1f} MB")
            return [gif_base]

    # Full GIF too large — split into part_a / part_b
    print(f"  Full GIF exceeds {max_mb} MB — splitting into part_a / part_b")
    gif_base.unlink(missing_ok=True)

    part_a = OUT_DIR / out_name.replace(".gif", "_part_a.gif")
    part_b = OUT_DIR / out_name.replace(".gif", "_part_b.gif")
    mid    = len(frames) // 2

    results = []
    for part_path, part_frames in [(part_a, frames[:mid]), (part_b, frames[mid:])]:
        for colors in [128, 96, 64, 48]:
            pil  = _build_pil_frames(part_frames, gif_w, colors)
            size = _write_pil_gif(pil, part_path, gif_fps)
            if size <= max_mb:
                print(f"  -> {part_path.name}: {size:.1f} MB ({colors} colors)")
                results.append(part_path)
                break
        else:
            # Still too large — keep the last attempt (48 colors) and warn
            print(f"  WARNING: {part_path.name} is {size:.1f} MB — keeping best effort")
            results.append(part_path)

    return results


def webm_to_gif_parts(webm_path: str, out_name: str) -> list[Path]:
    import imageio
    print(f"  Reading {Path(webm_path).name}")
    reader     = imageio.get_reader(webm_path)
    raw_frames = [f for f in reader]
    reader.close()
    return encode_gif(raw_frames, out_name, GIF_W, GIF_FPS)


# ---------------------------------------------------------------------------
# README update
# ---------------------------------------------------------------------------

README_PATH = Path("README.md")

DEMO_DESCRIPTIONS = {
    "01_dashboard": (
        "Risk dashboard",
        "App loading with Equinor sample data, full risk summary metrics, "
        "and all 5 charts (price series, daily returns, rolling volatility, drawdown, VaR)."
    ),
    "02_volatility": (
        "Tool call — annualised volatility",
        "Agent answers *What is the annualised volatility?* by calling the Python "
        "`calculate_volatility` tool and returning a structured result with assumptions."
    ),
    "03_rag": (
        "RAG citation — VaR methodology",
        "Agent answers *What is the methodology for VaR?* by retrieving passages from "
        "the risk-methodology documentation using FAISS, with document source shown."
    ),
    "04_refusal": (
        "EU AI Act refusal — investment advice blocked",
        "Agent refuses *Should I buy this stock?* at the Python safety layer before the "
        "LLM is ever called, labelled EU AI Act Unacceptable risk tier."
    ),
    "05_humanreview": (
        "Human review warning — consequential question",
        "Agent answers *Is this suitable for my pension?* and prepends a human-review "
        "warning because the question is consequential for financial planning."
    ),
    "06_datasource": (
        "RAG citation — data source provenance",
        "Agent answers *Where did the data come from?* by retrieving the data-source "
        "documentation with the `data_readme` document source cited."
    ),
}


def build_readme_demo_block(gif_manifest: dict[str, list[Path]]) -> str:
    """Build the markdown block to embed all GIFs with labels."""
    lines = ["## Demo\n"]
    for key in ["01_dashboard", "02_volatility", "03_rag",
                "04_refusal", "05_humanreview", "06_datasource"]:
        title, desc = DEMO_DESCRIPTIONS[key]
        lines.append(f"### {title}\n")
        lines.append(f"{desc}\n")
        for path in gif_manifest.get(key, []):
            rel = str(path).replace("\\", "/")
            label = path.stem.replace("_", " ").title()
            lines.append(f"![{label}]({rel})\n")
        lines.append("")
    return "\n".join(lines)


def update_readme(gif_manifest: dict[str, list[Path]]):
    text = README_PATH.read_text(encoding="utf-8")
    demo_block = build_readme_demo_block(gif_manifest)

    # Replace everything between "## Demo" (or insert before "## Overview") with the new block
    import re
    # Remove old Demo section if present
    text = re.sub(r"## Demo\n.*?(?=\n## |\Z)", "", text, flags=re.DOTALL)
    # Remove old Screenshots section
    text = re.sub(r"## Screenshots\n.*?(?=\n## |\Z)", "", text, flags=re.DOTALL)
    # Insert after the badges / first --- separator
    insert_marker = "\n---\n\n## Overview"
    if insert_marker in text:
        text = text.replace(insert_marker, f"\n---\n\n{demo_block}\n---\n\n## Overview")
    else:
        # fallback: insert after first ---
        text = text.replace("\n---\n", f"\n---\n\n{demo_block}\n---\n", 1)

    README_PATH.write_text(text, encoding="utf-8")
    print("README updated.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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

    print("Recording 6 scenarios...")
    async def _run():
        async with async_playwright() as pw:
            return await run_all(pw)
    webm_map = asyncio.run(_run())

    print("\nConverting to GIFs...")
    gif_manifest: dict[str, list[Path]] = {}
    for key, webm_path in webm_map.items():
        out_name = f"demo_{key}.gif"
        print(f"\n--- {out_name} ---")
        parts = webm_to_gif_parts(str(webm_path), out_name)
        gif_manifest[key] = parts
        try:
            shutil.rmtree(Path(webm_path).parent, ignore_errors=True)
        except Exception:
            pass

    print("\nAll done:")
    for key, parts in gif_manifest.items():
        for p in parts:
            mb = p.stat().st_size / (1024 * 1024)
            print(f"  {p.name}: {mb:.1f} MB")

    print("\nUpdating README...")
    update_readme(gif_manifest)
