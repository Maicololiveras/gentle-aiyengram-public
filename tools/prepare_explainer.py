"""Build the editable ASCII deck, offline narration and timing metadata."""
from __future__ import annotations

import json
import sys
import subprocess
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from binary_ascii.presentation import build_presentation


def timestamp(seconds: float) -> str:
    total = round(seconds * 1000)
    return f"{total//3600000:02d}:{total//60000%60:02d}:{total//1000%60:02d},{total%1000:03d}"


def main() -> None:
    source = ROOT / "examples/gentleman-explainer/storyboard.json"
    output = ROOT / "examples/gentleman-explainer/generated"
    work = ROOT / "examples/gentleman-explainer/audio"
    work.mkdir(parents=True, exist_ok=True)
    deck = json.loads(source.read_text(encoding="utf-8"))
    frames: list[tuple[float, bytes]] = []
    for index, scene in enumerate(deck["scenes"]):
        wav = work / f"{index+1:02d}-voice.wav"
        subprocess.run([sys.executable, str(ROOT / "tools/synthesize_spanish.py"), scene["narration"], str(wav)], check=True, stdout=subprocess.DEVNULL)
        with wave.open(str(wav), "rb") as file:
            assert file.getframerate() == 22050 and file.getnchannels() == 1
            length = file.getnframes() / file.getframerate()
            frames.append((length, file.readframes(file.getnframes())))
        scene["duration"] = round(max(8.0, length + 2.0), 3)
        print(f"{index+1:02d} {length:.2f}s → {scene['duration']:.2f}s")
    with wave.open(str(work / "narration.wav"), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(22050)
        for scene, (_, pcm) in zip(deck["scenes"], frames):
            audio.writeframes(b"\0" * (int(.55 * 22050) * 2))
            audio.writeframes(pcm)
            silence = max(0, scene["duration"] - .55 - len(pcm) / 44100)
            audio.writeframes(b"\0" * (round(silence * 22050) * 2))
    deck["audio"] = "../../assets/sound.mp3"
    timed = source.with_name("timed-storyboard.json")
    timed.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    build_presentation(timed, output, force=True)
    start = 0.0
    srt = []
    for index, scene in enumerate(deck["scenes"]):
        end = start + scene["duration"]
        srt.append(f"{index+1}\n{timestamp(start+.4)} --> {timestamp(end-.55)}\n{scene['narration']}\n")
        start = end
    (work / "subtitulos.srt").write_text("\n".join(srt), encoding="utf-8")
    (work / "timing.json").write_text(json.dumps({"duration":start,"scenes":[s["duration"] for s in deck["scenes"]]},indent=2),encoding="utf-8")
    print(f"TOTAL {start:.2f}s")


if __name__ == "__main__":
    main()
