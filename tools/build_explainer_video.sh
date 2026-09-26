#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
base=examples/gentleman-explainer

python tools/prepare_explainer.py
python tools/render_explainer.py
duration=$(python -c 'import json;print(json.load(open("examples/gentleman-explainer/audio/timing.json"))["duration"])')

ffmpeg -y -hide_banner -loglevel error -stream_loop -1 -i assets/sound.mp3 \
  -i "$base/audio/narration.wav" \
  -filter_complex '[0:a]volume=0.08,lowpass=f=8500[bg];[1:a]volume=1.35,highpass=f=75[voice];[bg][voice]amix=inputs=2:duration=shortest:dropout_transition=0,alimiter=limit=0.93[a]' \
  -map '[a]' -t "$duration" -c:a aac -b:a 160k "$base/audio/mix.m4a"

python - <<'PY'
import json
from pathlib import Path
p=Path('examples/gentleman-explainer/timed-storyboard.json')
data=json.loads(p.read_text(encoding='utf-8'))
data['audio']='audio/mix.m4a'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
PY
python -m binary_ascii present "$base/timed-storyboard.json" -o "$base/generated" --force
rm -f "$base/generated/assets/sound.mp3"

ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$base/video/frames.txt" \
  -i "$base/audio/mix.m4a" \
  -vf "fps=15,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf:text='01001101  10110110  00101101  11001010':x='w-mod(t*90\,w+text_w)':y=642:fontsize=15:fontcolor=0x76a9c8@0.45" \
  -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -c:a copy -t "$duration" \
  -movflags +faststart "$base/video/gentleman-ecosistema-narrado.mp4"

ffmpeg -y -hide_banner -loglevel error -i "$base/video/gentleman-ecosistema-narrado.mp4" \
  -i "$base/audio/subtitulos.srt" -map 0:v -map 0:a -map 1:s \
  -c:v copy -c:a copy -c:s mov_text -metadata:s:s:0 language=spa \
  -disposition:s:0 default -movflags +faststart \
  "$base/Gentleman-ecosistema-ODD-Engram-Gentle-Shell.mp4"
