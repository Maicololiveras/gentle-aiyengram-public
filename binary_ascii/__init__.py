"""Reusable image-to-binary-ASCII conversion and presentation generation."""
from .core import AsciiFrame, Cell, convert_image, render_ansi, render_png, render_svg, render_text
from .presentation import build_presentation

__all__ = ["AsciiFrame", "Cell", "convert_image", "render_ansi", "render_png", "render_svg", "render_text", "build_presentation"]
