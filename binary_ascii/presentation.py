"""Compile a validated scene manifest into a standalone interactive presentation."""
from __future__ import annotations

import json
import re
import shutil
from html import escape
from pathlib import Path

from .core import convert_image

HEX=re.compile(r"^#[0-9a-fA-F]{6}$")
LAYOUTS={"left","right","center"}
MOTIONS={"reveal","scan","pulse"}


def _image_path(folder: Path, value: object) -> Path:
    if not isinstance(value,str) or not value or "://" in value:
        raise ValueError("image/audio must be a local file path")
    path=(folder/value).resolve()
    if not path.is_file():raise ValueError(f"source file missing: {path}")
    return path


def build_presentation(manifest_path: str | Path, output: str | Path, *, force: bool=False) -> Path:
    path=Path(manifest_path).resolve()
    raw=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw,dict):raise ValueError("manifest root must be an object")
    scenes=raw.get("scenes")
    if not isinstance(scenes,list) or not 1<=len(scenes)<=30:
        raise ValueError("manifest needs 1..30 scenes")
    title=str(raw.get("title","Binary ASCII Presentation"))[:120]
    subtitle=str(raw.get("subtitle",""))[:180]
    background=str(raw.get("background","#040810"))
    if not HEX.fullmatch(background):raise ValueError("background must be #RRGGBB")
    target=Path(output).resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise ValueError("output directory is not empty; use --force")
    compiled=[];saved=[]
    for i,scene in enumerate(scenes):
        if not isinstance(scene,dict):raise ValueError(f"scene {i+1} must be an object")
        source=_image_path(path.parent,scene.get("image"))
        columns=int(scene.get("columns",105))
        if not 8<=columns<=240:raise ValueError(f"scene {i+1} columns must be 8..240")
        duration=float(scene.get("duration",5))
        if not 1<=duration<=60:raise ValueError(f"scene {i+1} duration must be 1..60 seconds")
        accent=str(scene.get("accent","#ff4b96"))
        if not HEX.fullmatch(accent):raise ValueError(f"scene {i+1} accent must be #RRGGBB")
        layout=str(scene.get("layout","right"))
        motion=str(scene.get("motion","reveal"))
        if layout not in LAYOUTS or motion not in MOTIONS:
            raise ValueError(f"scene {i+1} layout/motion is unsupported")
        frame=convert_image(source,columns=columns,cell_aspect=1,
                            min_luminance=int(scene.get("min_luminance",38)),
                            remove_background=bool(scene.get("remove_background",False)),
                            background_tolerance=int(scene.get("background_tolerance",24)))
        compiled.append({"title":str(scene.get("title",f"Scene {i+1}"))[:100],
                         "eyebrow":str(scene.get("eyebrow",f"{i+1:02d} / BINARY FIELD"))[:90],
                         "caption":str(scene.get("caption",""))[:180],
                         "accent":accent,"layout":layout,"motion":motion,
                         "duration":duration,"columns":frame.columns,"rows":frame.rows,
                         "cells":frame.records()})
        saved.append((source,f"sources/{i+1:02d}-{source.name}"))
    audio=None
    if raw.get("audio") is not None:
        audio=_image_path(path.parent,raw["audio"])
        if audio.suffix.lower() not in {".mp3",".m4a",".ogg",".wav"}:
            raise ValueError("audio must be mp3, m4a, ogg or wav")
    package={"title":title,"subtitle":subtitle,"background":background,"scenes":compiled,
             "audio":f"assets/sound{audio.suffix.lower()}" if audio else None}
    template=(Path(__file__).parent/"templates"/"presentation.html").read_text(encoding="utf-8")
    data=json.dumps(package,ensure_ascii=False,separators=(",",":"))
    # Inert JSON within an HTML script tag, safe even for `</script>` in titles.
    data=data.replace("<","\\u003c").replace(">","\\u003e").replace("&","\\u0026")
    text=template.replace("__TITLE__",escape(title)).replace("__DATA__",data)
    target.mkdir(parents=True,exist_ok=True)
    (target/"index.html").write_text(text,encoding="utf-8")
    (target/"presentation.json").write_text(json.dumps(package,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    sources=target/"sources";sources.mkdir(exist_ok=True)
    editable=dict(raw)
    editable_scenes=[]
    for scene,(source,name) in zip(scenes,saved):
        destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        editable_scenes.append({**scene,"image":name})
    editable["scenes"]=editable_scenes
    if audio:
        dest=target/package["audio"]
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(audio,dest)
        editable["audio"]=package["audio"]
    (target/"manifest.json").write_text(json.dumps(editable,ensure_ascii=False,indent=2),encoding="utf-8")
    return target
