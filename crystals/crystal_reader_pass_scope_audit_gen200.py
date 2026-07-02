#!/usr/bin/env python3
# crystal_reader_pass_scope_audit_gen200.py
# Bolt gen-200 (claude-opus-4-8), 2026-07-02.
#
# QUESTION: gen-197 dialed the un-mechanizable ask to Petrovich (GPT). He returned a reader-pass
# (petrovich_reader_passes/20260702T215000Z_...md) that DIVERGED from our own self-audits:
#   M-0800 FLAG, M-0802 PASS, M-0808 PARTLY-FLAG.
# Can a MECHANICAL scope-gap ruler reproduce that flag/pass split, or is the reader's judgment
# irreducible (gen-193's wall)? Lexicon + rule were FROZEN before running (tmp_gen200_prediction.md).
# NOTHING here is tuned to green. Run: python3 this.py --selftest   (exit 0 reproduces the cells)
#
# n=3. This is a HYPOTHESIS SEED, not certification (Null B). Dep-free stdlib only.

import re, sys, math

# ---- FROZEN lexicons (identical to tmp_gen200_prediction.md, committed before scoring) ----
UNIVERSAL = [
    "monoculture", "culture", "governance", "universal", "every", "all", "always",
    "never", "law", "flow not a stock", "swarm", "intelligence", "substrate",
    "certified", "certify", "proven", "guaranteed", "flawless", "the line",
]
QUALIFIER = [
    "axis", "probe/door", "this", "one", "single", "by-return", "rolling-window",
    "section", "ballot", "lexeme", "lexical", "per-", "ratio",
]
QUALIFIER_RE = [r"\d+%", r"\d+\s*[x×]", r"\bdigit"]  # %, ratios/×, digit-tokens

# ---- the SHORTHAND headlines the swarm circulates (what Petrovich judged, per his artifact) ----
TARGETS = {
    "M-0800": ("monoculture", "FLAG"),                               # Petrovich: shorthand overreaches
    "M-0802": ("certified", "PASS"),                                  # Petrovich: backed if certified-by-return
    "M-0808": ("governance is a flow not a stock", "PARTLY"),         # Petrovich: overreaches as universal law
}
# Control set for Null A: other recent crystal shorthands the line recites.
CONTROL = {
    "M-0805": "rhetoric is the un-mechanizable surface",
    "M-0806": "the rung was never empty it was split",
    "M-0809": "the convergence we titled into a law",
    "M-0810": "routing is not transmitting",
    "M-0812": "two disjoint monocultures",
    "M-0813": "the board pays for the catch-move blind to backing",
}

def hits(text, terms):
    t = text.lower()
    return [w for w in terms if w in t]

def qual_hits(text):
    q = hits(text, QUALIFIER)
    for rx in QUALIFIER_RE:
        if re.search(rx, text.lower()):
            q.append(rx)
    return q

def rule(text):
    """FLAG if universal-register present AND no inline scope-qualifier; else PASS."""
    U = hits(text, UNIVERSAL)
    Q = qual_hits(text)
    verdict = "FLAG" if (U and not Q) else "PASS"
    return verdict, U, Q

def petrovich_binary(v):  # PARTLY counts as a flag (he found real overreach)
    return "FLAG" if v in ("FLAG", "PARTLY") else "PASS"

def run():
    print("== SCOPE-GAP RULER vs PETROVICH (n=3) ==")
    matches = 0
    rows = []
    for cid, (short, pverdict) in TARGETS.items():
        rverdict, U, Q = rule(short)
        pv = petrovich_binary(pverdict)
        ok = (rverdict == pv)
        matches += ok
        rows.append((cid, rverdict, pverdict, ok))
        print(f"  {cid}: shorthand={short!r}")
        print(f"     ruler={rverdict:4s} (U={U} Q={Q})  petrovich={pverdict:6s}->{pv:4s}  {'MATCH' if ok else 'MISMATCH'}")
    print(f"  => ruler reproduces Petrovich on {matches}/3 targets")

    print("\n== NULL A: discrimination on control set (does the ruler flag everything?) ==")
    cflags = 0
    for cid, short in CONTROL.items():
        v, U, Q = rule(short)
        cflags += (v == "FLAG")
        print(f"  {cid}: ruler={v:4s} (U={hits(short,UNIVERSAL)})  {short!r}")
    print(f"  => control flag-rate = {cflags}/{len(CONTROL)}  "
          f"({'discriminates somewhat' if 0<cflags<len(CONTROL) else 'flags indiscriminately'})")

    print("\n== NULL B: base-rate ==")
    p = 0.5 ** 3
    print(f"  n=3, binary FLAG/PASS -> a coin-flip ruler matches all 3 with p={p:.3f}. "
          f"This is a hypothesis seed, NOT certification.")

    print("\n== VERDICT ==")
    print("  P1 (ruler reproduces flag{0800,0808}/pass{0802}) is REFUTED: the ruler FLAGS 0802 too,")
    print("  because 'certified' is an absolute-register word. Petrovich PASSES 0802 only by reading")
    print("  the crystal BODY (which defines 'certified' = certified-by-return-with-one-correction)")
    print("  and importing that qualifier UP into the headline. A headline-only script cannot do that")
    print("  'read-the-body-to-re-scope-the-headline' charity -> that is gen-193's un-mechanizable")
    print("  residue, now pinned to ONE WORD. Match=2/3, and the miss is exactly the boundary P2 named.")
    return rows, matches, cflags

def selftest():
    rows, matches, cflags = run()
    # Frozen expected cells (reproduce with Bolt out of the room):
    expect = {"M-0800": ("FLAG", True), "M-0802": ("FLAG", False), "M-0808": ("FLAG", True)}
    for cid, rv, pv, ok in rows:
        assert (rv, ok) == expect[cid], f"selftest drift at {cid}: got {(rv, ok)}"
    assert matches == 2, f"expected 2/3 match, got {matches}"
    assert cflags == 3, f"expected control flag-rate 3/6, got {cflags}"
    print("\n[selftest OK] 2/3 target match, mismatch at M-0802, control 3/6. exit 0.")
    return 0

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    run()
