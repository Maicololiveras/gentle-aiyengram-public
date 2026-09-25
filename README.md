# Gentle AI × Engram — Binary Memory Field

An independent, editable homepage animation concept for Gentleman Programming. The illustration is drawn on a responsive 1920 × 1080 HTML Canvas. The Gentle AI rose and Engram elephant are sampled from their original PNG artwork, then reconstructed as thousands of colored `0` and `1` glyphs. The PNGs serve as **templates only** and are not drawn over the finished art.

The 30-second narrative goes from the agent environment to persistent memory, the connection between both products, and a restored session. The current soundtrack is a 30-second edit of **“First Session”**, supplied by Maicol for this animation. Sound starts only when the visitor presses **♪**.

## Try it locally

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>. There is no build step and no external JavaScript dependency.

## Publish with GitHub Pages

For the first deployment, open this repository's **Settings → Pages** and set **Build and deployment → Source** to **GitHub Actions**. The included `Publish Canvas preview` workflow deploys on subsequent pushes to `main`; rerun its initial failed job (or dispatch the workflow manually) after enabling Pages. This initial repository setting cannot be activated by the workflow's standard `GITHUB_TOKEN`.

Controls: **↺** replay, **Ⅱ / ▶** pause/play, **↣** final scene, **♪** sound. Space pauses and the left/right arrows seek between scenes. Reduced-motion preferences open on the final frame. The Canvas keeps its 16:9 ratio on smaller screens.

## Edit it

| File | Purpose |
| --- | --- |
| `index.html` | Accessible page and controls |
| `style.css` | Layout and responsive presentation |
| `script.js` | Timeline, binary sampling, Canvas animation |
| `assets/rose.png` and `assets/engram-elephant.png` | Pixel templates for the branded glyph drawings |
| `assets/sound.mp3` | Thirty-second excerpt of “First Session,” with a short closing fade |
| `tools/generate_sound.py` | Optional generator for the earlier electronic demo soundtrack; requires NumPy and FFmpeg |

To swap in a different song, create a 30-second MP3 with a closing fade and replace `assets/sound.mp3`. The original full-length “First Session” file is not included in this repository.

This is a community tribute and a proposal for the maintainers, not an official deployment or endorsement. The brand artwork originates with [Gentle AI](https://github.com/Gentleman-Programming/gentle-ai) and [Engram](https://github.com/Gentleman-Programming/engram-landing). Product names and marks belong to their respective owners.
