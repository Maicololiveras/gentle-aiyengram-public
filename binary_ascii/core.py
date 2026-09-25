"""Deterministic binary typography derived from source image pixels."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


@dataclass(frozen=True)
class Cell:
    glyph: str
    rgb: tuple[int, int, int]
    alpha: int


@dataclass(frozen=True)
class AsciiFrame:
    columns: int
    rows: int
    cells: tuple[Cell | None, ...]

    def at(self, x: int, y: int) -> Cell | None:
        return self.cells[y * self.columns + x]

    def records(self) -> list[list[int | str]]:
        """Compact data for a browser Canvas: [x, y, glyph, r, g, b, alpha]."""
        return [[x, y, cell.glyph, *cell.rgb, cell.alpha]
                for y in range(self.rows) for x in range(self.columns)
                if (cell := self.at(x, y)) is not None]


def convert_image(source: str | Path | Image.Image, *, columns: int = 100,
                  rows: int | None = None, glyphs: str = "01", cell_aspect: float = .5,
                  alpha_threshold: int = 20, min_luminance: int = 0,
                  saturation: float = 1.0,
                  max_cells: int = 120_000) -> AsciiFrame:
    """Sample source RGBA pixels; never paste the raster into the output.

    cell_aspect is cell width / cell height. Use ~0.5 for ordinary terminal
    fonts or 1.0 for square cells in a pixel-precise web presentation.
    """
    if not 1 <= columns <= 2000: raise ValueError("columns must be 1..2000")
    if not 0 < cell_aspect <= 4: raise ValueError("cell_aspect must be >0 and <=4")
    if not 0 <= alpha_threshold <= 255: raise ValueError("alpha_threshold must be 0..255")
    if not 0 <= min_luminance <= 255: raise ValueError("min_luminance must be 0..255")
    if not .2 <= saturation <= 3: raise ValueError("saturation must be 0.2..3")
    if len(glyphs) != 2 or not all(c.isprintable() for c in glyphs):
        raise ValueError("glyphs must contain exactly two printable characters")
    if isinstance(source, Image.Image): image = source.copy()
    else:
        with Image.open(source) as loaded: image = loaded.copy()
    image = ImageOps.exif_transpose(image).convert("RGBA")
    if saturation != 1:
        image = ImageEnhance.Color(image).enhance(saturation)
    auto_rows = rows is None
    if auto_rows: rows = max(1, round(columns * image.height / image.width * cell_aspect))
    if rows < 1 or columns * rows > max_cells:
        raise ValueError(f"requested grid exceeds {max_cells:,} cells")
    # Cell coordinates are not square pixels. Fit in physical cell units so
    # the image retains its proportions after the glyph grid is rendered.
    if auto_rows:
        fitted_size = (columns, rows)
    else:
        needed_rows = columns * image.height / image.width * cell_aspect
        if needed_rows <= rows:
            fitted_size = (columns, max(1, round(needed_rows)))
        else:
            fitted_size = (max(1, round(rows * image.width / image.height / cell_aspect)), rows)
    fitted = image.resize(fitted_size, Image.Resampling.LANCZOS)
    stage = Image.new("RGBA", (columns, rows))
    stage.alpha_composite(fitted, ((columns-fitted.width)//2, (rows-fitted.height)//2))
    pixels = stage.load()
    cells: list[Cell | None] = []
    for y in range(rows):
        for x in range(columns):
            r, g, b, alpha = pixels[x, y]
            if alpha < alpha_threshold: cells.append(None); continue
            luminance = (54*r + 183*g + 19*b) // 256
            if luminance < min_luminance:
                # Lift dark petals against dark backgrounds without flattening hue.
                delta = min_luminance - luminance
                r, g, b = (min(255, c + delta) for c in (r, g, b))
            # '0' has more ink than '1' in most monospace faces. Place it more
            # often in dark regions so the binary drawing retains local value.
            glyph = glyphs[0 if ((x * 73 + y * 151) % 256) < 255 - luminance else 1]
            cells.append(Cell(glyph, (int(r), int(g), int(b)), alpha))
    return AsciiFrame(columns, rows, tuple(cells))


def render_text(frame: AsciiFrame, *, empty: str = " ") -> str:
    if len(empty) != 1: raise ValueError("empty must be one character")
    return "\n".join("".join(frame.at(x,y).glyph if frame.at(x,y) else empty
                            for x in range(frame.columns)) for y in range(frame.rows)) + "\n"


def render_ansi(frame: AsciiFrame, *, background: tuple[int,int,int] | None = None) -> str:
    lines=[]
    bg=(f"\x1b[48;2;{background[0]};{background[1]};{background[2]}m" if background else "")
    for y in range(frame.rows):
        parts=[bg]; previous=None
        for x in range(frame.columns):
            cell=frame.at(x,y)
            if cell is None:parts.append(" ");continue
            if cell.rgb!=previous:
                parts.append(f"\x1b[38;2;{cell.rgb[0]};{cell.rgb[1]};{cell.rgb[2]}m")
                previous=cell.rgb
            parts.append(cell.glyph)
        parts.append("\x1b[0m")
        lines.append("".join(parts))
    return "\n".join(lines)+"\n"


def _font(size: int, path: str | Path | None = None) -> ImageFont.FreeTypeFont:
    candidates = [str(path)] if path else []
    candidates += ["DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                   "DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
    for candidate in candidates:
        try:return ImageFont.truetype(candidate, size)
        except OSError:continue
    raise FileNotFoundError("Install a monospace TrueType font or pass --font")


def render_png(frame: AsciiFrame, *, cell_width: int = 8, cell_height: int = 12,
               background: tuple[int,int,int] = (4,8,16),
               font_path: str | Path | None = None) -> Image.Image:
    if cell_width < 3 or cell_height < 4: raise ValueError("cells too small")
    image=Image.new("RGB",(frame.columns*cell_width,frame.rows*cell_height),background)
    draw=ImageDraw.Draw(image)
    font=_font(max(5,cell_height),font_path)
    for y in range(frame.rows):
        for x in range(frame.columns):
            cell=frame.at(x,y)
            if cell is None:continue
            # Alpha blends pixels over the requested background; no raster layer.
            color=tuple((c*cell.alpha+bg*(255-cell.alpha))//255
                        for c,bg in zip(cell.rgb,background))
            draw.text((x*cell_width,y*cell_height-2),cell.glyph,font=font,fill=color)
    return image


def render_svg(frame: AsciiFrame, *, cell_width: int = 8, cell_height: int = 12,
               background: str = "#040810") -> str:
    width,height=frame.columns*cell_width,frame.rows*cell_height
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
         f'<rect width="100%" height="100%" fill="{escape(background,quote=True)}"/>',
         f'<g font-family="monospace" font-size="{cell_height}" font-weight="700">']
    for y in range(frame.rows):
        for x in range(frame.columns):
            cell=frame.at(x,y)
            if cell is None:continue
            r,g,b=cell.rgb
            out.append(f'<text x="{x*cell_width}" y="{(y+1)*cell_height-2}" fill="rgb({r},{g},{b})" opacity="{cell.alpha/255:.3f}">{escape(cell.glyph)}</text>')
    return "\n".join(out+["</g>","</svg>"])+"\n"
