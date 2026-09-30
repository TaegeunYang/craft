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

## Cache busting

`index.html` loads `style.css?v=…` and `main.js?v=…`. Bump the `v` value whenever either file changes so visitors never mix a new page with old CSS/JS.

## Justified text

Body paragraphs are justified on screens 641px and wider, with no hyphenation (hyphenated compounds sit in `<span class="nw">`). Word spacing is tuned for the 1040px desktop column: `--tw` on a `.split.tuned` row sets the text-column width, and `--ls` on a `.ls` paragraph sets a small letter-spacing (at most ±0.15px). After editing a paragraph's text, recheck its word spacing and retune these values.

## Videos

Drop MP4 files (H.264, muted) at these paths; the page picks them up automatically and shows a placeholder until then.

| Where | Path |
|---|---|
| Explorer, Pick-Place | `static/videos/explorer/{model}/pick_place/{cube}_{plate}_{ft,craft}.webm` + `_hevc.mov` + `_poster.webp` |
| Explorer, Pick-Place-Press | `static/videos/explorer/{model}/pick_place_press/{cube}_{plate}_{button}_{ft,craft}.webm` + `_hevc.mov` + `_poster.webp` |
| Instruction change | `static/videos/instruction_change.webm` + `instruction_change_hevc.mov` (transparent; built by `tools/make_instruction_video.py`) |
| Real robot | `static/videos/real/{cube}_{plate}_craft.mp4` (4:3 crop + "x1"; built by `tools/make_real_videos.py`) |

Colors are `red`, `blue`, `green`, `yellow` (Press: `red`, `blue`); `{model}` is `pi05`, `pi0`, or `gr00t`. Explorer videos are built by `tools/make_explorer_videos.py --model <model>`; add the model to `data-video-models` in `index.html` once its videos exist.

## Figures

Figures in `static/images/` are rendered from the paper's figure PDFs (the `Figures/` folder of the paper source):

```bash
python tools/render_figures.py path/to/Figures
```

## TODO

- [x] Co-author names
- [x] Author homepage links
- [x] Paper PDF (`static/paper.pdf`, linked from the Paper button; replace the file when the paper is revised)
- [ ] arXiv link (add a button once announced) and the BibTeX entry (the section shows TBD for now; restore the Copy button with it, see the comment in `index.html`)
- [ ] Code link (Code button)
- [ ] Remove the `<meta name="robots" content="noindex, nofollow">` tag at the public launch
- [ ] Explorer rollout videos (table above); set `--video-ratio` in `static/css/style.css` to match them
