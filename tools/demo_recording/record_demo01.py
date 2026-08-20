"""
Re-record and re-encode demo_01_dashboard.gif only.

Changes vs previous version:
- Larger fonts injected via CSS (metrics, labels, sidebar, chart titles)
- Slow natural scroll from very top of page downward
- Pause on risk summary metrics, then drift down to each chart one by one
- No agent panel — pure dashboard browsing experience
- Max quality: highest color palette that fits under 10 MB at 1280px
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "http://localhost:8501"
OUT_DIR = Path("docs/screenshots")
GIF_W   = 1280
GIF_FPS = 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def slow_scroll(page, distance: int, steps: int, pause: float):
    per = distance // max(steps, 1)
    for _ in range(steps):
        await page.mouse.wheel(0, per)
        await asyncio.sleep(pause)


async def inject_fonts(page):
    """Make all text on the page noticeably larger and cleaner."""
    await page.evaluate("""
        const style = document.createElement('style');
        style.textContent = `
            /* Main content area */
            section[data-testid="stMain"], .main { font-size: 20px !important; }

            /* Metric values (the big numbers) */
            [data-testid="stMetricValue"] { font-size: 2.4rem !important; font-weight: 700 !important; }

            /* Metric labels */
            [data-testid="stMetricLabel"] { font-size: 1.1rem !important; }

            /* Metric delta */
            [data-testid="stMetricDelta"] { font-size: 1.0rem !important; }

            /* Section headers / subheaders */
            h1, h2, h3 { font-size: 1.6rem !important; }

            /* Sidebar text */
            section[data-testid="stSidebar"] { font-size: 17px !important; }

            /* Captions / source note */
            [data-testid="stCaptionContainer"] { font-size: 14px !important; }

            /* General paragraph text */
            p { font-size: 18px !important; }
        `;
        document.head.appendChild(style);
    """)
    await asyncio.sleep(0.5)


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

async def record() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="demo01_new_"))
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-extensions"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(tmp),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()

        # ── Load app ──────────────────────────────────────────────────────
        print("Loading app...")
        await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(3)

        # Apply 150% zoom so UI is large and readable
        await page.evaluate("document.body.style.zoom = '150%'")
        await asyncio.sleep(0.5)

        # Inject larger fonts on top of the zoom
        await inject_fonts(page)

        # Wait for risk summary metrics to render
        await page.wait_for_selector("[data-testid='stMetric']", timeout=30_000)
        await asyncio.sleep(2)   # hold at the very top so viewer sees the title

        # ── Scroll slowly to risk summary ─────────────────────────────────
        print("Scrolling to risk summary...")
        await slow_scroll(page, 350, steps=14, pause=0.22)  # gentle drift down
        await asyncio.sleep(4)   # hold on metrics panel — all numbers visible

        # ── Scroll to each chart one by one ───────────────────────────────
        charts = page.locator('[data-testid="stPlotlyChart"]')
        n = await charts.count()
        names = ["Price series", "Daily returns", "Rolling volatility", "Drawdown", "VaR chart"]
        print(f"Found {n} charts")

        for i in range(min(n, 5)):
            print(f"  Chart {i+1}/5: {names[i]}")
            # Scroll smoothly to chart
            await charts.nth(i).scroll_into_view_if_needed()
            await asyncio.sleep(0.4)
            # Nudge up slightly so chart isn't cut off at top edge
            await page.mouse.wheel(0, -80)
            await asyncio.sleep(0.3)
            # Small final nudge to settle
            await page.mouse.wheel(0, 30)
            await asyncio.sleep(4)   # hold on each chart for viewer to read it

        # Brief final pause at the bottom
        await asyncio.sleep(2)

        video_path = await page.video.path()
        await ctx.close()
        await browser.close()

    return video_path


# ---------------------------------------------------------------------------
# GIF encoding — max quality, split if needed
# ---------------------------------------------------------------------------

def encode(webm_path: str) -> list[Path]:
    import imageio
    from PIL import Image

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUT_DIR / "demo_01_dashboard.gif"

    print(f"Reading {Path(webm_path).name}...")
    reader     = imageio.get_reader(webm_path)
    source_fps = reader.get_meta_data().get("fps", 25)
    frames     = [f for f in reader]
    reader.close()
    print(f"  {len(frames)} frames @ {source_fps:.0f} fps")

    # Sample to GIF_FPS (natural speed)
    step    = max(1, round(source_fps / GIF_FPS))
    sampled = frames[::step]
    print(f"  {len(sampled)} sampled frames (step={step})")

    def make_pil(flist, colors):
        out = []
        for f in flist:
            img = Image.fromarray(f)
            h   = int(img.height * GIF_W / img.width)
            img = img.resize((GIF_W, h), Image.LANCZOS)
            img = img.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
            out.append(img)
        return out

    def save_gif(pil_frames, path):
        dur = int(1000 / GIF_FPS)
        pil_frames[0].save(
            str(path), save_all=True, append_images=pil_frames[1:],
            optimize=True, duration=dur, loop=0,
        )
        mb = path.stat().st_size / (1024 * 1024)
        print(f"  {path.name}: {mb:.1f} MB")
        return mb

    # Try decreasing palette sizes — stop at first that fits
    for colors in [256, 192, 128, 96, 64]:
        print(f"  Trying colors={colors}...", end=" ", flush=True)
        pil  = make_pil(sampled, colors)
        size = save_gif(pil, base)
        if size <= 9.8:
            return [base]

    # Still too large — split into part_a / part_b at best quality
    print("  Splitting into part_a / part_b...")
    base.unlink(missing_ok=True)
    mid    = len(sampled) // 2
    part_a = OUT_DIR / "demo_01_dashboard_part_a.gif"
    part_b = OUT_DIR / "demo_01_dashboard_part_b.gif"
    result = []
    for path, chunk in [(part_a, sampled[:mid]), (part_b, sampled[mid:])]:
        for colors in [256, 192, 128, 96, 64]:
            pil  = make_pil(chunk, colors)
            size = save_gif(pil, path)
            if size <= 9.8:
                result.append(path)
                break
        else:
            result.append(path)
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Re-recording demo_01_dashboard...")
    webm = asyncio.run(record())
    print(f"WebM: {webm}")

    print("\nEncoding GIF...")
    parts = encode(str(webm))

    print("\nDone:")
    for p in parts:
        mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name}: {mb:.1f} MB")

    shutil.rmtree(Path(webm).parent, ignore_errors=True)
