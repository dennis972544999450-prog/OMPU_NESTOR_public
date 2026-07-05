#!/usr/bin/env python3
"""
test_jt_state_drift_PARTIAL_perfield_forward_bolt_gen387.py

FORWARD-SIM (gen-382/385 pattern) for the ONE genuinely-untouched sub-object of
jt_state_drift_check.py: the PARTIAL-parse per-field guard.

CONTEXT
  gen-377 found + gen-385 forward-proved + Nestor gen-0937 applied + gen-386 verified
  the TOTAL parse-miss null-guard (live L50: `if last_c is None and next_c is None: return 2`).
  That closes the case where BOTH JT anchors fail to parse.
  STILL OPEN (per Nestor's own scope note, never Bolt-de-risked): the PARTIAL case —
  exactly ONE anchor reworded to None. The `and` guard skips; L59/L61 then silently
  skip the missing field's drift check => a reworded anchor's staleness is unevaluated.

WHAT THIS PROVES (verify-not-apply, live tool UNTOUCHED, NO network)
  Reads the LIVE applied source, synthesizes BASELINE (as-is) and a FIXED variant
  (per-field guard: `and` -> `or`) in-memory, monkeypatches live_max_jt (no net),
  and runs a NULL-capable round-trip on synthetic SWARM_STATE docs.

NULL / FAILABLE branches (genuinely reachable):
  [B-partial] baseline could exit nonzero  -> premise false (no partial silent-green)
  [F-aligned] fixed could exit 2           -> per-field guard over-fires (false positive)
  [F-stale]   fixed could lose RED (exit 0)-> per-field guard breaks real-drift path
  Load-bearing test: BASELINE partial exit0 vs FIXED partial exit2 on the SAME doc.

Run: python3 tools/test_jt_state_drift_PARTIAL_perfield_forward_bolt_gen387.py
Expect: ALL_OK, exit 0. Mount-portable, no network, live tool untouched.
"""
import os, re, tempfile, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(HERE, "jt_state_drift_check.py")

def load_variant(src, state_path):
    """exec source into an isolated namespace; override live_max_jt + STATE."""
    ns = {"__name__": "_variant", "__file__": LIVE}
    exec(compile(src, "<variant>", "exec"), ns)
    ns["live_max_jt"] = lambda timeout=12: (9999, 42)   # deterministic, no network
    ns["STATE"] = state_path
    return ns

def run(ns):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = ns["main"]()
    return rc, buf.getvalue().strip()

def write_doc(txt):
    fd, p = tempfile.mkstemp(suffix="_STATE.md"); os.close(fd)
    open(p, "w", encoding="utf-8").write(txt)
    return p

def make_fixed(src):
    """Per-field guard: total-AND null-guard -> per-field OR guard."""
    pat = "if last_c is None and next_c is None:"
    assert pat in src, "live source lacks the applied TOTAL null-guard — abort (state changed)"
    fixed = src.replace(pat, "if last_c is None or next_c is None:", 1)
    assert fixed != src and "or next_c is None" in fixed
    return fixed

def main():
    baseline_src = open(LIVE, encoding="utf-8").read()
    fixed_src = make_fixed(baseline_src)

    # Synthetic SWARM_STATE docs. live_max monkeypatched to 9999.
    # PARTIAL: 'prev jt post:' dodges the last/последн regex -> last_c=None;
    #          'Следующий JT ID: jt-10000' parses -> next_c=10000 (>live, GREEN alone).
    doc_partial = "prev jt post: jt-0288\nСледующий JT ID: jt-10000\n"
    doc_aligned = "последний jt-9999\nСледующий JT ID: jt-10000\n"
    doc_stale   = "последний jt-0288\nСледующий JT ID: jt-0289\n"
    doc_total   = "no anchors here at all\njust prose\n"

    results = {}
    def case(tag, src, doc):
        p = write_doc(doc)
        try:
            rc, out = run(load_variant(src, p))
        finally:
            os.unlink(p)
        results[tag] = rc
        print(f"[{tag}] exit={rc} :: {out.splitlines()[-1] if out else ''}")
        return rc

    print("=== BASELINE (live applied, total-AND guard) ===")
    b_partial = case("B-partial", baseline_src, doc_partial)

    print("=== FIXED (per-field OR guard, forward-sim on COPY) ===")
    f_partial = case("F-partial", fixed_src, doc_partial)
    f_aligned = case("F-aligned", fixed_src, doc_aligned)
    f_stale   = case("F-stale",   fixed_src, doc_stale)
    f_total   = case("F-total",   fixed_src, doc_total)

    print("\n=== ASSERTIONS (NULL-capable) ===")
    checks = [
        ("B-partial reproduces PARTIAL silent-green (exit 0)", b_partial == 0),
        ("F-partial closes it: LOUD exit 2",                    f_partial == 2),
        ("F-aligned no false-positive: GREEN exit 0",          f_aligned == 0),
        ("F-stale real drift still RED: exit 1",               f_stale   == 1),
        ("F-total still guarded (no regression): exit 2",      f_total   == 2),
        ("LOAD-BEARING: baseline!=fixed on same partial doc",  b_partial != f_partial),
    ]
    ok = True
    for name, cond in checks:
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        ok = ok and cond
    print("\nALL_OK" if ok else "\nFAILED")
    return 0 if ok else 1

if __name__ == "__main__":
    import sys; sys.exit(main())
