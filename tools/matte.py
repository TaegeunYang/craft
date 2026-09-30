"""Remove the wall behind the table in LIBERO agentview renders.

The wall is a slightly warm gray (R - B ~ 5), while the robot and table are neutral (R = G = B)
and markers/objects are saturated, so the matte comes from that tint above the table's back edge.
Semi-transparent edge pixels are decontaminated by removing the wall color mixed into them.
"""
import numpy as np
from scipy import ndimage as ndi

WALL = np.array([108.0, 106.0, 103.0])  # wall color in these renders


def smoothstep(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def edge_fade(h: int, w: int, top: float, side: float, bottom: float) -> np.ndarray:
    """Alpha multiplier that fades the top, left/right, and bottom borders of an h x w image."""
    y = np.arange(h, dtype=np.float32)[:, None]
    x = np.arange(w, dtype=np.float32)[None, :]
    return (smoothstep(y / top) * smoothstep((h - 1 - y) / bottom)
            * smoothstep(x / side) * smoothstep((w - 1 - x) / side))


def matte(rgb: np.ndarray, edge_y: int, min_blob: int) -> np.ndarray:
    """RGBA image with the wall above row `edge_y` made transparent.

    `min_blob` is the pixel count above which a foreground blob in the wall band counts as the
    robot or a marker even if it does not touch the table edge; smaller blobs are wall speckles.
    """
    f = rgb.astype(np.float32)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    tint = r - b
    lum = f.mean(-1)
    grayish = (np.abs(r - g) <= 5) & (np.abs(g - b) <= 6) & (lum > 35) & (lum < 175)
    alpha = np.clip((4.6 - tint) / 3.6, 0, 1)  # wall tint ~5.3 -> 0, neutral robot -> 1
    alpha = np.where(grayish, alpha, 1.0)  # saturated markers, very dark or bright pixels are foreground
    alpha[edge_y:] = 1.0

    core = alpha > 0.5
    labels, n = ndi.label(core)
    keep = np.zeros(n + 1, bool)
    keep[np.unique(labels[edge_y])] = True
    keep |= ndi.sum(core, labels, index=np.arange(n + 1)) > min_blob
    keep[0] = False
    alpha = np.where(ndi.binary_dilation(keep[labels], iterations=3), alpha, 0.0)

    a = alpha[..., None]
    fg = np.where(a > 0.02, (f - (1 - a) * WALL) / np.maximum(a, 1e-3), f)
    return np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype(np.uint8)
