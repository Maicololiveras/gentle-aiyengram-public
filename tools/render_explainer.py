"""Render the binary-ascii presentation into a narrated publication video."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples/gentleman-explainer"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
W, H = 1280, 720


def color(hexcode: str) -> tuple[int, int, int]:
    return tuple(bytes.fromhex(hexcode.lstrip("#")))


def draw_scene(scene: dict, raw: dict, index: int, count: int) -> Image.Image:
    image = Image.new("RGB", (W, H), (6, 13, 24))
    draw = ImageDraw.Draw(image)
    accent = color(scene["accent"])
    faint = tuple(max(16, int(c * .32)) for c in accent)
    for x in range(0, W, 40):
        draw.line((x, 0, x, H), fill=(10, 21, 35), width=1)
    for y in range(0, H, 40):
        draw.line((0, y, W, y), fill=(10, 21, 35), width=1)
    for j in range(15):
        cx, cy = 982, 342
        r = 315 - j * 14
        shade = tuple(9 + int(c * .04 * (j / 15)) for c in accent)
        draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=shade, width=1)
    glyph_font = ImageFont.truetype(MONO, 7)
    cw, ch = 5, 4
    art_w, art_h = scene["columns"] * cw, scene["rows"] * ch
    ox, oy = 694 + (550 - art_w) // 2, 74 + (572 - art_h) // 2
    for x, y, glyph, r, g, b, alpha in scene["cells"]:
        rr, gg, bb = (max(18, int(value * alpha / 255)) for value in (r, g, b))
        draw.text((ox + x * cw, oy + y * ch - 2), glyph, fill=(rr, gg, bb), font=glyph_font)
    draw.rounded_rectangle((41, 38, 351, 77), radius=18, outline=faint, width=2)
    draw.text((59, 47), "GENTLEMAN  /  ECOSYSTEM", font=ImageFont.truetype(MONO, 19), fill=accent)
    draw.text((61, 117), raw["eyebrow"], font=ImageFont.truetype(MONO, 23), fill=accent)
    title_font = ImageFont.truetype(BOLD, 51)
    title_lines = raw["title"].split("\n")
    y = 166 if len(title_lines) > 1 else 193
    for line in title_lines:
        draw.text((57, y), line, font=title_font, fill=(246, 247, 254), stroke_width=0)
        y += 65
    cap_font = ImageFont.truetype(FONT, 24)
    import textwrap
    for j, line in enumerate(textwrap.wrap(raw["caption"].strip(), width=39)[:2]):
        draw.text((61, 344 + j * 34), line, font=cap_font, fill=(174, 194, 213))
    draw.rounded_rectangle((57, 453, 651, 625), radius=14, fill=(10, 23, 38), outline=(43, 64, 81), width=2)
    draw.ellipse((74, 470, 84, 480), fill=(255, 113, 143))
    draw.ellipse((92, 470, 102, 480), fill=(255, 196, 107))
    draw.ellipse((110, 470, 120, 480), fill=(119, 211, 188))
    mono = ImageFont.truetype(MONO, 20)
    for j, line in enumerate(raw["terminal"][:3]):
        draw.text((78, 494 + j * 38), line, font=mono, fill=(204, 231, 235) if j < 2 else accent)
    draw.text((59, 674), "GENTLE AI   /   GENTLE SHELL   /   PI   /   ODD   /   ENGRAM", font=ImageFont.truetype(MONO, 15), fill=(107, 132, 151))
    draw.text((1153, 667), f"{index+1:02d} / {count:02d}", font=ImageFont.truetype(MONO, 19), fill=accent)
    draw.rectangle((0, 709, W, 720), fill=(20, 37, 51))
    draw.rectangle((0, 709, round(W * (index+1) / count), 720), fill=accent)
    return image


def main() -> None:
    package = json.loads((BASE / "generated/presentation.json").read_text(encoding="utf-8"))
    raw = json.loads((BASE / "timed-storyboard.json").read_text(encoding="utf-8"))
    out = BASE / "video"
    out.mkdir(exist_ok=True)
    concat = []
    for i, (scene, metadata) in enumerate(zip(package["scenes"], raw["scenes"])):
        still = out / f"scene-{i+1:02d}.png"
        draw_scene(scene, metadata, i, len(package["scenes"])).save(still, optimize=True)
        concat += [f"file '{still}'", f"duration {scene['duration']:.3f}"]
    concat.append(f"file '{out / ('scene-' + str(len(package['scenes'])).zfill(2) + '.png')}'")
    (out / "frames.txt").write_text("\n".join(concat) + "\n")
    print(f"Rendered {len(package['scenes'])} binary glyph scenes at {W}x{H}")


if __name__ == "__main__":
    main()
