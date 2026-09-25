"""Reusable image-to-binary-ASCII conversion and presentation generation."""
from .core import AsciiFrame, Cell, convert_image, render_ansi, render_png, render_svg, render_text
from .background import inspect_image, remove_background
from .presentation import build_presentation

__all__ = ["AsciiFrame", "Cell", "convert_image", "render_ansi", "render_png", "render_svg", "render_text", "build_presentation", "inspect_image", "remove_background"]
