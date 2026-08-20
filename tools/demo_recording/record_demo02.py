"""
Re-record demo_02_volatility.gif

Story:
  1. Page loads, instantly jumps to the agent panel (no chart section shown)
  2. Cinematic zoom push-in: 150% -> 210% over ~1.5 s, centred on input box
  3. Type "What is the annualised volatility?" slowly, letter by letter
  4. Zoom pull-back to 160% so Run Agent button enters frame
  5. Mouse moves visibly to the button and clicks it
  6. Spinner plays — agent is thinking
  7. Answer appears — zoom push-in to 185% on answer text
  8. Slow scroll through each response section with pauses
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


async def animate_zoom(page, start_pct: float, end_pct: float, duration: float = 1.5, steps: int = 24):
    """Smoothly animate browser zoom from start_pct to end_pct."""
    for i in range(steps + 1):
        t   = i / steps
        # Ease in-out: smooth cubic
        t2  = t * t * (3 - 2 * t)
        pct = start_pct + (end_pct - start_pct) * t2
        await page.evaluate(f"document.body.style.zoom = '{pct:.2f}%'")
        await asyncio.sleep(duration / steps)


async def inject_fonts(page):
    await page.evaluate("""
        const style = document.createElement('style');
        style.textContent = `
            section[data-testid="stMain"], .main { font-size: 20px !important; }
            [data-testid="stMetricValue"]  { font-size: 2.4rem !important; font-weight: 700 !important; }
            [data-testid="stMetricLabel"]  { font-size: 1.1rem !important; }
            h1, h2, h3                     { font-size: 1.6rem !important; }
            section[data-testid="stSidebar"] { font-size: 17px !important; }
            p                              { font-size: 18px !important; }
            .stTextInput input             { font-size: 22px !important; padding: 12px !important; }
            /* Make the Run agent button large and obvious */
            [data-testid="stButton"] button { font-size: 18px !important; padding: 10px 28px !important; }
            /* Answer markdown */
            [data-testid="stMarkdownContainer"] p { font-size: 19px !important; }
            /* Info boxes (basis, tools, tier) */
            [data-testid="stAlert"] { font-size: 17px !important; }
        `;
        document.head.appendChild(style);
    """)
    await asyncio.sleep(0.4)


async def move_and_click(page, locator):
    """Get element bounding box, move mouse there visibly, then click."""
    box = await locator.bounding_box()
    if box:
        cx = box["x"] + box["width"]  / 2
        cy = box["y"] + box["height"] / 2
        # Move mouse from a distance so the cursor path is visible
        await page.mouse.move(cx - 200, cy - 80)
        await asyncio.sleep(0.3)
        await page.mouse.move(cx, cy, steps=20)   # slow glide to button
        await asyncio.sleep(0.4)
        await page.mouse.click(cx, cy)
    else:
        await locator.click()


# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

async def record() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="demo02_new_"))
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

        # Base zoom + fonts
        await page.evaluate("document.body.style.zoom = '150%'")
        await inject_fonts(page)
        await page.wait_for_selector("[data-testid='stMetric']", timeout=30_000)
        await asyncio.sleep(1)

        # ── Jump to agent panel (fast scroll — shows intent) ──────────────
        print("Scrolling to agent panel...")
        agent_heading = page.locator("text=Ask the Risk Agent")
        await agent_heading.scroll_into_view_if_needed()
        await asyncio.sleep(0.3)
        # Nudge up so heading is near top of frame, input box clearly visible
        await page.mouse.wheel(0, -40)
        await asyncio.sleep(1.5)   # brief pause so viewer orients

        agent_input = page.locator('input[placeholder*="volatility"]')

        # ── Cinematic push-in zoom towards the input box ──────────────────
        print("Cinematic zoom in...")
        await animate_zoom(page, 150, 210, duration=1.8, steps=30)
        await asyncio.sleep(0.8)   # hold at full zoom so box fills frame

        # ── Type question slowly ──────────────────────────────────────────
        print("Typing question...")
        await agent_input.click()
        await asyncio.sleep(0.4)
        await page.keyboard.type("What is the annualised volatility?", delay=90)
        await asyncio.sleep(0.8)   # hold — let viewer read the question

        # ── Zoom pull-back so Run Agent button is in frame ────────────────
        print("Zoom pull-back to show Run Agent button...")
        await animate_zoom(page, 210, 160, duration=1.2, steps=20)
        await asyncio.sleep(0.3)

        # Tab out to trigger Streamlit onChange and enable the button
        await page.keyboard.press("Tab")
        await asyncio.sleep(1.2)

        # ── Move mouse visibly to Run Agent and click ─────────────────────
        print("Clicking Run Agent...")
        run_btn = page.locator('button:has-text("Run agent")')
        # Wait for it to be enabled
        deadline = asyncio.get_event_loop().time() + 20
        while await run_btn.is_disabled():
            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError("Run agent still disabled")
            await asyncio.sleep(0.2)
        await move_and_click(page, run_btn)

        # ── Spinner — agent is thinking ───────────────────────────────────
        print("Waiting for agent response...")
        # Zoom back to neutral while waiting
        await animate_zoom(page, 160, 150, duration=0.8, steps=14)
        try:
            await page.wait_for_selector("[data-testid='stSpinner']", timeout=5_000)
            await asyncio.sleep(1)   # show spinner briefly
        except Exception:
            pass
        try:
            await page.wait_for_selector("[data-testid='stSpinner']",
                                         state="hidden", timeout=90_000)
        except Exception:
            pass
        await asyncio.sleep(2)   # let render settle

        # ── Zoom push-in on answer text ───────────────────────────────────
        print("Showing answer...")
        await animate_zoom(page, 150, 185, duration=1.2, steps=20)
        await asyncio.sleep(0.5)

        # Scroll down to reveal the answer text
        await slow_scroll(page, 180, steps=8, pause=0.18)
        await asyncio.sleep(3)   # pause on answer paragraph

        # Scroll to basis / tools row
        await slow_scroll(page, 200, steps=8, pause=0.18)
        await asyncio.sleep(3)   # pause on "Basis of answer / Tools called / Docs"

        # Scroll to EU AI Act tier / Human review row
        await slow_scroll(page, 200, steps=8, pause=0.18)
        await asyncio.sleep(3)   # pause on tier metadata

        # Final hold
        await asyncio.sleep(2)

        video_path = await page.video.path()
        await ctx.close()
        await browser.close()

    return video_path


# ---------------------------------------------------------------------------
# GIF encoding
# ---------------------------------------------------------------------------

def encode(webm_path: str) -> list[Path]:
    import imageio
    from PIL import Image

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUT_DIR / "demo_02_volatility.gif"

    print(f"Reading {Path(webm_path).name}...")
    reader     = imageio.get_reader(webm_path)
    source_fps = reader.get_meta_data().get("fps", 25)
    frames     = [f for f in reader]
    reader.close()
    print(f"  {len(frames)} frames @ {source_fps:.0f} fps")

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

    for colors in [256, 192, 128, 96, 64]:
        print(f"  colors={colors}...", end=" ", flush=True)
        pil  = make_pil(sampled, colors)
        size = save_gif(pil, base)
        if size <= 9.8:
            return [base]

    # Split
    print("  Splitting into part_a / part_b...")
    base.unlink(missing_ok=True)
    mid    = len(sampled) // 2
    part_a = OUT_DIR / "demo_02_volatility_part_a.gif"
    part_b = OUT_DIR / "demo_02_volatility_part_b.gif"
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
    print("Re-recording demo_02_volatility...")
    webm = asyncio.run(record())
    print(f"WebM: {webm}")

    print("\nEncoding GIF...")
    parts = encode(str(webm))

    print("\nDone:")
    for p in parts:
        mb = p.stat().st_size / (1024 * 1024)
        print(f"  {p.name}: {mb:.1f} MB")

    shutil.rmtree(Path(webm).parent, ignore_errors=True)
