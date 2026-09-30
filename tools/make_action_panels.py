"""Extract the four action-prediction panels (paper Fig. D.3) without text and remove the wall.

Usage:
    pip install numpy scipy pillow pymupdf
    python tools/make_action_panels.py path/to/fix_scene_diff_inst.pdf

Uses the uncompressed figure PDF, where each panel is a lossless 751x561 image on page 1 and the
labels, dashed boxes, and "Detail" insets are separate vector/text layers. Writes
static/images/pred_{ft,craft}_{pick,place}.webp and prints the zoom-inset styles for index.html.
"""
import io
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

from matte import edge_fade, matte

ROOT = Path(__file__).resolve().parents[1]
W, H = 751, 561
EDGE_Y, MIN_BLOB = 119, 200
FADE = edge_fade(H, W, top=30, side=45, bottom=30)
# panel origin on the page (pt) -> output name
PANELS = {(2.4, 36.2): "pred_ft_pick", (196.2, 36.2): "pred_craft_pick",
          (2.4, 187.5): "pred_ft_place", (196.2, 187.5): "pred_craft_place"}
# zoom regions (x, y, w, h in panel px, 4:3) covering the predicted trajectories of both methods
ZOOM = {"pick": (297, 160, 160, 120), "place": (160, 153, 148, 111)}


def main(pdf_path: str) -> None:
    doc = pymupdf.open(pdf_path)
    page = doc[0]
    found = {}
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            for (x0, y0), name in PANELS.items():
                if abs(r.x0 - x0) < 0.5 and abs(r.y0 - y0) < 0.5:
                    found[name] = img[0]
    assert len(found) == 4, found
    out = ROOT / "static" / "images"
    for name, xref in found.items():
        rgb = Image.open(io.BytesIO(doc.extract_image(xref)["image"])).convert("RGB")
        assert rgb.size == (W, H), rgb.size
        rgba = matte(np.asarray(rgb), EDGE_Y, MIN_BLOB)
        rgba[..., 3] = (rgba[..., 3] * FADE).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(out / f"{name}.webp", "WEBP", quality=92)
        print(f"{name}.webp")
    for row, (x, y, w, h) in ZOOM.items():
        box = f"left: {x / W * 100:.2f}%; top: {y / H * 100:.2f}%; width: {w / W * 100:.2f}%; height: {h / H * 100:.2f}%"
        inset = f"background-size: {W / w * 100:.2f}% auto; background-position: {x / (W - w) * 100:.2f}% {y / (H - h) * 100:.2f}%"
        print(f"{row}: zoom-box {{{box}}}  zoom-inset {{{inset}}}")


if __name__ == "__main__":
    main(sys.argv[1])
