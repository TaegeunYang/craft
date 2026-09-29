# Same Scene, Different Task — project page

Static project page for *Same Scene, Different Task: Skill Alignment for Compositional Generalization in VLAs* (CRAFT).
Plain HTML/CSS/JS, no build step, no analytics, no third-party requests.

## Preview locally

```bash
python3 -m http.server 8765
```

Then open http://localhost:8765.

## Deploy (GitHub Pages)

1. Create a public repository named `craft` under your account.
2. Push this folder to its `main` branch.
3. Settings → Pages → Source: *Deploy from a branch*, Branch: `main` / `(root)`.
4. The page is served at `https://taegeunyang.github.io/craft/`.

## Videos

Drop MP4 files (H.264, muted) at these paths; the page picks them up automatically and shows a placeholder until then.

| Where | Path |
|---|---|
| Explorer, Pick-Place | `static/videos/explorer/pick_place/{cube}_{plate}_{ft,craft}.mp4` |
| Explorer, Pick-Place-Press | `static/videos/explorer/pick_place_press/{cube}_{plate}_{button}_{ft,craft}.mp4` |
| Instruction change | `static/videos/instruction_change.webm` + `instruction_change_hevc.mov` (transparent; built by `tools/make_instruction_video.py`) |
| Real robot | `static/videos/real/{cube}_{plate}_craft.mp4` |

Colors are `red`, `blue`, `green`, `yellow` (Press: `red`, `blue`).

## Figures

Figures in `static/images/` are rendered from the paper's figure PDFs (the `Figures/` folder of the paper source):

```bash
python tools/render_figures.py path/to/Figures
```

## TODO

- [x] Co-author names
- [ ] Author homepage links (`index.html` hero)
- [ ] arXiv link and ID (Paper button, BibTeX)
- [ ] Code link (Code button)
- [ ] Remove the `<meta name="robots" content="noindex, nofollow">` tag at the public launch
- [ ] Rollout videos (table above); set `--video-ratio` in `static/css/style.css` to match them
