"""Crop the real-robot rollout videos to 4:3, stamp "x1" (real-time playback), and encode for the web.

Usage:
    pip install pillow
    python tools/make_real_videos.py path/to/dir_with_videos

Expects <cube>2<plate>.mp4 files (1280x720) in the given directory, e.g. blue2green.mp4, and writes
static/videos/real/<cube>_<plate>_craft.mp4 plus a poster image per video. The crop keeps x = 80..1040,
which centers the robot and objects (x ~ 220..900) in every recording. Requires ffmpeg with libx264.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CROP_X, CROP_W, H = 80, 960, 720
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
VIDEOS = ["blue2green", "red2yellow", "yellow2blue", "yellow2red", "blue2red"]


def speed_label(path: Path, text: str = "x1") -> None:
    im = Image.new("RGBA", (CROP_W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 52)
    left, top, right, bottom = d.textbbox((0, 0), text, font=font)
    pad_x, pad_y, margin = 18, 12, 22
    x1, y1 = CROP_W - margin, H - margin
    x0, y0 = x1 - (right - left) - 2 * pad_x, y1 - (bottom - top) - 2 * pad_y
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(0, 0, 0, 120))
    d.text((x0 + pad_x - left, y0 + pad_y - top), text, font=font, fill=(255, 255, 255, 255))
    im.save(path)


def main(src_dir: str) -> None:
    out = ROOT / "static" / "videos" / "real"
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        label = Path(tmp) / "x1.png"
        speed_label(label)
        for name in VIDEOS:
            cube, plate = name.split("2")
            dst = out / f"{cube}_{plate}_craft.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(Path(src_dir) / f"{name}.mp4"), "-i", str(label),
                            "-filter_complex", f"[0:v]crop={CROP_W}:{H}:{CROP_X}:0[v];[v][1:v]overlay=0:0",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p",
                            "-movflags", "+faststart", "-an", str(dst)], check=True)
            first = Path(tmp) / f"{name}_first.png"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(dst), "-frames:v", "1", str(first)], check=True)
            Image.open(first).save(ROOT / "static" / "images" / f"real_{cube}_{plate}_poster.webp", "WEBP", quality=82)
            print(f"{dst.name}: {dst.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main(sys.argv[1])
