"""Estimate simple image backgrounds and isolate the foreground for glyph art.

This is an edge-color matte, intended for plain or smoothly graded backgrounds.
It never replaces the photographed/illustrated foreground pixels with AI content.
"""
from __future__ import annotations

from collections import deque

import numpy as np
from PIL import Image, ImageFilter


def _smooth(values: np.ndarray, radius: int = 12) -> np.ndarray:
    kernel = np.exp(-.5 * (np.arange(-radius, radius + 1) / max(1, radius / 2)) ** 2)
    kernel /= kernel.sum()
    padded = np.pad(values, radius, mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def _side_color(rgb: np.ndarray, side: str, neutral: bool) -> np.ndarray:
    height, width = rgb.shape[:2]
    band = max(4, round(width * .12))
    pixels = rgb[:, :band] if side == "left" else rgb[:, -band:]
    chroma = pixels.max(2) - pixels.min(2)
    values = np.full((height, 3), np.nan, dtype=np.float32)
    for y in range(height):
        row = pixels[y]
        accepted = (chroma[y] < 28) if neutral else np.ones(len(row), dtype=bool)
        if accepted.sum() >= min(8, len(row) // 2):
            selected = row[accepted]
            # Median rejects an object that briefly touches the frame edge.
            values[y] = np.median(selected, axis=0)
    for channel in range(3):
        known = np.flatnonzero(np.isfinite(values[:, channel]))
        if not len(known):
            values[:, channel] = np.median(pixels[:, :, channel])
        else:
            values[:, channel] = np.interp(np.arange(height), known, values[known, channel])
            values[:, channel] = _smooth(values[:, channel])
    return values


def _fill_small_holes(mask: np.ndarray, limit: int) -> np.ndarray:
    """Preserve light details enclosed by outlines without filling large gaps."""
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    for y in range(height):
        for x in range(width):
            if mask[y, x] or seen[y, x]:
                continue
            cells = []
            queue = deque([(y, x)])
            seen[y, x] = True
            touches_edge = False
            while queue:
                cy, cx = queue.popleft()
                if len(cells) <= limit:
                    cells.append((cy, cx))
                if cy == 0 or cx == 0 or cy == height - 1 or cx == width - 1:
                    touches_edge = True
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and not mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            if not touches_edge and len(cells) <= limit:
                for cy, cx in cells:
                    mask[cy, cx] = True
    return mask


def remove_background(image: Image.Image, *, tolerance: int = 24) -> Image.Image:
    """Return an RGBA copy with a soft, edge-estimated background matte.

    Existing alpha is respected. Best on flat/graded backgrounds; complex
    backgrounds may need an externally prepared transparency mask instead.
    """
    if not 0 <= tolerance <= 100:
        raise ValueError("background tolerance must be 0..100")
    original = image.convert("RGBA")
    if original.getchannel("A").getextrema()[0] < 240:
        return original
    preview = original.copy()
    preview.thumbnail((768, 768), Image.Resampling.LANCZOS)
    rgb = np.asarray(preview.convert("RGB"), dtype=np.float32)
    height, width = rgb.shape[:2]
    border = np.concatenate((rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]))
    neutral = float(np.mean(border.max(1) - border.min(1) < 28)) > .45
    left, right = _side_color(rgb, "left", neutral), _side_color(rgb, "right", neutral)
    fraction = np.linspace(0, 1, width, dtype=np.float32)[None, :, None]
    backdrop = left[:, None, :] * (1 - fraction) + right[:, None, :] * fraction
    distance = np.sqrt(np.mean((rgb - backdrop) ** 2, axis=2))
    color_difference = (rgb.max(2) - rgb.min(2)) - (backdrop.max(2) - backdrop.min(2))
    distance = np.maximum(distance, color_difference * .9)
    strength = np.clip((distance - tolerance) / 22, 0, 1)
    # Join tiny gaps in outlines, then recover enclosed pale areas such as hair.
    strong = Image.fromarray(np.uint8(strength > .62) * 255, "L")
    strong = strong.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))
    protected = _fill_small_holes(np.asarray(strong, dtype=np.uint8).copy() > 0,
                                  max(32, round(width * height * .07)))
    matte = np.maximum(strength, protected.astype(np.float32) * .92)
    alpha = Image.fromarray(np.uint8(np.clip(matte * 255, 0, 255)), "L")
    alpha = alpha.resize(original.size, Image.Resampling.BILINEAR)
    original.putalpha(alpha)
    return original


def inspect_image(image: Image.Image) -> dict:
    """Small, deterministic color report for choosing a display theme."""
    image = image.convert("RGBA")
    sample = image.copy()
    sample.thumbnail((256, 256), Image.Resampling.LANCZOS)
    rgba = np.asarray(sample, dtype=np.uint8)
    rgb = rgba[:, :, :3]
    border = np.concatenate((rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]))
    border_rgb = np.median(border, axis=0).astype(int)
    backdrop_brightness = float(border_rgb @ np.array([.2126, .7152, .0722]))
    foreground = np.asarray(remove_background(sample), dtype=np.uint8)
    solid = rgb[foreground[:, :, 3] > 128]
    if not len(solid):
        solid = rgb.reshape(-1, 3)
    quantized = (solid // 32) * 32 + 16
    colors, counts = np.unique(quantized, axis=0, return_counts=True)
    palette = ["#%02x%02x%02x" % tuple(color) for color in colors[np.argsort(counts)[-5:][::-1]]]
    return {"background_estimate": "#%02x%02x%02x" % tuple(border_rgb),
            "background_brightness": round(backdrop_brightness),
            "suggested_theme": "light" if backdrop_brightness > 150 else "terminal",
            "transparent_source": bool((rgba[:, :, 3] < 240).any()),
            "detected_colors": palette}
