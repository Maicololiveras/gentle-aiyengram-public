"""`binary-ascii`: files, ANSI terminal playback, and web presentations."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from PIL import Image, ImageOps

from .core import AsciiFrame, convert_image, render_ansi, render_png, render_svg, render_text
from .background import inspect_image
from .presentation import build_presentation


def _rgb(value: str) -> tuple[int,int,int]:
    value=value.removeprefix("#")
    if len(value)!=6:
        raise argparse.ArgumentTypeError("color must be #RRGGBB")
    try:return tuple(int(value[i:i+2],16) for i in (0,2,4))
    except ValueError as error:raise argparse.ArgumentTypeError("color must be #RRGGBB") from error


def _image_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("image",type=Path,help="Any Pillow-supported raster image")
    p.add_argument("--width",type=int,default=100,help="ASCII columns (default 100)")
    p.add_argument("--height",type=int,help="ASCII rows; auto by image aspect")
    p.add_argument("--cell-aspect",type=float,default=.5,help="Width/height of terminal cell (default .5; use 1 for square pixels)")
    p.add_argument("--glyphs",default="01",help="Exactly two characters; default 01")
    p.add_argument("--min-luminance",type=int,help="Lift dark source pixels (terminal theme defaults to 85)")
    p.add_argument("--alpha-threshold",type=int,default=20)
    p.add_argument("--saturation",type=float,default=1.0,help="Color saturation (1 keeps source colors; e.g. 1.2 for vivid glyphs)")
    p.add_argument("--theme",choices=["source","auto","terminal","light"],default="source",
                   help="Auto detects source colors; terminal isolates the subject on dark navy")
    p.add_argument("--remove-background",action="store_true",help="Isolate foreground against a plain or graded background")
    p.add_argument("--background-tolerance",type=int,default=24,help="Background matching tolerance 0..100")


def _theme(args: argparse.Namespace) -> str:
    if args.theme != "auto":return args.theme
    with Image.open(args.image) as source:
        return inspect_image(ImageOps.exif_transpose(source))["suggested_theme"]


def _frame(args: argparse.Namespace, theme: str | None = None) -> AsciiFrame:
    theme=theme or _theme(args)
    return convert_image(args.image,columns=args.width,rows=args.height,
                         glyphs=args.glyphs,cell_aspect=args.cell_aspect,
                         min_luminance=args.min_luminance if args.min_luminance is not None else (85 if theme=="terminal" else 0),
                         alpha_threshold=args.alpha_threshold,saturation=args.saturation,
                         remove_background=args.remove_background or theme=="terminal",
                         background_tolerance=args.background_tolerance)


def cmd_convert(args: argparse.Namespace) -> None:
    theme=_theme(args)
    frame=_frame(args,theme)
    background=args.background or ((247,247,248) if theme=="light" else
                                   (7,17,30) if theme=="terminal" else (4,8,16))
    if args.transparent_background and args.format not in ("png","svg"):
        raise ValueError("--transparent-background requires PNG or SVG format")
    if args.format=="text": content=render_text(frame)
    elif args.format=="ansi":content=render_ansi(frame,background=background)
    elif args.format=="svg":content=render_svg(frame,cell_width=args.cell_width,cell_height=args.cell_height,
                                                  background=None if args.transparent_background else "#%02x%02x%02x" % background)
    elif args.format=="json":content=json.dumps({"columns":frame.columns,"rows":frame.rows,"cells":frame.records()},separators=(",",":"))+"\n"
    else:
        if not args.output:raise ValueError("PNG output requires --output")
        image=render_png(frame,cell_width=args.cell_width,cell_height=args.cell_height,
                         background=None if args.transparent_background else background,font_path=args.font)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        image.save(args.output)
        return
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(content,encoding="utf-8")
    else:
        if args.format=="ansi" and not sys.stdout.isatty():
            print("Warning: ANSI escape codes are going to a pipe/file.",file=sys.stderr)
        sys.stdout.write(content)


def cmd_play(args: argparse.Namespace) -> None:
    if not sys.stdout.isatty():
        sys.stdout.write(render_text(_frame(args)))
        return
    size=shutil.get_terminal_size((80,24))
    args.width=min(args.width,max(1,size.columns-1))
    if args.height is None:args.height=min(max(1,size.lines-2),
        max(1,round(args.width*args.cell_aspect*1.2)))
    frame=_frame(args)
    if args.fps<1 or args.fps>60 or args.duration<=0:
        raise ValueError("fps must be 1..60 and duration must be positive")
    start=time.monotonic()
    sys.stdout.write("\x1b[?1049h\x1b[?25l")
    try:
        while True:
            elapsed=time.monotonic()-start
            if elapsed>=args.duration:break
            reveal=min(1,elapsed/max(.1,args.duration*.72))
            visible=tuple(cell if (x/frame.columns*.6+y/frame.rows*.4)<reveal else None
                         for y in range(frame.rows) for x in range(frame.columns)
                         for cell in (frame.at(x,y),))
            stage=AsciiFrame(frame.columns,frame.rows,visible)
            sys.stdout.write("\x1b[H"+render_ansi(stage)+"\x1b[0m")
            sys.stdout.flush()
            time.sleep(max(0,1/args.fps-(time.monotonic()-start-elapsed)))
        sys.stdout.write("\x1b[H"+render_ansi(frame))
        sys.stdout.flush()
        if args.hold:input("Press Enter to close...")
    finally:
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()


def cmd_inspect(args: argparse.Namespace) -> None:
    with Image.open(args.image) as loaded:
        image=ImageOps.exif_transpose(loaded)
        report=inspect_image(image)
        report.update({"width":image.width,"height":image.height})
    sys.stdout.write(json.dumps(report,indent=2)+"\n")


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(prog="binary-ascii",description="Turn arbitrary images into binary glyphs, terminal motion, and web presentations.")
    commands=parser.add_subparsers(dest="command",required=True)
    convert=commands.add_parser("convert",help="Export text, ANSI, JSON, SVG or PNG")
    _image_options(convert)
    convert.add_argument("--format",choices=["text","ansi","json","svg","png"],default="text")
    convert.add_argument("--output","-o",type=Path)
    convert.add_argument("--background",type=_rgb,help="Background #RRGGBB; default depends on theme")
    convert.add_argument("--transparent-background",action="store_true",help="Output only the glyph subject with PNG/SVG transparency")
    convert.add_argument("--cell-width",type=int,default=8)
    convert.add_argument("--cell-height",type=int,default=12)
    convert.add_argument("--font",type=Path)
    convert.set_defaults(run=cmd_convert)
    play=commands.add_parser("play",help="Reveal colored binary art inside a terminal/TUI")
    _image_options(play)
    play.add_argument("--fps",type=int,default=15)
    play.add_argument("--duration",type=float,default=5)
    play.add_argument("--hold",action="store_true",help="Wait on the final frame")
    play.set_defaults(run=cmd_play)
    inspect=commands.add_parser("inspect",help="Detect background brightness, source transparency and dominant colors")
    inspect.add_argument("image",type=Path)
    inspect.set_defaults(run=cmd_inspect)
    present=commands.add_parser("present",help="Generate an editable cinematic HTML Canvas deck from a manifest")
    present.add_argument("manifest",type=Path)
    present.add_argument("--output","-o",type=Path,required=True)
    present.add_argument("--force",action="store_true",help="Replace generated output files")
    present.set_defaults(run=lambda a:build_presentation(a.manifest,a.output,force=a.force))
    args=parser.parse_args(argv)
    try:args.run(args)
    except (OSError,ValueError) as error:
        parser.exit(2,f"binary-ascii: {error}\n")
    return 0


if __name__=="__main__":raise SystemExit(main())
