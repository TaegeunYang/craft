"""Build the transparent instruction-change video from rendered rollout frames.

Usage:
    pip install numpy scipy pillow
    python tools/make_instruction_video.py path/to/s3_r16_seed3_OK [--last 226] [--fps 30]

The wall behind the table is removed (see matte.py); the robot, trajectory markers, table, and
objects are kept. Frames are cropped to 4:3 (the empty table at the bottom is cut), the cut edges
fade out softly, and the result is encoded twice: VP9 WebM with alpha (Chrome, Edge, Firefox) and
HEVC with alpha (Safari, needs macOS VideoToolbox). Requires ffmpeg with libvpx-vp9 and
hevc_videotoolbox.
"""
import argparse
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from matte import edge_fade, matte

ROOT = Path(__file__).resolve().parents[1]
EDGE_Y = 680  # table back edge in the 2048x2048 frames; rows below are always kept
MIN_BLOB = 1500
CROP = (0, 0, 2048, 1536)  # 4:3, drops the empty table at the bottom
SIZE = (1440, 1080)
# soft edges (px in the crop): the robot is cut by the camera at the top, the table by the crop at the
# sides and bottom. The table's back edge is a real edge and stays sharp. Objects end at y~1440.
FADE = edge_fade(CROP[3] - CROP[1], CROP[2] - CROP[0], top=150, side=245, bottom=86)


def process(args):
    src, dst = args
    x0, y0, x1, y1 = CROP
    rgba = matte(np.asarray(Image.open(src).convert("RGB")), EDGE_Y, MIN_BLOB)[y0:y1, x0:x1].copy()
    rgba[..., 3] = (rgba[..., 3] * FADE).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").convert("RGBa").resize(SIZE, Image.LANCZOS).convert("RGBA").save(dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frames")
    ap.add_argument("--last", type=int, default=226)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--name", default="instruction_change")
    args = ap.parse_args()

    frames = Path(args.frames)
    videos = ROOT / "static" / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        jobs = [(frames / f"agentview_step_{i:05d}.png", Path(tmp) / f"f_{i:05d}.png") for i in range(args.last + 1)]
        with ProcessPoolExecutor() as pool:
            list(pool.map(process, jobs, chunksize=4))
        pattern = str(Path(tmp) / "f_%05d.png")
        common = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps), "-i", pattern]
        subprocess.run(common + ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "32", "-b:v", "0",
                                 "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-an",
                                 str(videos / f"{args.name}.webm")], check=True)
        subprocess.run(common + ["-c:v", "hevc_videotoolbox", "-allow_sw", "1", "-alpha_quality", "0.9",
                                 "-b:v", "4M", "-tag:v", "hvc1", "-pix_fmt", "bgra", "-an",
                                 str(videos / f"{args.name}_hevc.mov")], check=True)
        Image.open(jobs[0][1]).save(ROOT / "static" / "images" / f"{args.name}_poster.webp", "WEBP", quality=90)
    for p in sorted(videos.glob(f"{args.name}*")):
        print(f"{p.name}: {p.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
