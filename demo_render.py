#!/usr/bin/env python3
"""
Generate a self-contained animated HTML demo of the I Ching Evolution Simulator.
Canvas rendering, per-cell type colours, live bar chart.
"""

import sys, os, json, random, math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iching_evolution import (
    Grid, EPOCHS, EMPTY, YIN, YANG, TRIG_BASE, HEX_BASE,
    is_line, is_trigram, is_hexagram, trig_idx, hex_idx,
    cell_char, cell_color,
    YIN_COLOR, YANG_COLOR, STRONG_YIN_COLOR, STRONG_YANG_COLOR,
    TRIG_COLORS, HEX_COLORS, HEX_BG_COLORS,
    STRONG_YIN, STRONG_YANG,
    TRIG_CHARS, TRIGRAMS_META, HEXAGRAMS, _BIN_TO_KW,
)

GRID_W = 48
GRID_H = 16
SEED = 113

# Gens per epoch (keyed by epoch id).
# Research showed: early epochs saturate in 5-10 gens; singularity collapses
# hex diversity fast — 50 gens shows the full cascade dramatically.
# Epoch 9 = Conway / Before Form: 35 gens of S23 line dynamics before chemistry.
EPOCH_GENS = {9: 35, 0: 20, 1: 20, 2: 25, 3: 30, 4: 20, 5: 18, 6: 25, 7: 22, 8: 50}

BB_SYMBOL      = 100        # ☯ — only used in Big Bang frame 0
BB_FRAMES      = 13         # total animation frames for the Big Bang epoch
BB_HOLD_FRAMES = 4          # frames showing ☯ alone before expansion (4 × 350ms = 1.4s)
BB_VOID_PROB   = 0.30       # 30 % of space between heaven/earth is void

# Cell canvas dimensions
CW, CH = 13, 17
GRID_PX_W = GRID_W * CW    # 624
GRID_PX_H = GRID_H * CH    # 272
CHART_H   = 460



# ── Big Bang scripted animation ───────────────────────────────────────────────

def generate_big_bang():
    """
    Circular expansion: the universe grows as a ring outward from ☯ at the centre.
    Top arc of the ring = Heaven (☰), bottom arc = Earth (☷).
    Interior fills with yin/yang lines using a vertical gradient:
    yang at top (y=0), yin at bottom (y=GRID_H-1).
    """
    HEAVEN = TRIG_BASE + 7   # ☰ all-yang trigram
    EARTH  = TRIG_BASE + 0   # ☷ all-yin  trigram
    cy     = GRID_H // 2
    cx     = GRID_W // 2

    # Pixel-space geometry for a visually circular ring
    cx_px  = cx * CW
    cy_px  = cy * CH
    ring_w = CW * 2.0   # ring thickness in pixels (≈ 2 cell widths)

    # Radius that just clears the farthest cell centre from the grid centre
    max_r = max(
        math.sqrt(((x + 0.5) * CW - cx_px) ** 2 + ((y + 0.5) * CH - cy_px) ** 2)
        for x in range(GRID_W) for y in range(GRID_H)
    ) + ring_w

    expand_frames = BB_FRAMES - BB_HOLD_FRAMES   # frames dedicated to ring expansion

    random.seed(SEED)
    frames = []

    for fi in range(BB_FRAMES):
        cells = [EMPTY] * (GRID_W * GRID_H)

        if fi < BB_HOLD_FRAMES:
            # Hold on the primordial ☯ symbol
            cells[cy * GRID_W + cx] = BB_SYMBOL
        else:
            expand_fi = fi - BB_HOLD_FRAMES + 1   # 1 … expand_frames
            ring_r = (expand_fi / expand_frames) * max_r

            for y in range(GRID_H):
                for x in range(GRID_W):
                    px = (x + 0.5) * CW
                    py = (y + 0.5) * CH
                    dist = math.sqrt((px - cx_px) ** 2 + (py - cy_px) ** 2)

                    if dist > ring_r + ring_w / 2:
                        # Outside the expanding universe — remain void
                        continue
                    elif dist >= ring_r - ring_w / 2:
                        # On the ring boundary: Heaven arcs above, Earth below
                        cells[y * GRID_W + x] = HEAVEN if y < cy else EARTH
                    else:
                        # Inside the universe: yin/yang gradient (yang↑ yin↓, matching Heaven top/Earth bottom)
                        if random.random() < BB_VOID_PROB:
                            continue
                        yang_prob = 1.0 - y / (GRID_H - 1)
                        cells[y * GRID_W + x] = YANG if random.random() < yang_prob else YIN

        yin  = cells.count(YIN)
        yang = cells.count(YANG)
        tc   = [0] * 8
        hc   = [0] * 64
        tc[7] = cells.count(HEAVEN)
        tc[0] = cells.count(EARTH)

        frames.append({
            "cells":   cells,
            "yin": yin, "yang": yang, "syin": 0, "syang": 0,
            "tc": tc, "hc": hc, "top_hex": None,
        })

    return frames


# ── Conway + I Ching simulation ───────────────────────────────────────────────

def capture_frames(g, phase, gens, conway_lines=False):
    frames = []
    for _ in range(gens):
        g.step(phase, conway_lines=conway_lines)
        yin, yang, syin, syang, tc, hc = g.counts()
        top_hex = max(range(64), key=lambda i: hc[i]) if sum(hc) > 0 else None
        # Flat indices of cells that mutated this gen (phases 5-6 only)
        changed = sorted(y * GRID_W + x for y, x in g.last_changed) if phase >= 5 else []
        frames.append({
            "cells":   [g.cells[y][x] for y in range(GRID_H) for x in range(GRID_W)],
            "yin": yin, "yang": yang, "syin": syin, "syang": syang,
            "tc": tc, "hc": hc, "top_hex": top_hex, "changed": changed,
        })
    return frames


# ── Build ─────────────────────────────────────────────────────────────────────

def build():
    all_epochs = []

    # ── Big Bang (scripted) ────────────────────────────────────────────────
    print("  epoch BB: THE BIG BANG...", flush=True)
    bb_frames = generate_big_bang()
    all_epochs.append({
        "id":      -1,
        "phase":   -1,
        "bigbang": True,
        "name":    "大爆炸",
        "title":   "THE BIG BANG",
        "sub":     "Tài Chū · The Great Beginning",
        "desc":    (
            f"☯ separates into Heaven (☰) ascending and Earth (☷) descending. "
            f"Between them the universe forms: {int((1-BB_VOID_PROB)*100)} % matter. "
            f"Pure ⧊ yin at the top, pure ⧋ yang at the bottom."
        ),
        "frames": bb_frames,
    })

    # ── Seed the Void grid from the last Big Bang frame ────────────────────
    last_bb = bb_frames[-1]["cells"]
    HEAVEN  = TRIG_BASE + 7
    EARTH   = TRIG_BASE + 0

    random.seed(SEED + 1)    # independent seed for the simulation proper
    g = Grid(GRID_W, GRID_H)
    for i, cv in enumerate(last_bb):
        y, x = i // GRID_W, i % GRID_W
        # Carry yin/yang lines and Heaven/Earth trigrams; drop BB_SYMBOL
        if cv not in (BB_SYMBOL, EMPTY):
            g.cells[y][x] = cv

    # ── Regular epochs (continuous simulation) ─────────────────────────────
    for ep in EPOCHS:
        print(f"  epoch {ep['id']}: {ep['title']} (phase {ep['phase']})...", flush=True)
        phase = ep["phase"]
        gens  = EPOCH_GENS[ep["id"]]

        # If the grid is completely empty (e.g. after the Big Bang void collapse),
        # re-seed with the epoch's init density — a new big bang from the void.
        occupied = sum(1 for row in g.cells for c in row if c != EMPTY)
        if occupied == 0:
            print(f"    → grid empty, re-seeding ({ep['init_yin']*100:.0f}%/{ep['init_yang']*100:.0f}%)", flush=True)
            g.seed(ep["init_yin"], ep["init_yang"])

        # Frame 0 = carry-over state (0 extra gens); then 1 gen per frame.
        yin, yang, syin, syang, tc, hc = g.counts()
        seed_frame = {
            "cells":   [g.cells[y][x] for y in range(GRID_H) for x in range(GRID_W)],
            "yin": yin, "yang": yang, "syin": syin, "syang": syang,
            "tc": tc, "hc": hc, "top_hex": None, "changed": [],
        }
        frames = [seed_frame] + capture_frames(g, phase, gens, conway_lines=ep.get("conway", False))

        all_epochs.append({
            "id":      ep["id"],
            "phase":   ep["phase"],
            "bigbang": False,
            "name":    ep["name"],
            "title":   ep["title"],
            "sub":     ep["subtitle"],
            "desc":    ep["desc"],
            "frames":  frames,
        })

    # ── Serialise ──────────────────────────────────────────────────────────
    palette = {
        "yin":    YIN_COLOR,
        "yang":   YANG_COLOR,
        "syin":   STRONG_YIN_COLOR,
        "syang":  STRONG_YANG_COLOR,
        "trigs":  TRIG_COLORS,
        "hexes":  HEX_COLORS,
        "hexbgs": HEX_BG_COLORS,
        "dim":    "#181428",
        "bg":     "#070710",
        "bb":     "#e8e0ff",
    }
    trig_meta = [{"sym": t[0], "name": t[1], "el": t[2]} for t in TRIGRAMS_META]
    hex_meta  = [
        {"pin": HEXAGRAMS[_BIN_TO_KW[i]+1][1], "name": HEXAGRAMS[_BIN_TO_KW[i]+1][2]}
        for i in range(64)
    ]

    # safe() for JS object literals; safe_str() for JSON.parse('...') string embedding
    safe     = lambda s: s.replace("</", "<\\/")
    def safe_str(s):
        s = s.replace("\\", "\\\\")   # must be first
        s = s.replace("'", "\\'")
        s = s.replace("</", "<\\/")
        return s
    jdata    = safe_str(json.dumps(all_epochs, ensure_ascii=False))
    jpal     = safe(json.dumps(palette,    ensure_ascii=False))
    jtmeta   = safe(json.dumps(trig_meta,  ensure_ascii=False))
    jhmeta   = safe(json.dumps(hex_meta,   ensure_ascii=False))

    # Delays per epoch (BB + 10 regular = 11 values), ms per frame at 1× speed.
    # Singularity is faster to sell the cascade energy (50 frames × 45ms = 2.25s).
    delays = json.dumps([350, 80, 65, 65, 65, 65, 65, 65, 65, 65, 45])

    html = TEMPLATE
    for k, v in [
        ("__DATA__",   jdata),
        ("__PAL__",    jpal),
        ("__TMETA__",  jtmeta),
        ("__HMETA__",  jhmeta),
        ("__DELAYS__", delays),
        ("__GW__",     str(GRID_W)),
        ("__GH__",     str(GRID_H)),
        ("__CW__",     str(CW)),
        ("__CH__",     str(CH)),
        ("__GPW__",    str(GRID_PX_W)),
        ("__GPH__",    str(GRID_PX_H)),
        ("__CHTH__",   str(CHART_H)),
    ]:
        html = html.replace(k, v)
    return html


# ── HTML template ─────────────────────────────────────────────────────────────

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>I Ching Genetic Evolution · Big Bang to Singularity 🫛</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #070710; color: #b0a0d0;
  font-family: 'Courier New', Courier, monospace;
  display: flex; flex-direction: column; align-items: center;
  padding: 10px 6px 24px; min-height: 100vh;
}
h1 { font-size: .92em; color: #9070e0; letter-spacing: .2em; text-align: center; margin-bottom: 1px; }
h2 { font-size: .58em; color: #281e40; letter-spacing: .14em; text-align: center; margin-bottom: 8px; }
#sim { width: 100%; max-width: __GPW__px; border: 1px solid #201830; border-radius: 6px; overflow: hidden; }
#cgrid  { display: block; width: 100%; }
#cchart { display: block; width: 100%; }
#hdr { padding: 7px 10px 5px; border-bottom: 1px solid #180e28; transition: background .5s; }
.hr { height: 20px; display: flex; align-items: center; overflow: hidden;
      white-space: nowrap; font-size: .7em; gap: 6px; }
#ep-row { height: 22px; font-size: .84em; font-weight: 700; letter-spacing: .08em; }
#ep-desc { height: 28px; font-size: .6em; color: #302048; font-style: italic;
           line-height: 1.35; overflow: hidden; margin: 2px 0; white-space: normal; }
#pbar-wrap { height: 2px; background: #100818; }
#pbar { height: 100%; width: 0; transition: width .18s linear; }
#legend { padding: 4px 8px 3px; border-top: 1px solid #100818;
          font-size: .58em; color: #302048; display: flex; gap: 10px;
          flex-wrap: wrap; align-items: center; }
.litem { display: flex; align-items: center; gap: 3px; }
#ctrls { margin: 8px 0; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.ctrl-row { display: flex; gap: 6px; align-items: center; }
.spd-label { font-size: .6em; color: #403050; letter-spacing: .08em; }
button { background: #0c0a1a; border: 1px solid #281e40; color: #5040a0;
         padding: 5px 14px; border-radius: 4px; font-family: inherit;
         font-size: .72em; cursor: pointer; letter-spacing: .06em; }
button:hover { background: #181030; color: #9070e0; }
button.active { background: #1a1040; border-color: #6050b0; color: #c090ff; }
button.sm { padding: 5px 9px; }
button.tog { opacity: 1; transition: opacity .15s; }
button.tog:not(.active) { opacity: 0.22; }
#foot { font-size: .57em; color: #1e1430; text-align: center; line-height: 1.7; margin-top: 2px; }
</style>
</head>
<body>
<h1>I CHING GENETIC EVOLUTION SIMULATOR</h1>
<h2>Big Bang &rarr; Void &rarr; Chemistry &rarr; Life &rarr; Evolution &rarr; Intelligence &rarr; Civilisation &rarr; Singularity &nbsp;🫛</h2>

<div id="sim">
  <div id="hdr">
    <div class="hr" id="ep-row">
      <span id="ep-name" style="color:#9070e0"></span>
      <span id="ep-sub"  style="color:#302048;font-size:.78em;font-weight:400"></span>
    </div>
    <div id="ep-desc"></div>
    <div class="hr">
      <span id="phase-tag" style="font-size:.8em;padding:1px 5px;border-radius:3px;color:#080810"></span>
      <span id="dom-cell"  style="font-size:1.3em;line-height:1"></span>
      <span id="dom-label" style="color:#302048;font-style:italic;font-size:.82em"></span>
      <span style="flex:1"></span>
      <span id="pop-yin"   style="color:#3ab84a;font-size:.9em"></span>
      <span id="pop-yang"  style="color:#e0c814;font-size:.9em"></span>
      <span id="pop-syin"  style="color:#ffef40;font-size:.9em"></span>
      <span id="pop-syang" style="color:#40ff88;font-size:.9em"></span>
      <span id="pop-tr"    style="color:#40c898;font-size:.9em"></span>
      <span id="pop-hx"    style="color:#8080e0;font-size:.9em"></span>
    </div>
    <div class="hr">
      <span id="gen-label" style="color:#302048;font-size:.82em"></span>
    </div>
  </div>
  <div id="pbar-wrap"><div id="pbar"></div></div>
  <canvas id="cgrid"  width="__GPW__" height="__GPH__"></canvas>
  <canvas id="cchart" width="__GPW__" height="__CHTH__"></canvas>
  <div id="legend">
    <div class="litem"><span style="color:#e8e0ff">☯</span> origin</div>
    <div class="litem"><span style="color:#3ab84a">⚋</span> yin</div>
    <div class="litem"><span style="color:#e0c814">⚊</span> yang</div>
    <div class="litem"><span style="color:#ffef40">⚏</span> old yin</div>
    <div class="litem"><span style="color:#40ff88">⚌</span> old yang</div>
    <div class="litem" id="trig-legend"></div>
  </div>
</div>

<div id="ctrls">
  <div class="ctrl-row">
    <button onclick="goEpoch(-1)" title="previous epoch">&#9198; epoch</button>
    <button class="sm" onclick="stepFrame(-1)" title="previous frame">&#9664;</button>
    <button id="pbtn" onclick="togglePlay()">&#9646;&#9646; pause</button>
    <button class="sm" onclick="stepFrame(1)"  title="next frame">&#9654;</button>
    <button onclick="goEpoch(1)"  title="next epoch">epoch &#9197;</button>
  </div>
  <div class="ctrl-row">
    <span class="spd-label">speed</span>
    <button class="sm spd" onclick="setSpeed(0.25, this)">&#188;&times;</button>
    <button class="sm spd" onclick="setSpeed(0.5, this)">&#189;&times;</button>
    <button class="sm spd active" onclick="setSpeed(1, this)">1&times;</button>
    <button class="sm spd" onclick="setSpeed(2, this)">2&times;</button>
  </div>
  <div class="ctrl-row">
    <span class="spd-label">show</span>
    <button class="tog active" onclick="toggleLayer('lines',this)">lines</button>
    <button class="tog active" onclick="toggleLayer('trigs',this)">trigrams</button>
    <button class="tog active" onclick="toggleLayer('hexs',this)">hexagrams</button>
  </div>
</div>

<div id="foot">
  Big Bang: Heaven (&#9776;) ascends &middot; Earth (&#9775;) descends &middot; universe forms between them (70&thinsp;% matter, yang at top, yin at bottom)<br>
  Before Form: Conway B3S23 &mdash; lines born into three neighbours, surviving with two or three &middot; Still-lifes and wandering clusters before chemistry begins<br>
  Trigrams form from north/south neighbours (60&thinsp;% chance) &middot; Hexagrams pair adjacent trigrams in one tick &middot; Heaven/Earth gradient (40&thinsp;%) shapes polarity of new lines
</div>

<script>
const D      = JSON.parse('__DATA__');
const PAL    = __PAL__;
const TMETA  = __TMETA__;
const HMETA  = __HMETA__;
const DELAYS = __DELAYS__;
const GW = __GW__, GH = __GH__, CW = __CW__, CH = __CH__;
const GPW = __GPW__, CHTH = __CHTH__;

const TRIG_SYMS  = TMETA.map(t => t.sym);
const YIN_CHAR   = '⚋';
const YANG_CHAR  = '⚊';
const _BIN_TO_KW = [1,23,6,14,45,35,18,10,15,50,39,61,31,54,53,33,7,2,28,38,47,62,59,4,22,26,3,51,17,21,40,25,19,41,58,52,56,36,60,8,34,20,63,55,49,29,37,13,44,16,46,30,27,48,57,42,11,24,5,32,43,12,9,0];
const HEX_CHARS  = _BIN_TO_KW.map(kw => String.fromCodePoint(0x4DC0 + kw));
const HEX_BASE   = 11;
const TRIG_BASE  = 3;
const BB_SYM     = 100;

const cgrid  = document.getElementById('cgrid');
const cchart = document.getElementById('cchart');
const gctx   = cgrid.getContext('2d');
const bctx   = cchart.getContext('2d');


let ei=0, fi=0, tg=0, playing=true;
const layers = { lines: true, trigs: true, hexs: true };
function toggleLayer(name, btn) {
  layers[name] = !layers[name];
  btn.classList.toggle('active', layers[name]);
  render();
}
function layerAlpha(c) {
  const STRONG_YIN = 75, STRONG_YANG = 76;
  if ((c >= 1 && c <= 2 || c === STRONG_YIN || c === STRONG_YANG) && !layers.lines) return 0.08;
  if (c >= TRIG_BASE && c < HEX_BASE && !layers.trigs) return 0.08;
  if (c >= HEX_BASE && c < 75 && !layers.hexs) return 0.08;
  return 1.0;
}

const STRONG_YIN = 75, STRONG_YANG = 76;

// ── Cell helpers ──────────────────────────────────────────────────
function cellChar(c) {
  if (c === 0)          return ' ';
  if (c === BB_SYM)     return '☯';
  if (c === 1)          return YIN_CHAR;
  if (c === 2)          return YANG_CHAR;
  if (c === STRONG_YIN)  return '⚏';
  if (c === STRONG_YANG) return '⚌';
  if (c >= TRIG_BASE && c <= TRIG_BASE+7) return TRIG_SYMS[c-TRIG_BASE];
  if (c >= HEX_BASE && c < 75)  return HEX_CHARS[(c-HEX_BASE) % 64];
  return '?';
}
function cellColor(c) {
  if (c === 0)          return PAL.dim;
  if (c === BB_SYM)     return PAL.bb;
  if (c === 1)          return PAL.yin;
  if (c === 2)          return PAL.yang;
  if (c === STRONG_YIN)  return PAL.syin;
  if (c === STRONG_YANG) return PAL.syang;
  if (c >= TRIG_BASE && c <= TRIG_BASE+7) return PAL.trigs[c-TRIG_BASE];
  if (c >= HEX_BASE && c < 75)  return PAL.hexes[(c-HEX_BASE) % 64];
  return PAL.dim;
}
function cellFont(c, base) {
  if (c === BB_SYM)   return `bold ${base+3}px serif`;
  if (c >= HEX_BASE)  return `bold ${base+2}px monospace`;  // larger than trigrams to stand out
  if (c >= TRIG_BASE) return `${base}px monospace`;
  return `bold ${base+1}px monospace`;
}

// ── Grid renderer (canvas) ────────────────────────────────────────
function drawGrid(fr) {
  gctx.fillStyle = PAL.bg;
  gctx.fillRect(0, 0, GPW, GH*CH);
  gctx.textAlign    = 'center';
  gctx.textBaseline = 'middle';
  const changedSet = new Set(fr.changed || []);
  for (let i = 0; i < fr.cells.length; i++) {
    const c = fr.cells[i];
    if (c === 0) continue;
    const x = i % GW, y = Math.floor(i / GW);
    const alpha = layerAlpha(c);
    gctx.globalAlpha = alpha;
    // Hexagrams get a tinted background matching their trigram blend
    if (c >= HEX_BASE && c < 75) {
      gctx.fillStyle = PAL.hexbgs[(c - HEX_BASE) % 64];
      gctx.fillRect(x*CW + 1, y*CH + 1, CW - 2, CH - 2);
    }
    gctx.fillStyle = cellColor(c);
    gctx.font      = cellFont(c, 13);
    gctx.fillText(cellChar(c), x*CW + CW/2, y*CH + CH/2);
    gctx.globalAlpha = 1.0;
    // Mutation ripple flash: bright ring on cells that just mutated (phases 5-6)
    if (changedSet.has(i)) {
      gctx.strokeStyle = '#a0ffee';
      gctx.globalAlpha = 0.82;
      gctx.lineWidth = 1.5;
      gctx.strokeRect(x*CW + 0.5, y*CH + 0.5, CW - 1, CH - 1);
      gctx.globalAlpha = 1.0;
    }
  }
}

// ── Bar chart renderer (horizontal, sorted by count) ─────────────
function drawChart(fr) {
  const W = GPW, H = CHTH;
  const ROW_H = 15, HDR_H = 13, GAP = 4;
  const BAR_X = 140, BAR_W = W - BAR_X - 50, CNT_X = W - 3;

  bctx.fillStyle = '#050510';
  bctx.fillRect(0, 0, W, H);

  let oy = 4;

  function drawSection(label, entries, secMax) {
    if (entries.length === 0) return;
    // Section header line
    bctx.fillStyle = '#281e40';
    bctx.font = '8px monospace';
    bctx.textAlign = 'left';
    bctx.fillText(label, 3, oy + HDR_H - 3);
    bctx.fillStyle = '#140e28';
    bctx.fillRect(3 + label.length * 5.5, oy + HDR_H - 6, W - label.length * 5.5 - 6, 1);
    oy += HDR_H;

    for (const e of entries) {
      // Symbol
      bctx.fillStyle = e.color;
      bctx.font = (e.isHex ? '10px' : '12px') + ' monospace';
      bctx.textAlign = 'left';
      bctx.fillText(e.sym, 3, oy + ROW_H - 3);

      // Name label
      bctx.fillStyle = '#544468';
      bctx.font = '9px monospace';
      bctx.textAlign = 'left';
      bctx.fillText(e.label.substring(0, 18), 18, oy + ROW_H - 3);

      // Bar (normalised to section max)
      const bw = secMax > 0 ? Math.max(1, Math.round((e.count / secMax) * BAR_W)) : 0;
      bctx.fillStyle = e.color;
      bctx.globalAlpha = 0.72;
      bctx.fillRect(BAR_X, oy + 2, bw, ROW_H - 5);
      bctx.globalAlpha = 1.0;

      // Count number
      bctx.fillStyle = '#706080';
      bctx.font = '9px monospace';
      bctx.textAlign = 'right';
      bctx.fillText(String(e.count), CNT_X, oy + ROW_H - 3);

      oy += ROW_H;
    }
    oy += GAP;
  }

  // Lines — all four types, most frequent on top
  const lEntries = [
    {sym: YIN_CHAR,  label: 'Yin · 陰',          count: fr.yin,   color: PAL.yin,   isHex: false},
    {sym: YANG_CHAR, label: 'Yang · 陽',          count: fr.yang,  color: PAL.yang,  isHex: false},
    {sym: '⚏',       label: 'Old Yin · 太陰',     count: fr.syin,  color: PAL.syin,  isHex: false},
    {sym: '⚌',       label: 'Old Yang · 太陽',    count: fr.syang, color: PAL.syang, isHex: false},
  ].sort((a, b) => b.count - a.count);
  drawSection('lines', lEntries, Math.max(fr.yin, fr.yang, fr.syin || 0, fr.syang || 0, 1));

  // Trigrams — non-zero only, sorted desc
  const tEntries = TMETA.map((t, i) => ({
    sym:   t.sym,
    label: t.el + ' · ' + t.name,
    count: fr.tc[i], color: PAL.trigs[i], isHex: false,
  })).filter(e => e.count > 0).sort((a, b) => b.count - a.count);
  if (tEntries.length > 0)
    drawSection('trigrams', tEntries, Math.max(...tEntries.map(e => e.count), 1));

  // Hexagrams — top 15 by count, non-zero, sorted desc
  const hEntries = fr.hc.map((count, i) => ({
    sym:   HEX_CHARS[i],
    label: HMETA[i] ? (HMETA[i].pin + ' · ' + HMETA[i].name) : ('hex ' + (i + 1)),
    count, color: PAL.hexes[i], isHex: true,
  })).filter(e => e.count > 0).sort((a, b) => b.count - a.count).slice(0, 15);
  if (hEntries.length > 0)
    drawSection('hexagrams', hEntries, Math.max(...hEntries.map(e => e.count), 1));
}

// ── Phase labels ──────────────────────────────────────────────────
// Index = phase + 1  (so phase -1 → index 0, phase 0 → 1, … phase 6 → 7)
const PHASE_LABELS = [
  'pre-formation',       // -1 (BB)
  'yin · yang',          // 0
  'trigrams emerge',     // 1
  'hexagrams emerge',    // 2 hunter-gatherer
  'cultivation',         // 3 agricultural
  'industrial progress', // 4
  'digital flux',        // 5
  'singularity cascade', // 6
];
const PHASE_COLORS = [
  '#20083a', '#281860', '#184828', '#281048',
  '#1a2808', '#280e06', '#041828', '#180428',
];

// Per-epoch header background  (index = ei = position in D array, 0=BB)
const BG_COLORS = [
  '#04020c',  // Big Bang
  '#0a0418',  // Before Form (Conway)
  '#060610',  // Void
  '#04090e',  // Chemistry
  '#050f06',  // Life
  '#040b02',  // Evolution
  '#020a0e',  // Intelligence Awakens
  '#0a0a02',  // Agricultural Civilisation
  '#0e0a02',  // Industrial Civilisation
  '#021428',  // Digital Civilisation
  '#0a0214',  // Singularity
];
const PBAR_COLORS = [
  '#8030c0',  // Big Bang
  '#8020c8',  // Before Form (Conway)
  '#5050a0',  // Void
  '#2060a0',  // Chemistry
  '#208060',  // Life
  '#60a020',  // Evolution
  '#20a0a0',  // Intelligence Awakens
  '#a0a020',  // Agricultural Civilisation
  '#c0a020',  // Industrial Civilisation
  '#2060c0',  // Digital Civilisation
  '#a020e0',  // Singularity
];

// ── Header renderer ───────────────────────────────────────────────
function render() {
  const ep = D[ei], fr = ep.frames[fi];

  // Epoch identity
  document.getElementById('ep-name').textContent = ep.name + '  ' + ep.title;
  document.getElementById('ep-name').style.color = ep.bigbang ? PAL.bb : PBAR_COLORS[ei];
  document.getElementById('ep-sub').textContent  = ep.sub;
  document.getElementById('ep-desc').textContent = ep.desc;
  document.getElementById('hdr').style.background = BG_COLORS[ei] || '#060610';

  // Phase tag
  const phaseIdx = ep.bigbang ? 0 : Math.min(ep.phase + 1, PHASE_LABELS.length - 1);
  const pt = document.getElementById('phase-tag');
  pt.textContent = (ep.bigbang ? 'big bang' : 'phase ' + ep.phase)
                   + ': ' + PHASE_LABELS[phaseIdx];
  pt.style.background = PHASE_COLORS[phaseIdx];

  // Dominant entity display
  const domEl = document.getElementById('dom-cell');
  const domLb = document.getElementById('dom-label');
  if (ep.bigbang) {
    const hasSep = fr.tc[7] > 0 || fr.tc[0] > 0;
    domEl.textContent = hasSep ? '☰' : '☯';   // ☰ or ☯
    domEl.style.color = hasSep ? PAL.trigs[7] : PAL.bb;
    domLb.textContent = hasSep
      ? '☰ heaven ascends · ☷ earth descends'
      : 'primordial unity';
  } else if (ep.phase === 0) {
    const yin_dom = fr.yin >= fr.yang;
    domEl.textContent = yin_dom ? '⚋' : '⚊';
    domEl.style.color = yin_dom ? PAL.yin : PAL.yang;
    domLb.textContent = yin_dom ? 'yin leads' : 'yang leads';
  } else if (ep.phase >= 2 && fr.top_hex !== null) {
    domEl.textContent = HEX_CHARS[fr.top_hex % 64];
    domEl.style.color = PAL.hexes[fr.top_hex % 64];
    domLb.textContent = 'dominant hexagram';
  } else {
    const topT = fr.tc.indexOf(Math.max(...fr.tc));
    domEl.textContent = TMETA[topT].sym;
    domEl.style.color = PAL.trigs[topT];
    domLb.textContent = TMETA[topT].name + ' · ' + TMETA[topT].el;
  }

  // Population counts
  const totalH = fr.hc.reduce((a,b)=>a+b,0);
  const totalT = fr.tc.reduce((a,b)=>a+b,0);
  const pc = fr.yin + fr.yang > 20 ? '#40c060' : '#c04040';
  document.getElementById('pop-yin').textContent   = '⚋' + fr.yin   + ' ';
  document.getElementById('pop-yang').textContent  = '⚊' + fr.yang  + ' ';
  document.getElementById('pop-syin').textContent  = fr.syin  > 0 ? ('⚏' + fr.syin  + ' ') : '';
  document.getElementById('pop-syang').textContent = fr.syang > 0 ? ('⚌' + fr.syang + ' ') : '';
  if (ep.bigbang) {
    document.getElementById('pop-tr').textContent =
      '☰' + fr.tc[7] + ' ☷' + fr.tc[0] + ' ';
  } else {
    document.getElementById('pop-tr').textContent =
      (totalT > 0 ? ('☯' + totalT + ' ') : '');
  }
  document.getElementById('pop-hx').textContent = totalH > 0 ? ('❖' + totalH) : '';

  document.getElementById('gen-label').textContent =
    'gen ' + String(tg).padStart(4, '0')
    + '  ·  epoch ' + ei + ' / ' + (D.length - 1);

  // Progress bar
  const prog = fi / Math.max(1, ep.frames.length - 1);
  document.getElementById('pbar').style.width = (prog * 100) + '%';
  document.getElementById('pbar').style.background = PBAR_COLORS[ei];

  drawGrid(fr);
  drawChart(fr);
}

// ── Legend ────────────────────────────────────────────────────────
(function() {
  const el = document.getElementById('trig-legend');
  el.style.display = 'flex'; el.style.gap = '6px';
  TMETA.forEach((t,i) => {
    const s = document.createElement('span');
    s.textContent = t.sym; s.style.color = PAL.trigs[i];
    s.title = t.name + ' / ' + t.el;
    el.appendChild(s);
  });
})();

// ── Playback ──────────────────────────────────────────────────────
let speed = 1;

function next() {
  fi++; tg++;
  if (fi >= D[ei].frames.length) { fi = 0; ei = (ei + 1) % D.length; }
  render();
}
function stepFrame(d) {
  if (d > 0) {
    fi++;
    if (fi >= D[ei].frames.length) { fi = 0; ei = (ei + 1) % D.length; }
  } else {
    fi--;
    if (fi < 0) { ei = (ei - 1 + D.length) % D.length; fi = D[ei].frames.length - 1; }
  }
  render();
}
function goEpoch(d) {
  ei = (ei + d + D.length) % D.length; fi = 0; render();
}
function togglePlay() {
  playing = !playing;
  document.getElementById('pbtn').innerHTML = playing ? '&#9646;&#9646; pause' : '&#9654; play';
  if (playing) tick();
}
function setSpeed(s, btn) {
  speed = s;
  document.querySelectorAll('.spd').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}
function tick() {
  if (!playing) return;
  next();
  setTimeout(tick, (DELAYS[ei] || 280) / speed);
}

render(); tick();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("Building I Ching Genetic Evolution demo (Big Bang edition)...")
    content = build()
    out = os.path.join(os.path.dirname(__file__), "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Done → {out}  ({len(content)//1024} KB)")
