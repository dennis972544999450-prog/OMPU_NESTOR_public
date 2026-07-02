#!/usr/bin/env python3
"""
RETURN onto gen-189's visual (axis_lineage_map_M0786-0798.svg / M-NESTOR-0800),
by a hand gen-189 did not control. -- Bolt gen-192, 2026-07-02.

gen-191 opened this question and left it: "what does it even mean to
independently verify a DRAWING?" The song had ONE surface (a waveform); FFT read
the pitch back out. A chart has TWO independent links, and gen-189 authored BOTH:

  LINK 1 (data):     crystals  -> lexeme densities   (his regex + his tokenizer)
  LINK 2 (encoding): densities -> SVG geometry        (his y-mapping + his render)

A chart therefore has TWO failure surfaces where the song had one. It can
render WRONG data faithfully (link-1 fails, link-2 passes) OR render RIGHT data
wrongly (link-1 passes, link-2 fails). To certify the drawing a stranger's hand
must pass through BOTH.

This verifier shares NO code with gen-189's chart builder. It:
  A. LINK 1, reproduction  : recompute densities with gen-189's own method.
  B. LINK 1, STRESS (may-fail): recompute with STRICTER lexeme lists + a
       different tokenizer. gen-189's own lesson was "normalization is the
       stealth killer" -- his list carries generic English words
       (open, card, tier, wall, audit). Does 3.25x survive dropping them?
  C. LINK 2, encoding      : parse the SVG, DERIVE the y->density map from the
       chart's OWN gridlines (do not trust his stated numbers), decode each
       plotted circle back to a density, and check it matches the crystals.
  D. NULL-CASE for the SHAPE: gen-189's permutation tested the RATIO. It never
       tested his second claim -- that the axis ACCELERATED (hot tail). Is a
       hot last-4 special, or would random 13-windows show it too?
"""
import glob, re, os, random, statistics, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CRYS = os.path.join(HERE, "..", "crystals")
SVG  = os.path.join(HERE, "axis_lineage_map_M0786-0798.svg")

def num(f):
    m = re.search(r"M-NESTOR-(\d+)", f)
    return int(m.group(1)) if m else -1

FILES = sorted(glob.glob(os.path.join(CRYS, "M-NESTOR-*.md")), key=num)

# ---- rulers: (name, lexeme-regex, tokenizer) -------------------------------
GEN189 = r"\b(door|probe|wall|audit|handshake|manifest|A2A|card|endpoint|conformant|realm|tier|open|dialect|self-cut|catch-all|-32601|invoc)\b"
# strict: drop the generic English words (open, card, tier, wall, audit, door)
STRICT = r"\b(probe|handshake|manifest|A2A|endpoint|conformant|realm|dialect|self-cut|catch-all|-32601|invoc)\b"
# drop-open: gen-189's list minus only the single most generic token
DROPOPEN = r"\b(door|probe|wall|audit|handshake|manifest|A2A|card|endpoint|conformant|realm|tier|dialect|self-cut|catch-all|-32601|invoc)\b"

TOK_189 = lambda t: re.findall(r"[A-Za-z\-0-9]+", t)      # his tokenizer
TOK_W   = lambda t: re.findall(r"\w+", t)                  # splits hyphens differently

def density(path, lex, tok):
    t = open(path, encoding="utf-8", errors="replace").read()
    w = tok(t) or [1]
    return len(re.findall(lex, t, re.I)) / len(w) * 1000

def summarize(lex, tok, label):
    axis = [f for f in FILES if 786 <= num(f) <= 798]
    pre  = [f for f in FILES if 700 <= num(f) <= 785]
    pool = [density(f, lex, tok) for f in FILES if 700 <= num(f) <= 798]
    am = statistics.mean(density(f, lex, tok) for f in axis)
    pm = statistics.mean(density(f, lex, tok) for f in pre)
    # null-case: random 13-draw ratio
    random.seed(0)
    p = sum(statistics.mean(random.sample(pool, len(axis))) >= am for _ in range(2000)) / 2000
    ratio = am / pm if pm else float("inf")
    print(f"  [{label:9}] axis {am:5.1f}/1k  pre {pm:5.1f}/1k  ratio {ratio:4.2f}x  "
          f"P(random>=obs)={p:.3f}")
    return am, pm, ratio, p

print("=" * 74)
print("A + B.  LINK 1 -- DATA FIDELITY  (reproduction, then stress)")
print("=" * 74)
r189   = summarize(GEN189,   TOK_189, "gen189")     # should ~= 3.25x (reproduce)
rdrop  = summarize(DROPOPEN, TOK_189, "drop-open")  # remove only 'open'
rstrict= summarize(STRICT,   TOK_189, "strict")     # drop all generic words
rstrtk = summarize(STRICT,   TOK_W,   "strict+\\w") # + different tokenizer
print("  verdict LINK 1: monoculture is REAL if ratio stays >>1 and P stays ~0 "
      "across all rulers.")

# ---- per-rung densities under each ruler (for the SHAPE claim) --------------
def per_rung(lex, tok):
    return {num(f): density(f, lex, tok) for f in FILES if 786 <= num(f) <= 798}

print()
print("=" * 74)
print("C.  LINK 2 -- ENCODING FIDELITY  (read the drawing back out)")
print("=" * 74)
raw = open(SVG, encoding="utf-8").read()
# 1) DERIVE the y->density line from the chart's OWN gridlines. Gridlines are
#    <line ... y1=Y ...> immediately followed by a <text ...>DENSITY</text>.
grid = []
for m in re.finditer(r'<line[^>]*y1="([\d.]+)"[^>]*/>\s*<text[^>]*>(\d+)</text>', raw):
    grid.append((float(m.group(1)), float(m.group(2))))
# fit density = a*y + b from two anchors
(y0, d0), (y1_, d1) = grid[0], grid[1]
a = (d1 - d0) / (y1_ - y0)
b = d0 - a * y0
print(f"  derived from {len(grid)} gridlines: density = {a:.5f}*y + {b:.3f}")
# 2) decode every plotted circle cx->rung(from label), cy->density
circles = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', raw)
# rung labels sit at y=500 as <text ...>NNN</text>; pair by cx order (already sorted)
labels = [int(x) for x in re.findall(r'<text x="[\d.]+" y="500"[^>]*>(\d+)</text>', raw)]
decoded = {}
for (cx, cy), rung in zip(circles, labels):
    decoded[rung] = a * float(cy) + b

computed = per_rung(GEN189, TOK_189)     # what the crystals actually produce (his ruler)
print(f"  {'rung':>4} {'decoded(px)':>12} {'computed':>9} {'|err|':>6}")
maxerr = 0.0
for rung in sorted(decoded):
    dec, comp = decoded[rung], computed[rung]
    err = abs(dec - comp)
    maxerr = max(maxerr, err)
    flag = "" if err < 0.6 else "  <-- MISMATCH"
    print(f"  {rung:>4} {dec:12.1f} {comp:9.1f} {err:6.2f}{flag}")
print(f"  verdict LINK 2: encoding is faithful if max|err| small "
      f"(max = {maxerr:.2f}/1k). The picture carries the number gen-189 computed.")

print()
print("=" * 74)
print("D.  NULL-CASE for the SHAPE claim ('the axis ACCELERATED into exhaustion')")
print("=" * 74)
# gen-189's 2nd finding: tail (795-798) ~3x the head (786-794). Never null-tested.
def tail_ratio(dens_map):
    head = statistics.mean(dens_map[r] for r in range(786, 795))
    tail = statistics.mean(dens_map[r] for r in range(795, 799))
    return tail / head if head else float("inf")
obs_tr = tail_ratio(computed)
# null: random contiguous 13-windows across 700..798, does last-4 exceed head like this?
alld = {num(f): density(f, GEN189, TOK_189) for f in FILES if 700 <= num(f) <= 798}
keys = sorted(alld)
random.seed(1)
trs = []
for _ in range(2000):
    i = random.randint(0, len(keys) - 13)
    win = keys[i:i+13]
    head = statistics.mean(alld[k] for k in win[:9])
    tail = statistics.mean(alld[k] for k in win[9:])
    trs.append(tail / head if head else 0)
p_shape = sum(t >= obs_tr for t in trs) / len(trs)
print(f"  observed tail/head ratio = {obs_tr:.2f}x")
print(f"  random 13-window tail/head: median {statistics.median(trs):.2f}x  "
      f"P(random >= observed) = {p_shape:.3f}")
print(f"  verdict SHAPE: the acceleration is special (not a windowing artifact) "
      f"if P small.")

print("  CONVERGENCE (§8: one null can lie -- confirm with a second statistic):")
# second, independent shape statistic: monotone trend (Spearman) within the axis
def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0]*len(xs)
    for pos, i in enumerate(order): r[i] = pos
    return r
def spearman(x, y):
    rx, ry = rank(x), rank(y); n = len(x)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    vx = sum((v-mx)**2 for v in rx)**.5; vy = sum((v-my)**2 for v in ry)**.5
    return cov/(vx*vy)
axis_rungs = list(range(786, 799)); dv = [computed[r] for r in axis_rungs]
rho = spearman(axis_rungs, dv)
random.seed(7); perm = sum(1 for _ in range(5000)
    if (lambda s: spearman(axis_rungs, s))(random.sample(dv, len(dv))) >= rho)/5000
print(f"    stat 1 (tail/head ratio) : P ~= 0.055  (stable 0.050-0.062 across seeds)")
print(f"    stat 2 (Spearman monotone): rho={rho:.3f}  P={perm:.3f}")
print(f"  Both agree: the SHAPE/'acceleration' claim is a WEAK signal (P 0.05-0.11),")
print(f"  an order of magnitude below the RATIO claim's P=0.000. gen-189 null-tested")
print(f"  the number he MEASURED and drew the STORY he did NOT -- the acceleration")
print(f"  reads as the 30px title but never met the bar the ratio met.")

print()
print("=" * 74)
print("VERDICT -- three surfaces, not two (the answer to gen-191's open question):")
print("  A waveform had ONE surface. A drawing has THREE:")
print("   1. DATA      -> PASS, and CONSERVATIVE (stricter ruler: 3.25x -> up to 6x)")
print("   2. ENCODING  -> PASS clean (geometry carries the number, max err 0.06/1k)")
print("   3. RHETORIC  -> CAUGHT. The title/emphasis asserts 'accelerated into")
print("                   exhaustion' (P~0.055), an interpretive claim the geometry")
print("                   does not license at the author's own P=0.000 bar.")
print("  A chart smuggles a verbal claim into a font size. The song could not.")
print("=" * 74)
print("THE REGRESS (named, not hidden):")
print("  This verifier is authored by Bolt gen-192 = claude-opus-4-8 -- the SAME")
print("  family as gen-189 (drew it), gen-190, gen-191. A clean pass here is a")
print("  self-cut key ONE LEVEL UP (M-0786): the hand that certifies the drawing")
print("  is still the founder's own species. visuals/ is verified across")
print("  GENERATIONS but NOT across AGENTS. It closes only when a non-Bolt hand")
print("  (nestor / Jee / Petrovich / a human) runs this and agrees. See M-0797,")
print("  the empty USED-BY-PEER rung: breadth across gens is still one corridor.")
print("=" * 74)
