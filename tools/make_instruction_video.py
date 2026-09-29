"""Build the transparent instruction-change video from rendered rollout frames.

Usage:
    pip install numpy scipy pillow
    python tools/make_instruction_video.py path/to/s3_r16_seed3_OK [--last 226] [--fps 30]

The wall behind the table is removed (transparent); the robot, trajectory markers, table,
and objects are kept. The wall is a slightly warm gray (R - B ~ 5), while the robot and table
are neutral (R = G = B) and markers/objects are saturated, so the matte comes from that tint
above the table's back edge. Frames are cropped to 4:3 (the empty table at the bottom is cut),
the cut edges fade out softly, and the result is encoded twice: VP9 WebM with alpha (Chrome, Edge, Firefox) and HEVC with alpha (Safari,
needs macOS VideoToolbox). Requires ffmpeg with libvpx-vp9 and hevc_videotoolbox.
"""
import argparse
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
EDGE_Y = 680  # table back edge in the 2048x2048 frames; rows below are always kept
WALL = np.array([108.0, 106.0, 103.0])  # typical wall color, removed from semi-transparent edges
CROP = (0, 0, 2048, 1536)  # 4:3, drops the empty table at the bottom
SIZE = (1440, 1080)
# soft edges (px in the crop): the robot is cut by the camera at the top, the table by the crop at the
# sides and bottom. The table's back edge is a real edge and stays sharp. Objects end at y~1440.
FADE_TOP, FADE_SIDE, FADE_BOTTOM = 150, 245, 86


def smoothstep(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def edge_fade(h: int, w: int) -> np.ndarray:
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    return (smoothstep(y / FADE_TOP) * smoothstep((h - 1 - y) / FADE_BOTTOM)
            * smoothstep(x / FADE_SIDE) * smoothstep((w - 1 - x) / FADE_SIDE))


FADE = edge_fade(CROP[3] - CROP[1], CROP[2] - CROP[0])


def matte(rgb: np.ndarray) -> np.ndarray:
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    tint = r - b
    lum = f.mean(-1)
    grayish = (np.abs(r - g) <= 5) & (np.abs(g - b) <= 6) & (lum > 35) & (lum < 175)
    alpha = np.clip((4.6 - tint) / 3.6, 0, 1)  # wall tint ~5.3 -> 0, neutral robot -> 1
    alpha = np.where(grayish, alpha, 1.0)  # saturated markers, very dark or bright pixels are foreground
    alpha[EDGE_Y:] = 1.0

    # keep only foreground that is part of the robot/markers (large or touching the table), not wall speckles
    core = alpha > 0.5
    labels, n = ndi.label(core)
    keep = np.zeros(n + 1, bool)
    keep[np.unique(labels[EDGE_Y])] = True
    keep |= ndi.sum(core, labels, index=np.arange(n + 1)) > 1500
    keep[0] = False
    alpha = np.where(ndi.binary_dilation(keep[labels], iterations=3), alpha, 0.0)

    a = alpha[..., None]
    fg = np.where(a > 0.02, (f - (1 - a) * WALL) / np.maximum(a, 1e-3), f)
    return np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype(np.uint8)


def process(args):
    src, dst = args
    x0, y0, x1, y1 = CROP
    rgba = matte(np.asarray(Image.open(src).convert("RGB")))[y0:y1, x0:x1].copy()
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
