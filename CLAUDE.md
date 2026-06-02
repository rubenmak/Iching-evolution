# I Ching Genetic Evolution Simulator

A generative animation where I Ching symbols evolve through Game of Life-style rules, from Big Bang to Singularity. Runs entirely in the browser as a self-contained HTML file (~900KB).

## Files

- `iching_evolution.py` — simulation engine: cell rules, mutation, phase transitions, epoch config
- `demo_render.py` — generates `index.html` from simulation data; run this after any changes
- `index.html` — the built demo; committed so GitHub Pages serves it directly

## Regenerating

```bash
python demo_render.py   # ~30s, outputs index.html
```

## Architecture

### Cell encoding (integers stored in frame arrays)
| Value | Meaning |
|-------|--------|
| 0 | empty |
| 1 | yin ⚋ |
| 2 | yang ⚊ |
| 3–10 | trigrams ☷☳☵☶☴☲☱☰ |
| 11–74 | hexagrams (64, King Wen via `_BIN_TO_KW`) |
| 75 | strong yin ⚏ |
| 76 | strong yang ⚌ |
| 100 | Big Bang ☯ |

### Epochs
```python
EPOCH_GENS = {9: 35, 0: 20, 1: 20, 2: 25, 3: 30, 4: 20, 5: 18, 6: 25, 7: 22, 8: 50}
```
Epoch 9 = Conway/Before Form (B3/S23 rules). Epochs 0–8 = Void → Singularity.

### Color system
- Yin: green `#3ab84a`, Yang: yellow `#e0c814`
- Earth ☷: deep green, Heaven ☰: celestial gold
- Strong yin/yang invert the pair (strong yin = bright yellow, strong yang = bright green)

### Grid & canvas
- Grid: 48 × 16 cells, each 13 × 17 px → canvas buffer 624 × 272 px
- Chart: 624 × 460 px
- Toroidal wrapping at borders: `(y + dy) % h`
- CSS: `width: 100%` scales to viewport; `max-width: 624px`

### Unicode (important — these were historically swapped)
- `⚊` U+268A = MONOGRAM FOR YANG (solid line) → yang
- `⚋` U+268B = MONOGRAM FOR YIN (broken line) → yin

## GitHub Pages
Live at: **https://rubenmak.github.io/Iching-evolution/**

Enable under repo Settings → Pages → Source: main branch, root folder.
