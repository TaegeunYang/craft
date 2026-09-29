"""Render the page's figures from the paper's figure PDFs and save them as WebP.

Usage:
    pip install pymupdf pillow
    python tools/render_figures.py path/to/Figures

`Figures` is the figure folder of the paper source (main figures at the top level,
appendix figures under `Appendix/`). Each PDF page is rendered at the target width,
trimmed to its non-white content, and written to static/images/.
"""
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops

OUT = Path(__file__).resolve().parents[1] / "static" / "images"

# output name: (source PDF relative to Figures/, page index, output width in px)
FIGURES = {
    "teaser": ("figure1_final_comp.pdf", 0, 2400),
    "overview": ("figure2_final_comp.pdf", 0, 2400),
    "benchmarks": ("figure3_final_comp.pdf", 0, 2400),
    "instruction_change": ("figure4_final_comp.pdf", 0, 2400),
    "tsne": ("figure5_final_comp.pdf", 0, 1400),
    "real_robot": ("figure6_final_comp.pdf", 0, 2400),
    "vision_shortcut": ("Appendix/vision_shortcut_comp.pdf", 0, 1400),
    "empty_instruction": ("Appendix/empty_instruction_comp.pdf", 0, 1400),
    "action_predictions": ("Appendix/fix_scene_diff_inst_comp.pdf", 0, 1400),
    "skill_reuse": ("Appendix/skill_kv_swap_comp.pdf", 0, 1400),
    "real_robot_more": ("Appendix/real_appendix_comp.pdf", 0, 2000),
}


def trim(img: Image.Image, pad_frac: float = 0.006) -> Image.Image:
    mask = ImageChops.difference(img, Image.new("RGB", img.size, "white")).convert("L").point(lambda v: 255 if v > 10 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img
    pad = max(4, int(img.width * pad_frac))
    return img.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, img.width), min(bbox[3] + pad, img.height)))


def main(fig_dir: str) -> None:
    fig_dir = Path(fig_dir)
    for name, (rel, page_idx, width) in FIGURES.items():
        page = pymupdf.open(fig_dir / rel)[page_idx]
        # render a bit wider than the target so trimming keeps the full target width
        zoom = width * 1.02 / page.rect.width
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        img = trim(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        if img.width > width:
            img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        img.save(OUT / f"{name}.webp", "WEBP", quality=88, method=6)
        print(f"{name:20s} {img.width}x{img.height}  <- {rel}")

    # Open Graph preview (1200x630) from the teaser
    teaser = Image.open(OUT / "teaser.webp").convert("RGB")
    scale = min(1140 / teaser.width, 570 / teaser.height)
    teaser = teaser.resize((round(teaser.width * scale), round(teaser.height * scale)), Image.LANCZOS)
    og = Image.new("RGB", (1200, 630), "white")
    og.paste(teaser, ((1200 - teaser.width) // 2, (630 - teaser.height) // 2))
    og.save(OUT / "og.jpg", "JPEG", quality=90)


if __name__ == "__main__":
    main(sys.argv[1])
