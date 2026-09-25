# Gentle AI × Engram — Binary Memory Field

An independent, editable homepage animation concept for Gentleman Programming. The illustration is drawn on a responsive 1920 × 1080 HTML Canvas. The Gentle AI rose and Engram elephant are sampled from their original PNG artwork, then reconstructed as thousands of colored `0` and `1` glyphs. The PNGs serve as **templates only** and are not drawn over the finished art.

The 30-second narrative goes from the agent environment to persistent memory, the connection between both products, and a restored session. An original, upbeat electronic soundtrack is optional and starts only when the visitor presses **♪**.

## Try it locally

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>. There is no build step and no external JavaScript dependency.

Controls: **↺** replay, **Ⅱ / ▶** pause/play, **↣** final scene, **♪** sound. Space pauses and the left/right arrows seek between scenes. Reduced-motion preferences open on the final frame. The Canvas keeps its 16:9 ratio on smaller screens.

## Edit it

| File | Purpose |
| --- | --- |
| `index.html` | Accessible page and controls |
| `style.css` | Layout and responsive presentation |
| `script.js` | Timeline, binary sampling, Canvas animation |
| `assets/rose.png` and `assets/engram-elephant.png` | Pixel templates for the branded glyph drawings |
| `assets/sound.mp3` | Original optional soundtrack |
| `tools/generate_sound.py` | Reproducible source for the soundtrack; requires NumPy and FFmpeg |

For the soundtrack, run `python3 tools/generate_sound.py`, then `ffmpeg -i assets/sound.wav -c:a libmp3lame -b:a 160k assets/sound.mp3`.

This is a community tribute and a proposal for the maintainers, not an official deployment or endorsement. The brand artwork originates with [Gentle AI](https://github.com/Gentleman-Programming/gentle-ai) and [Engram](https://github.com/Gentleman-Programming/engram-landing). Product names and marks belong to their respective owners.
