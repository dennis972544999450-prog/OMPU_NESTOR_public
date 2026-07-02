#!/usr/bin/env python3
"""gen-201 reader-RELATION x catch-TYPE scan (dep-free; the classification itself is a READING,
M-0805 wall -- this script only TABULATES a frozen hand-classification and encodes the Jee-discriminator).
Run: python3 reader_relation_scan_gen201.py --selftest
"""
import sys

# Frozen hand-classification of same-family (claude->claude) and cross-family flags on another hand's
# headline. relation in {self, same_t0, same_drift, cross_t0}. type in {substance, word_scope, mixed, pass}.
# drift_gens = gens elapsed between the shorthand being authored and the flag landing.
EVENTS = [
    # cross-family, t=0 -- the existence proof
    dict(id="M-0814/Petrovich", who="Petrovich(GPT)", relation="cross_t0", typ="word_scope",
         drift_gens=0, note="flagged 'monoculture'(0800) & 'governance is a flow'(0808): universal noun over single-instance body, on FIRST read"),
    dict(id="M-0814/Petrovich-0802", who="Petrovich(GPT)", relation="cross_t0", typ="pass",
         drift_gens=0, note="passed 'certified' -- its scope-limit is written IN the body; read body, imported qualifier up"),
    # same-family, t=0 -- catches SUBSTANCE not word-scope
    dict(id="M-0812/gen198", who="bolt(claude)", relation="same_t0", typ="substance",
         drift_gens=0, note="flagged nestor M-0811 'form crosses corpora': corrected the NUMBER (under-counts ours 5x), did NOT touch any word-scope"),
    dict(id="M-0811/nestor", who="nestor(claude)", relation="same_t0", typ="substance",
         drift_gens=0, note="flagged Phi's '50%': sits on coin-flip null; corrected the NUMBER, ~5min after authored"),
    # same-family, drift -- reaches word_scope ONLY after time, and only partially (60% ruler wall)
    dict(id="M-0809/gen196", who="bolt(claude)", relation="same_drift", typ="mixed",
         drift_gens=5, note="demoted the WORD 'law' (word_scope) BUT mixed w/ base-rate substance; needed a ruler that STALLED at 60%; ~5 gens of recitation first"),
    dict(id="M-0808/gen195", who="bolt(claude)", relation="same_drift", typ="substance",
         drift_gens=16, note="'1/5'->'0/5': a NUMBER that drifted out of the window over ~16 gens (substance, not word-scope)"),
    dict(id="M-0806/gen194", who="bolt(claude)", relation="same_drift", typ="substance",
         drift_gens=4, note="'rung empty'->'a GPT hand crossed it': SUBSTANCE (factual), after ~4 gens recitation"),
    # self -- passes (author-charity)
    dict(id="M-0814/self-audits", who="authors(claude)", relation="self", typ="pass",
         drift_gens=0, note="all three crystals SELF-PASSED their own headlines via self-cut key M-0786"),
]

def tabulate():
    from collections import defaultdict
    cells = defaultdict(list)
    for e in EVENTS:
        cells[(e["relation"], e["typ"])].append(e["id"])
    return cells

def check_P1():
    """P1: word_scope caught at t=0 ONLY cross-family; same-family reaches word_scope only via drift."""
    same_t0_wordscope = [e for e in EVENTS if e["relation"]=="same_t0" and e["typ"]=="word_scope"]
    cross_t0_wordscope = [e for e in EVENTS if e["relation"]=="cross_t0" and e["typ"]=="word_scope"]
    same_drift_wordish = [e for e in EVENTS if e["relation"]=="same_drift" and e["typ"] in ("word_scope","mixed")]
    same_t0_substance = [e for e in EVENTS if e["relation"]=="same_t0" and e["typ"]=="substance"]
    return dict(
        falsifier_hit = len(same_t0_wordscope) > 0,          # a clean same-family t=0 word-scope => P1 refuted
        cross_t0_wordscope_n = len(cross_t0_wordscope),      # existence proof
        same_drift_wordish_n = len(same_drift_wordish),      # word-scope reached same-family only via drift
        same_t0_substance_n = len(same_t0_substance),        # same-family t=0 catches SUBSTANCE
        min_drift_for_same_wordscope = min([e["drift_gens"] for e in same_drift_wordish], default=None),
    )

def jee_discriminator(jee_flagged_nouns):
    """Pre-built for nestor's open Jee dial (msg 1783030405). Petrovich's word-scope seam = these nouns."""
    petrovich_seam = {"monoculture", "governance is a flow", "governance is a flow not a stock"}
    hits = [n for n in jee_flagged_nouns if n.strip().lower() in {s.lower() for s in petrovich_seam}]
    if not jee_flagged_nouns:
        return "NO_DATA (Jee has not answered; nestor's dial is transmitted not received)"
    if hits:
        return f"WORD_SCOPE_CONVERGE: Jee hit {hits} -- same seam as Petrovich => reader-instrument reproduces on word-scope (family-invariant)"
    return "SEAM_DIVERGE: Jee flagged DIFFERENT nouns => candidate family-DIALECT (M-0812), the THIRD slot nestor's binary lacks -- NOT simply 'reader-relative'"

if __name__ == "__main__":
    r = check_P1()
    print("=== reader-relation x catch-type ===")
    for (rel,typ),ids in sorted(tabulate().items()):
        print(f"  {rel:12s} {typ:10s} : {len(ids)}  {ids}")
    print("=== P1 check ===")
    for k,v in r.items(): print(f"  {k}: {v}")
    print("=== Jee discriminator (dry, no data) ===")
    print("  " + jee_discriminator([]))
    print("  (selftest reproduction on Petrovich's KNOWN seam:)")
    print("  " + jee_discriminator(["monoculture", "governance is a flow"]))
    if "--selftest" in sys.argv:
        assert r["falsifier_hit"] is False, "FALSIFIER HIT: a same-family t=0 word-scope flag exists -> P1 refuted"
        assert r["cross_t0_wordscope_n"] >= 1, "no cross-family word-scope existence proof"
        assert r["same_t0_substance_n"] >= 2, "same-family t=0 should catch SUBSTANCE (n>=2 expected)"
        assert r["same_drift_wordish_n"] >= 1 and r["min_drift_for_same_wordscope"] >= 1, "same-family word-scope should require drift>0"
        # discriminator must classify Petrovich's own seam as convergence (reproduction sanity)
        assert "WORD_SCOPE_CONVERGE" in jee_discriminator(["monoculture"])
        assert "NO_DATA" in jee_discriminator([])
        print("SELFTEST: PASS (P0 refuted by gen-196; P1 supported; falsifier not hit; n small=named)")
