"""Build the explorer's FT (Full) vs CRAFT rollout videos with the wall removed.

Usage:
    pip install numpy scipy pillow
    python tools/make_explorer_videos.py ~/demo_selected [--model pi05] [--only TASK_SUBSTRING]

Input layout: <benchmark>/<task>/<model>/scene<idx>/frame_XXXX.png (1024x1024 agentview renders),
benchmark in {4quad, press}; a model directory containing "craft" is CRAFT, the other one FT (Full).
Both models of a task share the initial scene. The two videos of a task get the same length:
  - FT failed (hit the step limit): both use CRAFT's frame count, FT is cut there.
  - both succeeded (demonstrated combination): the longer length, the shorter video holds its last frame.
Frames are matted (see matte.py), cropped to 4:3 from the top, faded at the cut edges (the table only at
the sides and bottom), resized to 640x480, and encoded as VP9 WebM with alpha (Chrome, Edge, Firefox) and HEVC with alpha (Safari).
Writes static/videos/explorer/<model>/<pick_place|pick_place_press>/<cube>_<plate>[_<button>]_<ft|craft>{.webm,_hevc.mov,_poster.webp};
list the model in data-video-models on the explorer in index.html so the page shows its videos.
"""
import argparse
import re
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from functools import lru_cache

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from matte import matte, smoothstep

ROOT = Path(__file__).resolve().parents[1]
BENCH = {"4quad": "pick_place", "press": "pick_place_press"}
TASK = re.compile(r"pick_up_the_(\w+?)_block_and_place_it_on_the_(\w+?)_plate(?:_then_press_the_(\w+?)_button)?$")
FPS = 30
EDGE_Y, MIN_BLOB = 339, 375  # table back edge / speckle threshold in the 1024x1024 renders
CROP = (0, 0, 1024, 768)  # 4:3 from the top; objects end at y ~ 690
SIZE = (640, 480)
# Soft edges. The top fade applies to everything (the camera cuts the robot there). The side and bottom
# fades only soften the table: pixels that differ from the first frame (robot, trail, moved objects) stay
# opaque, since the robot reaches the frame edges in many rollouts.
_H, _W = CROP[3] - CROP[1], CROP[2] - CROP[0]
_Y = np.arange(_H, dtype=np.float32)[:, None]
_X = np.arange(_W, dtype=np.float32)[None, :]
FADE_TOP = smoothstep(_Y / 75) * np.ones((1, _W), np.float32)
FADE_TABLE = smoothstep((_H - 1 - _Y) / 43) * smoothstep(_X / 122) * smoothstep((_W - 1 - _X) / 122)


@lru_cache(maxsize=4)
def reference(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int16)


def process(args):
    src, ref, dst = args
    x0, y0, x1, y1 = CROP
    rgb = np.asarray(Image.open(src).convert("RGB"))
    rgba = matte(rgb, EDGE_Y, MIN_BLOB)[y0:y1, x0:x1].astype(np.float32)
    diff = np.abs(rgb.astype(np.int16) - reference(str(ref))).max(-1)[y0:y1, x0:x1].astype(np.float32)
    moving = ndi.gaussian_filter(ndi.grey_dilation(smoothstep((diff - 10) / 25), size=(5, 5)), 1.5)
    rgba[..., 3] *= FADE_TOP * (FADE_TABLE + (1 - FADE_TABLE) * moving)
    Image.fromarray(rgba.astype(np.uint8), "RGBA").convert("RGBa").resize(SIZE, Image.LANCZOS).convert("RGBA").save(dst)


def frames_of(model_dir: Path) -> list[Path]:
    scenes = sorted(model_dir.glob("scene*"))
    assert len(scenes) == 1, model_dir
    return sorted(scenes[0].glob("frame_*.png"))


def encode(pattern: str, out_base: Path) -> None:
    common = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern]
    subprocess.run(common + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "34", "-b:v", "0", "-row-mt", "1",
                             "-deadline", "good", "-cpu-used", "2", "-an", f"{out_base}.webm"], check=True)
    hevc = common + ["-c:v", "hevc_videotoolbox", "-allow_sw", "1", "-alpha_quality", "0.9", "-b:v", "0.9M",
                     "-tag:v", "hvc1", "-pix_fmt", "bgra", "-an", f"{out_base}_hevc.mov"]
    for attempt in range(3):  # VideoToolbox occasionally fails to open a session; a retry succeeds
        if subprocess.run(hevc).returncode == 0:
            break
        time.sleep(2)
    else:
        raise RuntimeError(f"HEVC encoding failed: {out_base}_hevc.mov")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--model", default="pi05", help="output folder name, matching the explorer's data-model")
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    root = Path(args.root).expanduser()
    for bench_dir in sorted(root.iterdir()):
        if bench_dir.name not in BENCH:
            continue
        out_dir = ROOT / "static" / "videos" / "explorer" / args.model / BENCH[bench_dir.name]
        out_dir.mkdir(parents=True, exist_ok=True)
        for task_dir in sorted(bench_dir.iterdir()):
            match = TASK.match(task_dir.name)
            if not task_dir.is_dir() or not match or args.only not in task_dir.name:
                continue
            cube, plate, button = match.groups()
            models = {("craft" if "craft" in m.name else "ft"): frames_of(m) for m in task_dir.iterdir() if m.is_dir()}
            craft, ft = models["craft"], models["ft"]
            demonstrated = cube == plate and (button is None or button == cube)
            n = max(len(craft), len(ft)) if demonstrated else len(craft)
            stem = "_".join(c for c in (cube, plate, button) if c)
            with tempfile.TemporaryDirectory() as tmp, ProcessPoolExecutor() as pool:
                for method, frames in (("ft", ft), ("craft", craft)):
                    seq = [frames[min(i, len(frames) - 1)] for i in range(n)]  # cut, or hold the last frame
                    work = Path(tmp) / method
                    work.mkdir()
                    list(pool.map(process, [(f, seq[0], work / f"f_{i:05d}.png") for i, f in enumerate(seq)], chunksize=8))
                    base = out_dir / f"{stem}_{method}"
                    encode(str(work / "f_%05d.png"), base)
                    Image.open(work / "f_00000.png").save(f"{base}_poster.webp", "WEBP", quality=80)
            print(f"{BENCH[bench_dir.name]}/{stem}: craft={len(craft)} ft={len(ft)} -> {n} frames "
                  f"({'demonstrated' if demonstrated else 'undemonstrated'})")


if __name__ == "__main__":
    main()
