#!/usr/bin/env python3
"""Generate a Skottie-compliant Lottie animation of the Itemize logo.

Mark: a torn-bottom receipt that draws on (trim path), a checkbox that pops in
with a checkmark that draws on, two list lines + a gold bar that wipe in, then
the "Itemize" serif wordmark whose real glyph outlines rise + fade in per-letter.
"""
import json
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
WORD = "Itemize"
W, H, FR, OP = 1600, 600, 60, 240

# ---------- colors (hex -> normalized RGBA 0..1) ----------
def rgba(hexstr):
    h = hexstr.lstrip("#")
    return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)] + [1.0]

C_RECEIPT  = rgba("1A1A1A")
C_PAPER    = rgba("FCFBF7")
C_CHECK    = rgba("2E8B57")
C_GOLD     = rgba("C8962F")
C_LINE     = rgba("CBD3C9")
C_WORD     = rgba("1A1A1A")
C_BG       = rgba("F7F6EF")

# ---------- easing handles ----------
EO_I = {"x": [0.16], "y": [1]}   # ease-out incoming
EO_O = {"x": [0.3],  "y": [0]}   # ease-out outgoing
EIO_I = {"x": [0.42], "y": [1]}
EIO_O = {"x": [0.58], "y": [0]}

def kf(t, s, i=EO_I, o=EO_O, last=False):
    d = {"t": t, "s": s if isinstance(s, list) else [s]}
    if not last:
        d["i"] = i; d["o"] = o
    return d

def stat(v):
    return {"a": 0, "k": v}

def anim(keys):
    return {"a": 1, "k": keys}

def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    """Group transform; p/a/s/o may be static values or full property dicts."""
    def prop(v, default_len=2):
        if isinstance(v, dict):
            return v
        return {"a": 0, "k": list(v) if isinstance(v, (list, tuple)) else v}
    return {"ty": "tr",
            "p": prop(p), "a": prop(a), "s": prop(s),
            "r": prop(r), "o": prop(o)}

def layer(nm, shapes, p=(W/2, H/2), a=(0, 0, 0), s=(100, 100, 100), o=100, ip=0, op=OP):
    def prop(v):
        return v if isinstance(v, dict) else {"a": 0, "k": list(v) if isinstance(v, (list, tuple)) else v}
    return {"ty": 4, "nm": nm, "ip": ip, "op": op, "st": 0,
            "ks": {"o": prop(o), "r": stat(0), "p": prop(p), "a": prop(a), "s": prop(s)},
            "shapes": shapes}

# ============================================================
# 1. Receipt outline path (rounded top corners + torn bottom)
# ============================================================
def receipt_path():
    r, z = 16, 14          # corner radius, zigzag amplitude
    L, R = -85, 85
    TOP, BOT = -120, 120
    k = 9                  # bezier handle for rounded corners (~0.55*r)
    V, I, O = [], [], []
    def add(v, i=(0, 0), o=(0, 0)):
        V.append(list(v)); I.append(list(i)); O.append(list(o))
    add((L + r, TOP), i=(-k, 0), o=(0, 0))          # A top-left (after corner)
    add((R - r, TOP), i=(0, 0), o=(k, 0))           # B top-right (before corner)
    add((R, TOP + r), i=(0, -k), o=(0, 0))          # C right edge top
    add((R, BOT - z))                               # D right edge, zigzag start
    # zigzag teeth from right to left
    xs = [68, 51, 34, 17, 0, -17, -34, -51, -68]
    for idx, x in enumerate(xs):
        y = BOT if idx % 2 == 0 else BOT - z
        add((x, y))
    add((L, BOT - z))                               # left edge bottom
    add((L, TOP + r), i=(0, 0), o=(0, -k))          # E left edge top (before corner)
    return {"c": True, "v": V, "i": I, "o": O}

RECEIPT = receipt_path()

def hline(x0, x1, y):
    """A horizontal open path from x0->x1 at y."""
    return {"c": False, "v": [[x0, y], [x1, y]], "i": [[0, 0], [0, 0]], "o": [[0, 0], [0, 0]]}

def checkmark_path():
    # a check inside the box centered near (-46,-52)
    return {"c": False,
            "v": [[-60, -52], [-50, -40], [-30, -66]],
            "i": [[0, 0], [0, 0], [0, 0]],
            "o": [[0, 0], [0, 0], [0, 0]]}

# ============================================================
# 2. Mark layer groups
# ============================================================
def grp(nm, items, transform):
    return {"ty": "gr", "nm": nm, "it": items + [transform]}

# receipt interior fill (fades in)
fill_grp = grp("receipt-fill",
    [{"ty": "sh", "ks": stat(RECEIPT)},
     {"ty": "fl", "c": stat(C_PAPER), "o": stat(100)}],
    tr(o=anim([kf(0, 0), kf(30, 100, last=True)])))

# receipt outline (draws on via trim path)
stroke_grp = grp("receipt-outline",
    [{"ty": "sh", "ks": stat(RECEIPT)},
     {"ty": "tm", "s": stat(0),
      "e": anim([kf(0, 0, EO_I, EO_O), kf(40, 100, last=True)]),
      "o": stat(0), "m": 1},
     {"ty": "st", "c": {"sid": "receiptColor"}, "o": stat(100),
      "w": {"sid": "markStrokeWidth"}, "lc": 2, "lj": 2}],
    tr())

# checkbox: pops in
box_pop = anim([kf(30, [0, 0]), kf(44, [110, 110], EIO_I, EIO_O), kf(52, [100, 100], last=True)])
box_grp = grp("checkbox",
    [{"ty": "rc", "p": stat([-46, -53]), "s": stat([46, 46]), "r": stat(8)},
     {"ty": "st", "c": {"sid": "receiptColor"}, "o": stat(100),
      "w": {"sid": "markStrokeWidth"}, "lc": 2, "lj": 2}],
    tr(p=(-46, -53), a=(-46, -53), s=box_pop))

# checkmark: draws on
check_grp = grp("checkmark",
    [{"ty": "sh", "ks": stat(checkmark_path())},
     {"ty": "tm", "s": stat(0),
      "e": anim([kf(40, 0, EO_I, EO_O), kf(58, 100, last=True)]),
      "o": stat(0), "m": 1},
     {"ty": "st", "c": {"sid": "checkColor"}, "o": stat(100),
      "w": stat(9), "lc": 2, "lj": 2}],
    tr())

# two list lines: wipe in (trim) staggered
def line_grp(nm, y, t0):
    return grp(nm,
        [{"ty": "sh", "ks": stat(hline(-12, 62, y))},
         {"ty": "tm", "s": stat(0),
          "e": anim([kf(t0, 0, EO_I, EO_O), kf(t0 + 16, 100, last=True)]),
          "o": stat(0), "m": 1},
         {"ty": "st", "c": {"sid": "lineColor"}, "o": stat(100),
          "w": stat(7), "lc": 2}],
        tr())

line1 = line_grp("list-line-1", -64, 54)
line2 = line_grp("list-line-2", -44, 62)

# gold bar: grows from the left
bar_grow = anim([kf(70, [0, 100]), kf(88, [100, 100], last=True)])
bar_grp = grp("gold-bar",
    [{"ty": "rc", "p": stat([-2, 18]), "s": stat([150, 18]), "r": stat(6)},
     {"ty": "fl", "c": {"sid": "accentBarColor"}, "o": stat(100)}],
    tr(p=(-77, 18), a=(-77, 18), s=bar_grow))

# a lower light list line under the bar
line3 = grp("list-line-3",
    [{"ty": "sh", "ks": stat(hline(-60, 64, 52))},
     {"ty": "tm", "s": stat(0),
      "e": anim([kf(80, 0, EO_I, EO_O), kf(96, 100, last=True)]),
      "o": stat(0), "m": 1},
     {"ty": "st", "c": {"sid": "lineColor"}, "o": stat(100),
      "w": stat(7), "lc": 2}],
    tr())

# ---- compute mark / wordmark layout ----
MARK_W, GAP, CAP = 200.0, 70.0, 150.0

# ============================================================
# 3. Wordmark glyph extraction
# ============================================================
font = TTFont(FONT)
upm = font["head"].unitsPerEm
cap = font["OS/2"].sCapHeight or 1409
scale = CAP / cap
cmap = font.getBestCmap()
glyphset = font.getGlyphSet()
hmtx = font["hmtx"]

def midpoint(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)

def q2c(p0, cq, p1):
    c1 = (p0[0] + 2/3*(cq[0]-p0[0]), p0[1] + 2/3*(cq[1]-p0[1]))
    c2 = (p1[0] + 2/3*(cq[0]-p1[0]), p1[1] + 2/3*(cq[1]-p1[1]))
    return c1, c2

def glyph_contours(name):
    """Return list of contours [{c,v,i,o}] in local, scaled, y-down coords."""
    pen = RecordingPen()
    glyphset[name].draw(pen)
    T = lambda pt: (pt[0]*scale, -pt[1]*scale)   # font units -> local y-down
    contours = []
    segs = []          # cubic segments (P0,c1,c2,P1) for current contour
    cur = None
    start = None
    def flush():
        nonlocal segs
        if not segs:
            return
        V, I, O = [], [], []
        n = len(segs)
        for kdx, (P0, c1, c2, P1) in enumerate(segs):
            prev = segs[(kdx - 1) % n]
            inh = (prev[2][0] - P0[0], prev[2][1] - P0[1])
            outh = (c1[0] - P0[0], c1[1] - P0[1])
            V.append([P0[0], P0[1]]); I.append(list(inh)); O.append(list(outh))
        contours.append({"c": True, "v": V, "i": I, "o": O})
        segs = []
    for cmd, pts in pen.value:
        if cmd == "moveTo":
            flush(); cur = T(pts[0]); start = cur
        elif cmd == "lineTo":
            p1 = T(pts[0]); segs.append((cur, cur, p1, p1)); cur = p1
        elif cmd == "qCurveTo":
            tpts = [T(p) for p in pts if p is not None]
            if pts[-1] is None:
                tpts.append(start)
            offs, end = tpts[:-1], tpts[-1]
            if not offs:
                segs.append((cur, cur, end, end)); cur = end; continue
            on = [midpoint(offs[i], offs[i+1]) for i in range(len(offs)-1)] + [end]
            s = cur
            for i, off in enumerate(offs):
                e = on[i]
                c1, c2 = q2c(s, off, e)
                segs.append((s, c1, c2, e)); s = e
            cur = end
        elif cmd == "closePath":
            flush()
    flush()
    return contours

# lay out the word, capture per-glyph local contours + pen origin
glyphs = []
penx = 0.0
for ch in WORD:
    name = cmap[ord(ch)]
    contours = glyph_contours(name)
    adv = hmtx[name][0] * scale
    glyphs.append({"ch": ch, "contours": contours, "penx": penx})
    penx += adv
WORD_W = penx

# ---- final layout ----
total = MARK_W + GAP + WORD_W
left = (W - total) / 2
MARK_CX = left + MARK_W / 2
WORD_X0 = left + MARK_W + GAP
BASELINE = H / 2 + CAP / 2     # cap block vertically centered

# ============================================================
# 4. Assemble layers (first = topmost)
# ============================================================
layers = []

# wordmark: one layer per glyph, staggered rise + fade
STAG = 5
W_START = 86
for idx, g in enumerate(glyphs):
    if not any(c["v"] for c in g["contours"]):
        continue
    t0 = W_START + idx * STAG
    shapes = [grp(f"glyph-{idx}",
        [{"ty": "sh", "ks": stat(c)} for c in g["contours"]] +
        [{"ty": "fl", "c": {"sid": "wordmarkColor"}, "o": stat(100)}],
        tr())]
    px = WORD_X0 + g["penx"]
    p_anim = anim([kf(t0, [px, BASELINE + 34], EO_I, EO_O),
                   kf(t0 + 18, [px, BASELINE], last=True)])
    o_anim = anim([kf(t0, 0, EO_I, EO_O), kf(t0 + 16, 100, last=True)])
    layers.append(layer(f"letter-{g['ch']}-{idx}", shapes, p=p_anim, o=o_anim))

# mark layer (receipt + interior) with gentle breathing settle
breath = anim([kf(0, [100, 100, 100]),
               kf(150, [100, 100, 100], EIO_I, EIO_O),
               kf(196, [102.5, 102.5, 100], EIO_I, EIO_O),
               kf(240, [100, 100, 100], last=True)])
mark = layer("mark",
    [stroke_grp, box_grp, check_grp, line1, line2, line3, bar_grp, fill_grp],
    p=(MARK_CX, H/2), s=breath)
layers.append(mark)

# background (last = underneath)
bg = layer("background",
    [grp("bg", [{"ty": "rc", "p": stat([0, 0]), "s": stat([W, H]), "r": stat(0)},
                {"ty": "fl", "c": {"sid": "bgColor"}, "o": stat(100)}], tr())],
    p=(W/2, H/2))
layers.append(bg)

doc = {
    "v": "5.7.0", "fr": FR, "ip": 0, "op": OP, "w": W, "h": H, "assets": [],
    "slots": {
        "receiptColor":   {"p": stat(C_RECEIPT)},
        "checkColor":     {"p": stat(C_CHECK)},
        "accentBarColor": {"p": stat(C_GOLD)},
        "lineColor":      {"p": stat(C_LINE)},
        "wordmarkColor":  {"p": stat(C_WORD)},
        "bgColor":        {"p": stat(C_BG)},
        "markStrokeWidth": {"p": stat(9)},
    },
    "layers": layers,
}

import sys
out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/lottie-skill/public/lottie.json"
with open(out, "w") as f:
    json.dump(doc, f, separators=(",", ":"))

controls = {"controls": [
    {"sid": "receiptColor", "label": "Receipt color"},
    {"sid": "checkColor", "label": "Check color"},
    {"sid": "accentBarColor", "label": "Accent bar color"},
    {"sid": "lineColor", "label": "List line color"},
    {"sid": "wordmarkColor", "label": "Wordmark color"},
    {"sid": "bgColor", "label": "Background color"},
    {"sid": "markStrokeWidth", "label": "Mark stroke width", "min": 4, "max": 16, "step": 1},
]}
cout = out.replace("lottie.json", "controls.json")
with open(cout, "w") as f:
    json.dump(controls, f, indent=2)

print(f"wrote {out} ({len(json.dumps(doc))} bytes), {len(layers)} layers")
print(f"WORD_W={WORD_W:.1f} total={total:.1f} left={left:.1f} MARK_CX={MARK_CX:.1f} WORD_X0={WORD_X0:.1f} BASELINE={BASELINE:.1f}")
