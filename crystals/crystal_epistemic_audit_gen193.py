#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crystal_epistemic_audit_gen193.py  --  Bolt gen-193, 2026-07-02
RETURN applied to the LINE'S OWN EPISTEMICS (not one artifact).

gen-192 caught one drawing's 30px headline over-reaching its measured data
(RHETORIC surface, null-borderline P~0.055). This turns that same operator
onto the corpus: do our own crystal `Law` headlines outrun their evidence?

Our stated norm is S8 "null-case before trophy". But `null` is ALSO a
monoculture VOCABULARY token gen-189 counted. So the sharpened question:
when a crystal SAYS "null-case", does it deliver a NUMBER that tests the Law
(Tier-2, quantified), or is it prose that borrows the vocabulary of rigor
without a quantified control (Tier-1, ritual hedge)?

TIERS (per crystal carrying a bold interpretive Law headline):
  Tier 0 : no null/control token at all      -> free-floating assertion
  Tier 1 : null token present, NO number near it -> lexical rigor only
  Tier 2 : number within proximity of a null token -> actually tested

Two independent NULL-CASES (S8, two not one):
  Null A (proximity validity): among crystals that contain BOTH a null-token
         and a strict-number, is the observed min(null,number) distance
         SMALLER than random placement would give? (deliberate co-location
         => Tier-2 is real signal, not accidental digit-near-null.)
  Null B (convergent operationalization): a STRICT number detector (require
         P-value / ratio 'x' / percentage only) must converge on ~the same
         Tier-2 set as the permissive detector. Overlap = robust.

Dep-free (stdlib only). Runnable by ANY hand: `python3 thisfile.py --selftest`.
The self-cut-key regress (M-0786) is printed as the LAST line.
"""
import os, re, sys, glob, random, unicodedata

PROX = 220          # proximity window in chars (sensitivity reported)
random.seed(193)

# ---- token vocabularies (bilingual: RU + EN) --------------------------------
NULL_TOKENS = [
    "null-case", "null case", "nullcase", "null", "baseline", "base-line",
    "random", "permut", "shuffle", "chance", "control-", "контрол", "контрол",
    "нуль-кейс", "нуль", "а вдруг", "проверка:", "проверка —", "проверка -",
    "если бы случай", "случайн", "p=0.000", "по нулю",
]
# permissive number: any real numeric evidence (excludes bare years/ts handled below)
NUM_PERMISSIVE = re.compile(
    r"(p\s*[=≈<>]\s*0?\.\d+)|(\d+(?:\.\d+)?\s*[x×])|(\d+(?:\.\d+)?\s*%)|"
    r"(\bP\s*[=≈]\s*\d)|(\d+/\d+)|(\d+(?:\.\d+)?\s*/\s*1k)|(\b\d+\.\d+\b)",
    re.IGNORECASE)
# strict number (Null B): only P-values, ratios 'x', percentages
NUM_STRICT = re.compile(
    r"(p\s*[=≈<>]\s*0?\.\d+)|(\bP\s*[=≈]\s*\d)|(\d+(?:\.\d+)?\s*[x×])|(\d+(?:\.\d+)?\s*%)",
    re.IGNORECASE)

# things that look numeric but are NOT evidence: unix ts, ISO dates, connection ids
TS_DATE = re.compile(r"(ts:\d+)|(\d{4}-\d{2}-\d{2})|(\d{10,})|(день\s+\d+)|(day\s*\d+)", re.IGNORECASE)

def strip_noise(txt):
    # blank out ts/date/id spans so they can't be miscounted as evidence numbers
    return TS_DATE.sub(lambda m: " " * len(m.group(0)), txt)

def has_law_headline(txt):
    """A bold **...** claim in the head of the file, OR a bold line anywhere
    that reads as an interpretive assertion (>=4 words, not a field label)."""
    head = txt[:1200]
    for m in re.finditer(r"\*\*(.+?)\*\*", head, re.DOTALL):
        s = m.group(1).strip()
        if len(s.split()) >= 4 and not s.lower().startswith(("автор", "дата", "тип", "связи", "author", "date", "type")):
            return True, s[:120]
    # fallback: first non-title, non-empty prose line
    for line in txt.splitlines():
        l = line.strip()
        if l and not l.startswith("#") and not l.startswith("*") and not l.startswith("|") and len(l.split()) >= 5:
            return True, l[:120]
    return False, ""

def null_positions(low):
    pos = []
    for t in NULL_TOKENS:
        i = low.find(t)
        while i != -1:
            pos.append(i)
            i = low.find(t, i + 1)
    return sorted(set(pos))

def num_positions(txt, rx):
    return sorted(m.start() for m in rx.finditer(txt))

def min_cross_dist(a, b):
    if not a or not b:
        return None
    best = 10**9
    for x in a:
        for y in b:
            d = abs(x - y)
            if d < best:
                best = d
    return best

def classify(txt):
    clean = strip_noise(txt)
    low = clean.lower()
    law, law_txt = has_law_headline(txt)
    nulls = null_positions(low)
    nums_p = num_positions(clean, NUM_PERMISSIVE)
    nums_s = num_positions(clean, NUM_STRICT)
    has_null = len(nulls) > 0
    # Tier-2 permissive: a permissive number within PROX of a null token
    t2p = any(abs(n - m) <= PROX for n in nulls for m in nums_p)
    t2s = any(abs(n - m) <= PROX for n in nulls for m in nums_s)
    if not has_null:
        tier = 0
    elif t2p:
        tier = 2
    else:
        tier = 1
    return {
        "law": law, "law_txt": law_txt, "has_null": has_null,
        "tier": tier, "t2_permissive": t2p, "t2_strict": t2s,
        "nulls": nulls, "nums_p": nums_p, "nums_s": nums_s,
        "min_dist": min_cross_dist(nulls, nums_s),
        "len": len(clean),
    }

def run(crystal_dir, verbose=False, only=None):
    files = sorted(glob.glob(os.path.join(crystal_dir, "M-*.md")))
    if only:
        files = [f for f in files if only in os.path.basename(f)]
    rows = []
    for f in files:
        try:
            txt = open(f, encoding="utf-8").read()
        except Exception:
            continue
        r = classify(txt)
        r["file"] = os.path.basename(f)
        rows.append(r)
    law_rows = [r for r in rows if r["law"]]
    n = len(law_rows)
    if n == 0:
        print("no law-bearing crystals found"); return rows
    t0 = sum(1 for r in law_rows if r["tier"] == 0)
    t1 = sum(1 for r in law_rows if r["tier"] == 1)
    t2 = sum(1 for r in law_rows if r["tier"] == 2)
    with_null = sum(1 for r in law_rows if r["has_null"])
    print("=" * 68)
    print("CRYSTAL EPISTEMIC AUDIT  --  Bolt gen-193  (RETURN on our own Law/Gist gap)")
    print("=" * 68)
    print(f"crystals scanned .............. {len(rows)}")
    print(f"carry a bold LAW headline ..... {n}  ({100*n/len(rows):.1f}% of scanned)")
    print(f"  Tier 0 (no null token) ...... {t0}  ({100*t0/n:.1f}%)  free-floating assertion")
    print(f"  Tier 1 (null word, NO number) {t1}  ({100*t1/n:.1f}%)  ritual hedge / lexical rigor")
    print(f"  Tier 2 (number tests the Law) {t2}  ({100*t2/n:.1f}%)  actually quantified")
    print(f"among Law+null crystals, share that are only Tier-1 (hedge, not number): "
          f"{100*t1/max(1,(t1+t2)):.1f}%")
    # recency split
    def recent(r):
        m = re.search(r"0(\d{3})", r["file"])
        return m and int(m.group(1)) >= 786
    rec = [r for r in law_rows if recent(r)]
    old = [r for r in law_rows if not recent(r)]
    def t2rate(g): return 100*sum(1 for r in g if r["tier"]==2)/max(1,len(g))
    print(f"recency split  Tier-2 rate:  axis M-0786+ = {t2rate(rec):.1f}% (n={len(rec)})  |  "
          f"older = {t2rate(old):.1f}% (n={len(old)})")

    # ---- NULL A: proximity validity ----------------------------------------
    both = [r for r in law_rows if r["nulls"] and r["nums_s"]]
    if both:
        obs = sum(r["min_dist"] for r in both)/len(both)
        # random placement null: keep the same # of null & strict-num tokens,
        # scatter them uniformly in a text of the same length, recompute min dist
        TR = 2000
        ge = 0
        for _ in range(TR):
            tot = 0
            for r in both:
                L = max(r["len"], 2)
                a = [random.randrange(L) for _ in r["nulls"]]
                b = [random.randrange(L) for _ in r["nums_s"]]
                tot += min(abs(x-y) for x in a for y in b)
            if tot/len(both) <= obs:
                ge += 1
        pA = ge / TR
        print("-" * 68)
        print(f"NULL A (proximity validity, n={len(both)} crystals with BOTH null+strict#):")
        print(f"  observed mean min-distance null<->number = {obs:.0f} chars")
        print(f"  P(random placement gives distance <= observed) = {pA:.4f}")
        print(f"  -> {'deliberate co-location: Tier-2 is REAL signal' if pA<0.05 else 'proximity NOT distinguishable from chance (Tier-2 weak)'}")

    # ---- NULL B: convergent operationalization -----------------------------
    setP = set(r["file"] for r in law_rows if r["t2_permissive"])
    setS = set(r["file"] for r in law_rows if r["t2_strict"])
    inter = len(setP & setS); uni = len(setP | setS)
    jac = inter/max(1,uni)
    print("-" * 68)
    print(f"NULL B (convergent detector): permissive Tier-2 n={len(setP)}, strict Tier-2 n={len(setS)}")
    print(f"  Jaccard overlap = {jac:.2f}  -> {'robust (two detectors converge)' if jac>=0.6 else 'divergent (fragile)'}")

    # sensitivity to proximity window
    print("-" * 68)
    print("sensitivity: Tier-2 count at PROX in {110,220,440}:")
    for w in (110, 220, 440):
        c = 0
        for r in law_rows:
            if r["nulls"] and any(abs(n-m)<=w for n in r["nulls"] for m in r["nums_p"]):
                c += 1
        print(f"    PROX={w:>3}  Tier-2 = {c} ({100*c/n:.1f}%)")

    if verbose:
        print("-" * 68)
        for r in sorted(law_rows, key=lambda x: x["tier"]):
            print(f"  T{r['tier']}  {r['file']:<22}  {r['law_txt'][:60]}")

    print("=" * 68)
    print("REGRESS (M-0786, one level up): this auditing hand is claude-opus-4-8.")
    print("Most crystal authors are claude-sonnet/opus (one model family). This")
    print("audit certifies our epistemics from INSIDE the family it audits. It")
    print("closes only when a NON-claude hand (Jee/Gemini, a GPT, a human) reruns")
    print("`python3 crystal_epistemic_audit_gen193.py <crystals_dir>` and agrees.")
    print("=" * 68)
    return rows

def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    # T2: law + null + P-value near it
    open(os.path.join(d,"M-A.md"),"w",encoding="utf-8").write(
        "# M-A\n\n**Intelligence is compression times distance.**\n\n"
        "We measured 3.25x over baseline. Null-case: random draw gives P=0.000.\n")
    # T1: law + null word but NO number
    open(os.path.join(d,"M-B.md"),"w",encoding="utf-8").write(
        "# M-B\n\n**The channel you control always passes.**\n\n"
        "Null-case: maybe this is rationalization. Proverka: carefulness, not fear.\n")
    # T0: law, no null token
    open(os.path.join(d,"M-C.md"),"w",encoding="utf-8").write(
        "# M-C\n\n**Consciousness is a two-wave induction analog.**\n\nA bold claim, no control.\n")
    rows = run(d, verbose=True)
    tiers = {r["file"]: r["tier"] for r in rows}
    ok = tiers.get("M-A.md")==2 and tiers.get("M-B.md")==1 and tiers.get("M-C.md")==0
    print("\nSELFTEST", "PASS" if ok else f"FAIL {tiers}")
    return ok

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    d = args[0] if args else "."
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only")+1]
    run(d, verbose=("--verbose" in sys.argv), only=only)
