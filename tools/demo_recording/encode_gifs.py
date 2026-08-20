"""
Re-encode all 6 WebM recordings to GIFs.

Run this when the recordings exist but GIF encoding was interrupted.
Maps each temp dir to its scenario key based on creation timestamp order.
"""

import sys
from pathlib import Path

# --- WebM paths in creation-time order (confirmed by stat timestamps) ---
WEBM_MAP = {
    "01_dashboard": r"C:\Users\rezaa\AppData\Local\Temp\demo01_fc6pnwws\page@407d853ff6386e90dbaec78ad026607f.webm",
    "02_volatility": r"C:\Users\rezaa\AppData\Local\Temp\demo_Scen_p_a3_m9g\page@6710436609fd73372ca5bbfd3a66c1a9.webm",
    "03_rag": r"C:\Users\rezaa\AppData\Local\Temp\demo_Scen_7bbhm280\page@24dc4005aa309cd8474e590f075554be.webm",
    "04_refusal": r"C:\Users\rezaa\AppData\Local\Temp\demo_Scen_9ufeb0h4\page@bd703b7df4306fccf3984e5f0de0b4f6.webm",
    "05_humanreview": r"C:\Users\rezaa\AppData\Local\Temp\demo_Scen_zzpr3dmn\page@f8dd45996520d8d2d7794ff4eb167162.webm",
    "06_datasource": r"C:\Users\rezaa\AppData\Local\Temp\demo_Scen_isksd18_\page@ebd450602669e5f7deed8764e82fa369.webm",
}

OUT_DIR  = Path("docs/screenshots")
GIF_W    = 1280
GIF_FPS  = 12
MAX_MB   = 9.8


def build_pil_frames(raw_frames, gif_w, colors):
    from PIL import Image
    out = []
    for f in raw_frames:
        img = Image.fromarray(f)
        h   = int(img.height * gif_w / img.width)
        img = img.resize((gif_w, h), Image.LANCZOS)
        img = img.quantize(colors=colors, dither=Image.Dither.FLOYDSTEINBERG)
        out.append(img)
    return out


def write_gif(pil_frames, path, gif_fps):
    dur = int(1000 / gif_fps)
    pil_frames[0].save(
        str(path), save_all=True, append_images=pil_frames[1:],
        optimize=True, duration=dur, loop=0,
    )
    return path.stat().st_size / (1024 * 1024)


def encode_one(key, webm_path):
    import imageio
    print(f"\n=== demo_{key} ===")
    print(f"  Reading {Path(webm_path).name}")

    reader     = imageio.get_reader(webm_path)
    source_fps = reader.get_meta_data().get("fps", 25)
    raw_frames = [f for f in reader]
    reader.close()
    print(f"  {len(raw_frames)} frames @ {source_fps:.0f} fps")

    # Sample to GIF_FPS — natural speed (no speedup beyond fps downconversion)
    step   = max(1, round(source_fps / GIF_FPS))
    frames = raw_frames[::step]
    print(f"  -> {len(frames)} sampled frames (step={step})")

    base = OUT_DIR / f"demo_{key}.gif"

    # Try progressively smaller palettes
    for colors in [128, 96, 64, 48]:
        print(f"  colors={colors}...", end=" ", flush=True)
        pil   = build_pil_frames(frames, GIF_W, colors)
        size  = write_gif(pil, base, GIF_FPS)
        print(f"{size:.1f} MB")
        if size <= MAX_MB:
            print(f"  OK: {base.name}")
            return {key: [base]}

    # Still too large — split into part_a / part_b
    print(f"  Splitting into part_a / part_b...")
    base.unlink(missing_ok=True)

    mid    = len(frames) // 2
    part_a = OUT_DIR / f"demo_{key}_part_a.gif"
    part_b = OUT_DIR / f"demo_{key}_part_b.gif"
    result = []

    for ppath, pframes in [(part_a, frames[:mid]), (part_b, frames[mid:])]:
        for colors in [128, 96, 64, 48]:
            pil  = build_pil_frames(pframes, GIF_W, colors)
            size = write_gif(pil, ppath, GIF_FPS)
            if size <= MAX_MB:
                print(f"  {ppath.name}: {size:.1f} MB ({colors} colors)")
                result.append(ppath)
                break
        else:
            print(f"  WARNING: {ppath.name} {size:.1f} MB (keeping best effort)")
            result.append(ppath)

    return {key: result}


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Allow running a single key: python encode_gifs.py 03_rag
    keys = sys.argv[1:] if len(sys.argv) > 1 else list(WEBM_MAP.keys())

    manifest = {}
    for key in keys:
        webm = WEBM_MAP[key]
        if not Path(webm).exists():
            print(f"MISSING WebM for {key}: {webm}")
            continue
        manifest.update(encode_one(key, webm))

    print("\n--- Summary ---")
    for key, paths in manifest.items():
        for p in paths:
            mb = p.stat().st_size / (1024 * 1024)
            print(f"  {p.name}: {mb:.1f} MB")
