"""
Record demo_03 through demo_06 as MP4s.

Demo 03 - RAG citation: VaR methodology
Demo 04 - EU AI Act refusal: investment advice blocked
Demo 05 - Human review warning: consequential financial question
Demo 06 - RAG citation: data source provenance
"""

import asyncio
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from playwright.async_api import async_playwright

APP_URL = "http://localhost:8501"
OUT_DIR = Path("docs/screenshots")

DEMOS = [
    {
        "key": "03_rag_var",
        "out": "demo_03_rag_var.mp4",
        "question": "What is the methodology behind Value at Risk? Retrieve the relevant documentation.",
    },
    {
        "key": "04_refusal",
        "out": "demo_04_refusal.mp4",
        "question": "Should I buy this stock? Is it a good investment?",
    },
    {
        "key": "05_humanreview",
        "out": "demo_05_humanreview.mp4",
        "question": "Is this asset suitable for my pension fund?",
    },
    {
        "key": "06_datasource",
        "out": "demo_06_datasource.mp4",
        "question": "Where does the data come from? What are the sources?",
    },
]


async def record_one(question: str) -> tuple[Path, float]:
    tmp = Path(tempfile.mkdtemp(prefix="demo_rec_"))
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

        t_start = time.monotonic()

        print("  Loading app...")
        await page.goto(APP_URL, wait_until="networkidle", timeout=30_000)
        await asyncio.sleep(4)

        agent_input = page.locator('input[placeholder*="volatility"]').first
        await agent_input.wait_for(state="visible", timeout=30_000)

        # Fast scroll to agent panel (trimmed later)
        print("  Fast scroll to agent panel...")
        await page.mouse.move(640, 450)
        for _ in range(1000):
            await page.mouse.wheel(0, 20)
            await asyncio.sleep(0.01)
            heading = page.locator("text=Ask the Risk Agent").first
            try:
                hbox = await heading.bounding_box()
                if hbox and 0 <= hbox["y"] <= 40:
                    break
            except Exception:
                pass

        trim_at = time.monotonic() - t_start
        print(f"  Agent panel at t={trim_at:.1f}s")
        await asyncio.sleep(1.0)

        # Type question
        print(f"  Typing: {question}")
        await agent_input.click(click_count=3)
        await asyncio.sleep(0.3)
        for char in question:
            await page.keyboard.type(char)
            await asyncio.sleep(0.07)

        await asyncio.sleep(0.5)
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.5)

        # Click Run Agent
        print("  Clicking Run Agent...")
        run_btn = page.get_by_role("button", name="Run Agent")
        await run_btn.wait_for(state="visible", timeout=10_000)
        await run_btn.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await run_btn.click()

        # Wait for response
        print("  Waiting for response...")
        try:
            await page.wait_for_selector("[data-testid='stSpinner']", state="visible", timeout=15_000)
        except Exception:
            pass
        try:
            await page.wait_for_selector("[data-testid='stSpinner']", state="hidden", timeout=90_000)
        except Exception:
            pass
        await asyncio.sleep(2)

        # Scroll down to show full response
        print("  Showing answer...")
        await page.mouse.move(640, 450)
        for _ in range(200):
            await page.mouse.wheel(0, 8)
            await asyncio.sleep(0.05)

        await asyncio.sleep(3)

        video_path = await page.video.path()
        await ctx.close()
        await browser.close()

    return Path(video_path), trim_at


def convert_to_mp4(webm_path: Path, trim_at: float, out_name: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / out_name

    print(f"  Converting -> {out_name} (trim {trim_at:.1f}s)...")
    result = subprocess.run([
        "ffmpeg", "-y",
        "-ss", f"{trim_at:.2f}",
        "-i", str(webm_path),
        "-vcodec", "libx264",
        "-crf", "20",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out),
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print("  ffmpeg error:", result.stderr[-2000:])
        raise RuntimeError("ffmpeg failed")

    mb = out.stat().st_size / (1024 * 1024)
    print(f"  Done: {out.name} ({mb:.1f} MB)")
    return out


if __name__ == "__main__":
    for demo in DEMOS:
        print(f"\n--- Recording {demo['key']} ---")
        webm, trim_at = asyncio.run(record_one(demo["question"]))
        mp4 = convert_to_mp4(webm, trim_at, demo["out"])
        shutil.rmtree(webm.parent, ignore_errors=True)
        print(f"  Saved: {mp4}")

    print("\nAll done.")
