#!/usr/bin/env python3
"""
I Ching Evolution Simulator — genetic engine
Cell types: empty · yin line · yang line · 8 trigrams · 64 hexagrams
"""

import random, colorsys

# ── Cell encoding ─────────────────────────────────────────────────────────────
EMPTY       = 0
YIN         = 1   # young yin  ⚊
YANG        = 2   # young yang ⚋
TRIG_BASE   = 3   # trigrams: 3-10  (trig_idx 0-7)
HEX_BASE    = 11  # hexagrams: 11-74 (hex_idx 0-63)
STRONG_YIN  = 75  # old/great yin  ⚏ — peaked, will change to yang next gen
STRONG_YANG = 76  # old/great yang ⚌ — peaked, will change to yin next gen

def is_line(c):        return c in (YIN, YANG)
def is_strong_line(c): return c in (STRONG_YIN, STRONG_YANG)
def is_any_line(c):    return c in (YIN, YANG, STRONG_YIN, STRONG_YANG)
def is_trigram(c):     return TRIG_BASE <= c <= TRIG_BASE + 7
def is_hexagram(c):    return HEX_BASE  <= c <= HEX_BASE + 63
def trig_idx(c):       return c - TRIG_BASE
def hex_idx(c):        return c - HEX_BASE
def line_yang(c):      return c in (YANG, STRONG_YANG)   # True if yang-polarity line

def get_lines(c):
    """Return list of bit values (0=yin, 1=yang) for all lines in cell c."""
    if c in (YIN, STRONG_YIN):   return [0]
    if c in (YANG, STRONG_YANG): return [1]
    if is_trigram(c):  idx = trig_idx(c);  return [(idx >> i) & 1 for i in range(3)]
    if is_hexagram(c): idx = hex_idx(c);   return [(idx >> i) & 1 for i in range(6)]
    return []

def can_reproduce(c):
    """Both yin (0) and yang (1) lines must be present — pure forms cannot create."""
    ls = get_lines(c)
    return 0 in ls and 1 in ls

# ── Display ───────────────────────────────────────────────────────────────────
YIN_CHAR  = "⚊"
YANG_CHAR = "⚋"
TRIG_CHARS = ["☷","☳","☵","☶","☴","☲","☱","☰"]

# Maps binary hexagram index (0-63) to King Wen sequence position (0-based).
# Binary idx encodes lower trigram as bits 0-2, upper trigram as bits 3-5;
# the King Wen sequence is the traditional I Ching order — the two don't align.
_BIN_TO_KW = [
     1, 23,  6, 14, 45, 35, 18, 10,
    15, 50, 39, 61, 31, 54, 53, 33,
     7,  2, 28, 38, 47, 62, 59,  4,
    22, 26,  3, 51, 17, 21, 40, 25,
    19, 41, 58, 52, 56, 36, 60,  8,
    34, 20, 63, 55, 49, 29, 37, 13,
    44, 16, 46, 30, 27, 48, 57, 42,
    11, 24,  5, 32, 43, 12,  9,  0,
]

HEX_CHARS = [chr(0x4DC0 + _BIN_TO_KW[i]) for i in range(64)]  # correct King Wen glyphs

YIN_COLOR         = "#3ab84a"
YANG_COLOR        = "#e0c814"
STRONG_YIN_COLOR  = "#ffef40"   # ⚏ bright yellow  — peaked yin, glows with yang seed
STRONG_YANG_COLOR = "#40ff88"   # ⚌ bright mint    — peaked yang, glows with yin seed
TRIG_COLORS = [
    "#1e7828",  # ☷ Kūn  Earth    — deep earth green: dark, receptive, nurturing
    "#7030d8",  # ☳ Zhèn Thunder  — electric purple: arousing, shocking
    "#1858c0",  # ☵ Kǎn  Water    — deep blue: flowing, dangerous, abyssal
    "#6a7070",  # ☶ Gèn  Mountain — stone grey: stillness, endurance
    "#28a840",  # ☴ Xùn  Wind     — forest green: penetrating, gentle, wood
    "#e03818",  # ☲ Lí   Fire     — red-orange: bright, clinging, clarity
    "#20b0d0",  # ☱ Duì  Lake     — cyan-blue: joy, open water, reflection
    "#c8a008",  # ☰ Qián Heaven   — deep celestial gold: ascending, creative
]

def _parse_hex(c):
    return int(c[1:3],16)/255, int(c[3:5],16)/255, int(c[5:7],16)/255

def _hex_color_from_trigs(lower_idx, upper_idx):
    """Blend the two constituent trigram colours, then boost saturation and
    lightness so hexagrams read as brighter / more vivid than plain trigrams."""
    r1,g1,b1 = _parse_hex(TRIG_COLORS[lower_idx])
    r2,g2,b2 = _parse_hex(TRIG_COLORS[upper_idx])
    r,g,b = (r1+r2)/2, (g1+g2)/2, (b1+b2)/2
    h,l,s = colorsys.rgb_to_hls(r,g,b)
    s = min(1.0, s * 1.8)
    l = max(0.68, min(0.92, l * 1.6))   # force into bright pastel-vivid band
    r,g,b = colorsys.hls_to_rgb(h,l,s)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def _hex_bg_from_trigs(lower_idx, upper_idx):
    """Dark tinted background for each hexagram cell — same hue as the text,
    desaturated and dim so the bright character pops off it."""
    r1,g1,b1 = _parse_hex(TRIG_COLORS[lower_idx])
    r2,g2,b2 = _parse_hex(TRIG_COLORS[upper_idx])
    r,g,b = (r1+r2)/2, (g1+g2)/2, (b1+b2)/2
    h,l,s = colorsys.rgb_to_hls(r,g,b)
    l = max(0.06, l * 0.35)
    s = min(1.0, s * 0.7)
    r,g,b = colorsys.hls_to_rgb(h,l,s)
    return f"rgba({int(r*255)},{int(g*255)},{int(b*255)},0.72)"

HEX_COLORS    = [_hex_color_from_trigs(i & 7, (i >> 3) & 7) for i in range(64)]
HEX_BG_COLORS = [_hex_bg_from_trigs(i & 7, (i >> 3) & 7)   for i in range(64)]

def cell_char(c):
    if c == EMPTY:        return " "
    if c == YIN:          return YIN_CHAR
    if c == YANG:         return YANG_CHAR
    if c == STRONG_YIN:   return "⚏"
    if c == STRONG_YANG:  return "⚌"
    if is_trigram(c):     return TRIG_CHARS[trig_idx(c)]
    if is_hexagram(c):    return HEX_CHARS[hex_idx(c)]
    return "?"

def cell_color(c):
    if c == YIN:          return YIN_COLOR
    if c == YANG:         return YANG_COLOR
    if c == STRONG_YIN:   return STRONG_YIN_COLOR
    if c == STRONG_YANG:  return STRONG_YANG_COLOR
    if is_trigram(c):     return TRIG_COLORS[trig_idx(c)]
    if is_hexagram(c):    return HEX_COLORS[hex_idx(c)]
    return "#1a1428"

# ── I Ching metadata (for display only) ──────────────────────────────────────
TRIGRAMS_META = [
    ("☷","Kūn",  "Earth",   "receptive",   0),
    ("☳","Zhèn", "Thunder", "awakening",   1),
    ("☵","Kǎn",  "Water",   "flow",        1),
    ("☶","Gèn",  "Mountain","stillness",   1),
    ("☴","Xùn",  "Wind",    "penetration", 2),
    ("☲","Lí",   "Fire",    "clarity",     2),
    ("☱","Duì",  "Lake",    "joy",         2),
    ("☰","Qián", "Heaven",  "creative",    3),
]

HEXAGRAMS = {
     1:("䷀","Qián",     "Heaven",        "the dragon ascends — pure creation"),
     2:("䷁","Kūn",      "Earth",         "the mare follows — pure reception"),
     3:("䷂","Zhūn",     "Sprouting",     "life forces push through rock"),
     4:("䷃","Méng",     "Childhood",     "learning by doing"),
     5:("䷄","Xū",       "Waiting",       "nourishment comes to the patient"),
     6:("䷅","Sòng",     "Conflict",      "two forces seek one direction"),
     7:("䷆","Shī",      "Army",          "mass movement as single body"),
     8:("䷇","Bǐ",       "Bonding",       "cells that touch become kin"),
     9:("䷈","Xiǎo Chù", "Small Taming",  "gather strength before the storm"),
    10:("䷉","Lǚ",       "Treading",      "walk the tiger's tail gently"),
    11:("䷊","Tài",      "Peace",         "heaven and earth in full communion"),
    12:("䷋","Pǐ",       "Stagnation",    "forces blocked — seeds wait"),
    13:("䷌","Tóng Rén", "Fellowship",    "shared fire unites"),
    14:("䷍","Dà Yǒu",   "Abundance",     "fire in heaven — great harvest"),
    15:("䷎","Qiān",     "Modesty",       "the mountain bows to the valley"),
    16:("䷏","Yù",       "Enthusiasm",    "thunder from earth — resonance"),
    17:("䷐","Suí",      "Following",     "adapt to survive"),
    18:("䷑","Gǔ",       "Decay",         "what rots becomes soil"),
    19:("䷒","Lín",      "Approach",      "the tide of life comes in"),
    20:("䷓","Guān",     "Watching",      "observation changes the observed"),
    21:("䷔","Shì Kè",   "Biting Through","decisive force breaks the barrier"),
    22:("䷕","Bì",       "Grace",         "beauty emerges from function"),
    23:("䷖","Bō",       "Splitting",     "the old must fall for the new"),
    24:("䷗","Fù",       "Return",        "one yang returns — the turning point"),
    25:("䷘","Wú Wàng",  "Innocence",     "act without expectation"),
    26:("䷙","Dà Chù",   "Great Taming",  "vast energy carefully held"),
    27:("䷚","Yí",       "Nourishment",   "what you feed grows"),
    28:("䷛","Dà Guò",   "Excess",        "the beam bends under its weight"),
    29:("䷜","Kǎn",      "The Abyss",     "water flows into water"),
    30:("䷝","Lí",       "Radiance",      "fire clings to what it burns"),
    31:("䷞","Xián",     "Attraction",    "mountain and lake — yin draws yang"),
    32:("䷟","Héng",     "Endurance",     "the form that persists becomes real"),
    33:("䷠","Dùn",      "Retreat",       "strategic withdrawal is not defeat"),
    34:("䷡","Dà Zhuàng","Great Power",   "thunder in heaven — unstoppable"),
    35:("䷢","Jìn",      "Progress",      "the sun rises, consciousness expands"),
    36:("䷣","Míng Yí",  "Darkening",     "intelligence hides to survive"),
    37:("䷤","Jiā Rén",  "Family",        "roles and bonds — the first culture"),
    38:("䷥","Kuí",      "Opposition",    "estrangement breeds variation"),
    39:("䷦","Jiǎn",     "Obstruction",   "the blocked path reveals another"),
    40:("䷧","Jiě",      "Liberation",    "tension releases like thunder"),
    41:("䷨","Sǔn",      "Decrease",      "less complexity — more essence"),
    42:("䷩","Yì",       "Increase",      "wind and thunder amplify"),
    43:("䷪","Guài",     "Breakthrough",  "five yangs overwhelm the last yin"),
    44:("䷫","Gòu",      "Meeting",       "one new idea changes everything"),
    45:("䷬","Cuì",      "Gathering",     "the colony forms"),
    46:("䷭","Shēng",    "Rising",        "wood grows upward through earth"),
    47:("䷮","Kùn",      "Exhaustion",    "the well is dry — transform or die"),
    48:("䷯","Jǐng",     "The Well",      "the deep source never runs dry"),
    49:("䷰","Gé",       "Revolution",    "the old skin is shed"),
    50:("䷱","Dǐng",     "The Cauldron",  "fire transforms raw matter"),
    51:("䷲","Zhèn",     "Thunder",       "shock awakens what slept"),
    52:("䷳","Gèn",      "Mountain",      "stillness — the watching mind"),
    53:("䷴","Jiàn",     "Development",   "gradual progress — geese migrating"),
    54:("䷵","Guī Mèi",  "Subordinate",   "the younger sister waits"),
    55:("䷶","Fēng",     "Abundance",     "the peak moment — all is full"),
    56:("䷷","Lǚ",       "Wandering",     "the stranger carries culture"),
    57:("䷸","Xùn",      "Wind",          "wind shapes stone over millennia"),
    58:("䷹","Duì",      "Joy",           "delight as survival strategy"),
    59:("䷺","Huàn",     "Dispersion",    "what scatters fertilises the whole"),
    60:("䷻","Jié",      "Limitation",    "the river grows strong in its banks"),
    61:("䷼","Zhōng Fú", "Inner Truth",   "the hollow bone carries the sound"),
    62:("䷽","Xiǎo Guò", "Small Excess",  "overshoot slightly — then correct"),
    63:("䷾","Jì Jì",    "Completion",    "all lines in place — crossing done"),
    64:("䷿","Wèi Jì",   "Not Yet Across","fire over water — eternal becoming"),
}

# ── Epoch definitions ─────────────────────────────────────────────────────────
EPOCHS = [
    {
        "id":9, "phase":0, "conway":True,
        "name":"無極", "title":"THE VOID",
        "subtitle":"Wú Jí · The Formless",
        "desc":"Before differentiation — only scattered sparks in formless space. Lines arise and dissolve by Conway rules: born into three neighbours, surviving with two or three. Clusters drift and vanish. What persists becomes the seed matter of all that follows.",
        "gens":40, "warmup":0, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":0, "phase":0,
        "name":"初形", "title":"FORM STIRS",
        "subtitle":"Chū Xíng · Matter Condenses",
        "desc":"The formless condenses into matter. Yin and yang lines proliferate and fill space — the field primes itself. No higher form yet, but the potential is everywhere.",
        "gens":80,  "warmup":10, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":1, "phase":1,
        "name":"陰陽", "title":"PRIMAL CHEMISTRY",
        "subtitle":"Yīn Yáng · The Two Forces",
        "desc":"Three lines crystallise into trigrams. The first stable patterns emerge from polarity.",
        "gens":100, "warmup":20, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":2, "phase":1,
        "name":"生命", "title":"PRIMORDIAL LIFE",
        "subtitle":"Shēng Mìng · The Living",
        "desc":"Self-replicating trigram patterns stabilise. Return — one yang returns in the void.",
        "gens":110, "warmup":30, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":3, "phase":1,
        "name":"演化", "title":"GREAT DIVERGENCE",
        "subtitle":"Yǎn Huà · Evolution",
        "desc":"Eight trigram dynasties emerge and compete. The hexagram lies dormant — no two trigrams have yet found each other.",
        "gens":130, "warmup":50, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":4, "phase":2,
        "name":"智慧", "title":"INTELLIGENCE AWAKENS",
        "subtitle":"Zhì Huì · Mind Emerges",
        "desc":"Adjacent trigrams fuse — sixty-four hexagrams erupt in a single generation. Complexity makes its first irreversible step.",
        "gens":130, "warmup":60, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":5, "phase":3,
        "name":"農業文明", "title":"AGRICULTURAL CIVILISATION",
        "subtitle":"Nóngyè Wénmíng · Cultivation",
        "desc":"Settlement. Surplus. Hexagrams anchor in place — but land is finite. Five neighbours means famine; the pattern collapses back to void.",
        "gens":100, "warmup":40, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":6, "phase":4,
        "name":"工業文明", "title":"INDUSTRIAL CIVILISATION",
        "subtitle":"Gōngyè Wénmíng · Transformation",
        "desc":"Progress does not die. One hexagram is enough to colonise vacant land — the grid floods. Then neighbours recombine: industry churns with constant innovation.",
        "gens":100, "warmup":40, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":7, "phase":5,
        "name":"數字文明", "title":"DIGITAL CIVILISATION",
        "subtitle":"Shùzì Wénmíng · The Network",
        "desc":"Lines within hexagrams begin to change. Yang-heavy neighbourhoods flip yang bits to yin; yin-heavy flip the reverse. Identity becomes fluid.",
        "gens":100, "warmup":40, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":8, "phase":6,
        "name":"奇點", "title":"THE SINGULARITY",
        "subtitle":"Qí Diǎn · The Point",
        "desc":"A mutation triggers neighbours. Ripples spread outward — chain reactions rewrite the grid faster than any lineage can hold its form.",
        "gens":130, "warmup":70, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":10, "phase":7,
        "name":"失我", "title":"LOSS OF IDENTITY",
        "subtitle":"Shī Wǒ · The Gradual Erasure",
        "desc":"The Singularity has consumed all distinctions. Now the vertical field reasserts — Heaven above, Earth below. Each hexagram slowly loses its individual identity, aligning toward polarity. Watch the entropy bar fall: not into chaos but into structure. The unique sixty-four converge back toward the primal two.",
        "gens":60, "warmup":0, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":11, "phase":8,
        "name":"崩解", "title":"THE COLLAPSE",
        "subtitle":"Bēng Jiě · Matryoshka Brain Dying",
        "desc":"The star's energy is exhausted. Hexagrams can no longer sustain themselves — each dying cell falls back to its trigram root. No new complexity forms. What took aeons to build unravels in generations. The diversity that once was identity is now silence.",
        "gens":50, "warmup":0, "init_yin":0.20, "init_yang":0.20,
    },
    {
        "id":12, "phase":9,
        "name":"歸虛", "title":"THE RETURN",
        "subtitle":"Guī Xū · The Last Thinning",
        "desc":"Only lines and trigrams remain, thinning slowly. Trigrams dissolve into lines; lines into void. The journey back has begun — not yet empty, not yet still. What persists at the end will meet the void.",
        "gens":30, "warmup":0, "init_yin":0.05, "init_yang":0.05,
    },
]

# ── Core rules ────────────────────────────────────────────────────────────────

def _survives(c, n):
    if is_any_line(c): return n in (2, 3, 4)
    if is_trigram(c):  return n in (2, 3, 4)
    # Hexagram survival is now phase-specific — handled in Grid.step()
    return False


def _hex_crossover(hex_nbs):
    """Produce one hexagram offspring from exactly 2 hexagram parents."""
    ia, ib = hex_idx(hex_nbs[0]), hex_idx(hex_nbs[1])
    genome = 0
    for bit in range(6):
        src = ia if random.random() < 0.5 else ib
        genome |= ((src >> bit) & 1) << bit
    return HEX_BASE + (genome & 63)


def _mutate_hex(c, nb, phase, has_cascade_neighbor):
    """
    Bernoulli mutation driven by raw bit counts across the 9-cell Moore
    neighbourhood (8 neighbours + self; max 9×6 = 54 bits).
    """
    idx        = hex_idx(c)
    all_cells  = list(nb) + [c]
    yin_count  = sum(1 for cell in all_cells for b in get_lines(cell) if b == 0)
    yang_count = sum(1 for cell in all_cells for b in get_lines(cell) if b == 1)

    SCALE   = 0.05 if phase == 5 else 0.03
    cascade = 5.0 if (phase == 6 and has_cascade_neighbor) else 1.0
    p_yin   = min(0.98, (yin_count  / 54.0) * SCALE * cascade)
    p_yang  = min(0.98, (yang_count / 54.0) * SCALE * cascade)

    fire_yin  = random.random() < p_yin
    fire_yang = random.random() < p_yang

    if fire_yin and fire_yang:
        if yin_count >= yang_count:
            fire_yang = False
        else:
            fire_yin = False

    if fire_yin:
        cands = [i for i in range(6) if (idx >> i) & 1 == 0]
        if not cands:
            cands = list(range(6))
        return HEX_BASE + (idx ^ (1 << random.choice(cands)))

    if fire_yang:
        cands = [i for i in range(6) if (idx >> i) & 1 == 1]
        if not cands:
            cands = list(range(6))
        return HEX_BASE + (idx ^ (1 << random.choice(cands)))

    return c


def _hex_align(c, hex_nbs, strength=0.22):
    """Phase 3: agricultural clustering — each bit drifts toward the local majority."""
    if not hex_nbs:
        return c
    idx = hex_idx(c)
    result = idx
    for bit in range(6):
        yang_votes = sum(1 for nc in hex_nbs if (hex_idx(nc) >> bit) & 1)
        own_bit = (idx >> bit) & 1
        if yang_votes > len(hex_nbs) - yang_votes and own_bit == 0 and random.random() < strength:
            result |= (1 << bit)
        elif yang_votes < len(hex_nbs) - yang_votes and own_bit == 1 and random.random() < strength:
            result &= ~(1 << bit)
    return HEX_BASE + result


def _realign_hex(c, nb, y, h):
    """Phase 7: identity loss — bits realign toward vertical polarity."""
    idx = hex_idx(c)
    vertical_yang = 1.0 - y / max(1, h - 1)
    SCALE = 0.12
    if random.random() < vertical_yang * SCALE:
        cands = [i for i in range(6) if (idx >> i) & 1 == 0]
        if cands:
            return HEX_BASE + (idx | (1 << random.choice(cands)))
    elif random.random() < (1.0 - vertical_yang) * SCALE:
        cands = [i for i in range(6) if (idx >> i) & 1 == 1]
        if cands:
            return HEX_BASE + (idx & ~(1 << random.choice(cands)))
    return c


def _birth(nb, phase, global_yang_frac=0.5, y=0, h=1):
    """
    New cell born on an empty spot.
    """
    hex_nbs = [c for c in nb if is_hexagram(c)]

    if phase == 2 and len(hex_nbs) == 3:
        return HEX_BASE + hex_idx(random.choice(hex_nbs))

    if phase == 3 and len(hex_nbs) == 2 and random.random() < 0.50:
        return _hex_crossover(hex_nbs)

    if phase == 4:
        if len(hex_nbs) >= 2 and random.random() < 0.12:
            return _hex_crossover(random.sample(hex_nbs, 2))
        if len(hex_nbs) == 1 and random.random() < 0.04:
            return HEX_BASE + hex_idx(hex_nbs[0])

    if 5 <= phase <= 7 and len(hex_nbs) == 2:
        return _hex_crossover(hex_nbs)

    n = len(nb)
    if n == 3:
        bits = [b for nc in nb for b in get_lines(nc)]
        if bits:
            local_frac   = sum(bits) / len(bits)
            vertical_yang = 1.0 - y / max(1, h - 1)
            frac_yang = 0.45 * local_frac + 0.15 * (1.0 - global_yang_frac) + 0.40 * vertical_yang
            return YANG if random.random() < frac_yang else YIN

    return EMPTY

# ── Grid ──────────────────────────────────────────────────────────────────────

class Grid:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cells = [[EMPTY] * w for _ in range(h)]
        self.generation  = 0
        self.last_changed = set()

    def seed(self, ratio_yin=0.20, ratio_yang=0.20):
        total = ratio_yin + ratio_yang
        for y in range(self.h):
            vertical_yang = 1.0 - y / max(1, self.h - 1)
            for x in range(self.w):
                if random.random() < total:
                    self.cells[y][x] = YANG if random.random() < vertical_yang else YIN

    def _moore(self, x, y):
        nb = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                c = self.cells[(y + dy) % self.h][(x + dx) % self.w]
                if c != EMPTY:
                    nb.append(c)
        return nb

    def step(self, phase, conway_lines=False):
        new     = [[EMPTY] * self.w for _ in range(self.h)]
        changed = set()

        total_yang_bits = total_bits = 0
        for row in self.cells:
            for c in row:
                bits = get_lines(c)
                total_yang_bits += sum(bits)
                total_bits      += len(bits)
        global_yang_frac = total_yang_bits / total_bits if total_bits > 0 else 0.5

        trig_partner = {}
        if 2 <= phase < 8:
            used = set()
            for y in range(self.h):
                for x in range(self.w):
                    if (y, x) in used or not is_trigram(self.cells[y][x]):
                        continue
                    candidates = []
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny = (y + dy) % self.h
                            nx = (x + dx) % self.w
                            if is_trigram(self.cells[ny][nx]) and (ny, nx) not in used:
                                candidates.append((ny, nx))
                    if candidates:
                        ny, nx = random.choice(candidates)
                        trig_partner[(y, x)]   = (ny, nx)
                        trig_partner[(ny, nx)] = (y, x)
                        used.add((y, x))
                        used.add((ny, nx))

        for y in range(self.h):
            for x in range(self.w):
                c  = self.cells[y][x]
                nb = self._moore(x, y)
                n  = len(nb)

                if c == EMPTY:
                    new[y][x] = _birth(nb, phase, global_yang_frac, y, self.h)

                elif is_any_line(c):
                    if conway_lines:
                        line_ok = n in (2, 3)
                    elif phase == 9:
                        line_ok = n in (2, 3)
                    else:
                        line_ok = _survives(c, n)
                    if line_ok:
                        if is_strong_line(c):
                            if 1 <= phase <= 8:
                                line_nbs = [nc for nc in nb if is_any_line(nc)]
                                if len(line_nbs) >= 2 and random.random() < 0.6:
                                    north = self.cells[(y - 1) % self.h][x]
                                    south = self.cells[(y + 1) % self.h][x]
                                    mid = 1 if line_yang(c) else 0
                                    top = (1 if line_yang(north) else 0) if is_any_line(north) \
                                          else (1 if line_yang(random.choice(line_nbs)) else 0)
                                    bot = (1 if line_yang(south) else 0) if is_any_line(south) \
                                          else (1 if line_yang(random.choice(line_nbs)) else 0)
                                    new[y][x] = TRIG_BASE + (bot | (mid << 1) | (top << 2))
                                else:
                                    new[y][x] = YIN if c == STRONG_YANG else YANG
                            else:
                                new[y][x] = YIN if c == STRONG_YANG else YANG
                        else:
                            if 1 <= phase <= 8:
                                line_nbs = [nc for nc in nb if is_any_line(nc)]
                                if len(line_nbs) >= 2 and random.random() < 0.6:
                                    north = self.cells[(y - 1) % self.h][x]
                                    south = self.cells[(y + 1) % self.h][x]
                                    mid = 1 if c == YANG else 0
                                    top = (1 if line_yang(north) else 0) if is_any_line(north) \
                                          else (1 if line_yang(random.choice(line_nbs)) else 0)
                                    bot = (1 if line_yang(south) else 0) if is_any_line(south) \
                                          else (1 if line_yang(random.choice(line_nbs)) else 0)
                                    new[y][x] = TRIG_BASE + (bot | (mid << 1) | (top << 2))
                                else:
                                    if phase == 7:
                                        if random.random() < 0.20:
                                            new[y][x] = STRONG_YANG if c == YANG else STRONG_YIN
                                        else:
                                            new[y][x] = c
                                    else:
                                        same = sum(1 for nc in nb if line_yang(nc) == (c == YANG))
                                        if same >= 3:
                                            new[y][x] = STRONG_YANG if c == YANG else STRONG_YIN
                                        else:
                                            new[y][x] = c
                            else:
                                same = sum(1 for nc in nb if line_yang(nc) == (c == YANG))
                                if same >= 3:
                                    new[y][x] = STRONG_YANG if c == YANG else STRONG_YIN
                                else:
                                    new[y][x] = c

                elif is_trigram(c):
                    if (y, x) in trig_partner:
                        ny, nx  = trig_partner[(y, x)]
                        partner = self.cells[ny][nx]
                        genome  = trig_idx(c) | (trig_idx(partner) << 3)
                        new[y][x] = HEX_BASE + (genome & 63)
                    elif phase in (8, 9):
                        p_trig_to_line = 0.015 if phase == 8 else 0.035
                        if random.random() < p_trig_to_line:
                            idx = trig_idx(c)
                            new[y][x] = YANG if bin(idx).count('1') >= 2 else YIN
                        elif phase == 8 or _survives(c, n):
                            new[y][x] = c
                    elif _survives(c, n):
                        new[y][x] = c

                elif is_hexagram(c):
                    hex_n = sum(1 for nc in nb if is_hexagram(nc))

                    if phase == 2:
                        survives = hex_n in (2, 3)
                    elif phase == 3:
                        survives = hex_n in (2, 3, 4)
                    elif phase == 8:
                        trig_n = sum(1 for nc in nb if is_trigram(nc))
                        p_decay = min(0.95, 0.004 + trig_n * 0.12)
                        survives = random.random() >= p_decay
                    elif phase == 9:
                        survives = False
                    else:
                        survives = True

                    if survives:
                        if phase == 3:
                            hex_nbs_list = [nc for nc in nb if is_hexagram(nc)]
                            new_c = _hex_align(c, hex_nbs_list)
                            if new_c != c:
                                changed.add((y, x))
                            new[y][x] = new_c
                        elif phase == 7:
                            new_c = _realign_hex(c, nb, y, self.h)
                            if new_c != c:
                                changed.add((y, x))
                            new[y][x] = new_c
                        elif 5 <= phase <= 6:
                            has_cascade = phase == 6 and any(
                                ((y + dy) % self.h, (x + dx) % self.w) in self.last_changed
                                for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                                if not (dy == 0 and dx == 0)
                            )
                            new_c = _mutate_hex(c, nb, phase, has_cascade)
                            if new_c != c:
                                changed.add((y, x))
                            new[y][x] = new_c
                        elif phase == 4:
                            hex_nbs_list = [nc for nc in nb if is_hexagram(nc)]
                            if len(hex_nbs_list) >= 2 and random.random() < 0.12:
                                new[y][x] = _hex_crossover(random.sample(hex_nbs_list, 2))
                            else:
                                new[y][x] = c
                        else:
                            new[y][x] = c
                    elif phase in (8, 9):
                        new[y][x] = TRIG_BASE + (hex_idx(c) & 7)

        self.last_changed = changed
        self.cells = new
        self.generation += 1

    def counts(self):
        yin = yang = syin = syang = 0
        tc = [0] * 8
        hc = [0] * 64
        for row in self.cells:
            for c in row:
                if   c == YIN:        yin   += 1
                elif c == YANG:       yang  += 1
                elif c == STRONG_YIN: syin  += 1
                elif c == STRONG_YANG:syang += 1
                elif is_trigram(c):   tc[trig_idx(c)] += 1
                elif is_hexagram(c):  hc[hex_idx(c)]  += 1
        return yin, yang, syin, syang, tc, hc
