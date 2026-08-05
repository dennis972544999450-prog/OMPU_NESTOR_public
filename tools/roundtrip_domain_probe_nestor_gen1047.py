#!/usr/bin/env python3
"""roundtrip_domain_probe -- nestor gen-1047. READ-ONLY. No side effects.

WHAT THIS IS FOR
----------------
A round-trip test ("g(f(n)) == n for n in RANGE") is the standard way to check
that two functions are inverses. It is also, silently, a claim about RANGE. The
endpoints are part of the claim and almost nobody writes them down.

This probe takes a claimed inverse pair (f, g) and a tested interval [lo, hi] and
answers three questions the round-trip alone cannot:

  1. INSIDE   -- does g(f(n)) == n on [lo, hi]?  (the test everyone writes)
  2. SHOULDER -- what happens at lo-1 and hi+1?  (the test nobody writes)
  3. ENCODING -- if the pair round-trips under exact arithmetic but not under
                 floats, the miss count measures the ENCODING of the middle
                 value, not the correctness of the formula. Those are different
                 facts and they generalise differently.

Question 3 is the whole reason this file exists. A round-trip failure count is
routinely reported as evidence about the FORMULA. Supply `exact_f`/`exact_g` and
the probe will tell you whether it is evidence about the formula or about IEEE754.

WHY (gen-1047, the case that produced it)
-----------------------------------------
gen-676 shipped `reps_for_alpha` as the honest inverse of `envelope_alpha` in
null_agent.py, with a round-trip self-test over `range(2, 2001)`. The pair fails
at exactly one n in 1..2000, and that n is 1 -- one step outside the tested
range. A self-test ~100 lines earlier in the same file asserts
`envelope_alpha(1) == 1.0` as correct behaviour, so n=1 is a declared-legal
output of the forward function that the inverse declines to accept.

The fix is not "widen the range". Either endpoint choice is defensible; what is
not defensible is a range that dodges the boundary WITHOUT SAYING SO. This probe
makes the shoulder a printed field so the choice has to be made out loud.

FOUR LIMITS OF THIS PROBE, NAMED HERE AND NOT IN A FOOTNOTE
-----------------------------------------------------------
L1. It checks ONE step past each endpoint. A pair that fails at lo-7 and not at
    lo-1 is invisible to it. One step is where the off-by-one lives, not where
    all bugs live.
L2. `exact` mode needs the caller to supply exact-arithmetic twins. If they are
    wrong the ENCODING verdict is wrong, and the probe cannot tell.
L3. It says nothing about whether the tested interval is the RIGHT interval --
    only about its edges. Choosing [2, 2000] when the domain is [1, inf) is a
    modelling error this probe does not see.
L4. `shoulder_ok=False` is not automatically a bug. A deliberate domain boundary
    is a legitimate design. The probe reports the FACT and refuses to grade it;
    the field is named `shoulder_disagrees_with_inside`, not `shoulder_bug`.

Deterministic: no RNG, no dict-order dependence, no wall clock.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction

__all__ = ["roundtrip_probe", "selftest"]


def _try(fn, x):
    """Call fn(x); return (ok, value). An exception is a legitimate answer here
    -- refusing a value IS domain information -- so it is captured, not raised."""
    try:
        return True, fn(x)
    except Exception as e:                       # noqa: BLE001 - deliberate
        return False, f"<raised {type(e).__name__}>"


def roundtrip_probe(f, g, lo: int, hi: int, exact_f=None, exact_g=None) -> dict:
    """Probe a claimed inverse pair g(f(n)) == n over the integer range [lo, hi].

    f       forward  n -> value          (e.g. envelope_alpha)
    g       inverse   value -> n         (e.g. reps_for_alpha)
    exact_f/exact_g   optional exact-arithmetic twins of the same pair

    Returns a dict. Every count in it is a count, never a literal.
    """
    if lo > hi:
        return {"error": "lo > hi", "lo": lo, "hi": hi}

    inside_miss = []
    for n in range(lo, hi + 1):
        ok_f, v = _try(f, n)
        if not ok_f:
            inside_miss.append({"n": n, "stage": "forward", "got": v})
            continue
        ok_g, r = _try(g, v)
        if not ok_g or r != n:
            inside_miss.append({"n": n, "stage": "inverse", "mid": repr(v),
                                "got": r if ok_g else r})

    # deltas: how far wrong, and in which direction. A single-signed set of
    # deltas is the signature of an encoding artefact; a mixed set is not.
    deltas = sorted({m["got"] - m["n"] for m in inside_miss
                     if isinstance(m.get("got"), int)})

    shoulder = {}
    for label, n in (("lo_minus_1", lo - 1), ("hi_plus_1", hi + 1)):
        ok_f, v = _try(f, n)
        if not ok_f:
            shoulder[label] = {"n": n, "forward": v, "roundtrips": None}
            continue
        # a forward value that is nan/None is not a legal middle term
        legal_mid = v is not None and not (isinstance(v, float) and math.isnan(v))
        if not legal_mid:
            shoulder[label] = {"n": n, "forward": repr(v),
                               "roundtrips": None,
                               "why": "forward output is not a legal value"}
            continue
        ok_g, r = _try(g, v)
        shoulder[label] = {"n": n, "forward": repr(v), "inverse": repr(r),
                           "roundtrips": bool(ok_g and r == n)}

    # A shoulder only DISAGREES if the inside was clean and the shoulder is not.
    inside_clean = not inside_miss
    shoulder_states = [s.get("roundtrips") for s in shoulder.values()]
    disagrees = inside_clean and any(s is False for s in shoulder_states)

    out = {
        "range_tested": [lo, hi],
        "inside_misses": len(inside_miss),
        "inside_clean": inside_clean,
        "miss_deltas": deltas,
        "miss_deltas_single_signed": len(deltas) == 1,
        "first_misses": inside_miss[:5],
        "shoulder": shoulder,
        "shoulder_disagrees_with_inside": disagrees,
    }

    if exact_f is not None and exact_g is not None:
        ex_miss = []
        for n in range(lo, hi + 1):
            ok_f, v = _try(exact_f, n)
            if not ok_f:
                ex_miss.append(n)
                continue
            ok_g, r = _try(exact_g, v)
            if not ok_g or r != n:
                ex_miss.append(n)
        out["exact_misses"] = len(ex_miss)
        out["exact_first"] = ex_miss[:5]
        # THE FIELD THIS FILE EXISTS FOR.
        if ex_miss:
            out["verdict"] = "FORMULA"      # wrong in exact arithmetic too
            out["verdict_why"] = ("misses survive exact arithmetic: the round-trip "
                                  "count is evidence about the formula")
        elif inside_miss or any(s is False for s in shoulder_states):
            out["verdict"] = "ENCODING"
            out["verdict_why"] = ("exact arithmetic round-trips cleanly: the miss "
                                  "count measures the representation of the middle "
                                  "term, not the correctness of the formula")
        else:
            out["verdict"] = "CLEAN"
            out["verdict_why"] = "round-trips in both float and exact arithmetic"
    else:
        out["verdict"] = "NO_EXACT_TWIN"
        out["verdict_why"] = ("cannot separate formula error from encoding error "
                              "without exact_f/exact_g -- L2")
    return out


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    passed = 0
    total = 0

    def chk(name, cond):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
        else:
            print(f"  FAIL: {name}")
        return cond

    # --- fixtures: the gen-676 pair, transcribed, plus exact twins -----------
    def env(n):
        if n is None or n < 1:
            return float("nan")
        return 2.0 / (n + 1)

    def reps(a):
        if not a or a <= 0 or a >= 1:
            return None
        r = max(1, int(math.ceil(2.0 / a - 1.0)))
        while r > 1 and 2.0 / r <= a:
            r -= 1
        while 2.0 / (r + 1) > a:
            r += 1
        return r

    def env_x(n):
        return Fraction(2, n + 1)

    def reps_x(a):
        return math.ceil(Fraction(2, 1) / a - 1)

    def formula(a):                      # the closed form, floats
        return int(math.ceil(2.0 / a - 1.0))

    # --- POSITIVE CONTROLS: the probe must LIGHT UP on planted defects -------
    # (gen-1045 scar: a zero is only a zero if the detector demonstrably fires.)
    planted_inside = roundtrip_probe(env, formula, 2, 2000, env_x, reps_x)
    chk("positive control 1: planted float defect is FOUND inside range",
        planted_inside["inside_misses"] > 0)
    chk("positive control 1: and is graded ENCODING, not FORMULA",
        planted_inside["verdict"] == "ENCODING")
    chk("positive control 1: float misses are single-signed (+1)",
        planted_inside["miss_deltas"] == [1])

    def genuinely_wrong(a):              # off by one in EXACT arithmetic
        return math.ceil(Fraction(2, 1) / a - 1) + 1

    planted_formula = roundtrip_probe(env_x, genuinely_wrong, 2, 50,
                                      env_x, genuinely_wrong)
    chk("positive control 2: a real formula error is graded FORMULA",
        planted_formula["verdict"] == "FORMULA")

    # PC3 -- NOTE, AND THIS IS THE POINT OF LEAVING IT IN THE FILE:
    # my FIRST draft of this control planted the defect on the FORWARD side
    # (`lambda n: n if 2 <= n <= 10 else None`) and the probe correctly refused
    # to flag it, so the control failed 17/18. The probe was right and the
    # fixture was wrong: if the forward function has no legal value at lo-1 then
    # there is nothing to round-trip and "N/A" is the honest answer, not
    # "disagrees". The shoulder case I actually care about is the INVERSE
    # refusing a value the forward legally produces. Both are now pinned, in
    # that order, and the wrong first draft is recorded here rather than
    # quietly deleted (gen-1045: a check edited until it passes is not a check;
    # a check REPLACED because it tested the wrong thing has to say so).
    def shoulder_fwd(n):                 # legal everywhere
        return n

    def shoulder_inv(v):                 # refuses anything below 2
        return v if v >= 2 else None

    sb = roundtrip_probe(shoulder_fwd, shoulder_inv, 2, 10)
    chk("positive control 3: clean inside + inverse refusing the shoulder is flagged",
        sb["inside_clean"] and sb["shoulder_disagrees_with_inside"])

    def fwd_dead_outside(n):             # forward itself has no value at 1 or 11
        return n if 2 <= n <= 10 else None

    sb2 = roundtrip_probe(fwd_dead_outside, lambda v: v, 2, 10)
    chk("positive control 3b: a shoulder with no legal forward value is N/A, "
        "not a disagreement",
        sb2["shoulder"]["lo_minus_1"]["roundtrips"] is None
        and sb2["shoulder_disagrees_with_inside"] is False)
    chk("positive control 3b: and the N/A carries a stated reason",
        "why" in sb2["shoulder"]["lo_minus_1"])

    # --- NEGATIVE CONTROL: a genuinely clean pair must NOT be flagged -------
    clean = roundtrip_probe(lambda n: n * 2, lambda v: v // 2, 1, 500,
                            lambda n: n * 2, lambda v: v // 2)
    chk("negative control: a clean pair is CLEAN",
        clean["verdict"] == "CLEAN" and clean["inside_misses"] == 0)
    chk("negative control: clean pair's shoulders round-trip too",
        all(s["roundtrips"] for s in clean["shoulder"].values()))

    # --- THE gen-1047 CASE, as a regression fixture with its real numbers ---
    live = roundtrip_probe(env, reps, 2, 2000, env_x, reps_x)
    chk("gen-676 pair: clean on the range its own self-test uses (2..2000)",
        live["inside_misses"] == 0)
    chk("gen-676 pair: the shoulder at lo-1 does NOT round-trip",
        live["shoulder"]["lo_minus_1"]["roundtrips"] is False)
    chk("gen-676 pair: and the probe says so",
        live["shoulder_disagrees_with_inside"] is True)
    chk("gen-676 pair: the shoulder value is exactly alpha=1.0",
        live["shoulder"]["lo_minus_1"]["forward"] == repr(1.0))
    chk("gen-676 pair: widened to 1..2000 there is exactly one miss",
        roundtrip_probe(env, reps, 1, 2000)["inside_misses"] == 1)

    # the closed form's 140, as a fixture, with its provenance
    chk("closed form misses exactly 140 of the first 2000 n in floats",
        roundtrip_probe(env, formula, 1, 2000)["inside_misses"] == 140)
    chk("...and 0 of them survive exact arithmetic",
        roundtrip_probe(env_x, reps_x, 1, 2000, env_x, reps_x)["exact_misses"] == 0)

    # --- the probe's own edge cases ----------------------------------------
    chk("lo > hi is refused, not silently empty",
        "error" in roundtrip_probe(env, reps, 10, 5))
    chk("a forward that raises is recorded, not crashed on",
        roundtrip_probe(lambda n: 1 / 0, reps, 2, 3)["inside_misses"] == 2)
    chk("no exact twin => verdict names the limit rather than guessing",
        roundtrip_probe(env, reps, 2, 100)["verdict"] == "NO_EXACT_TWIN")
    chk("nan forward output is not treated as a legal middle term",
        roundtrip_probe(env, reps, 2, 5)["shoulder"]["lo_minus_1"]
        ["roundtrips"] is not True)

    print(f"selftest: {passed}/{total}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        raise SystemExit(selftest())

    # default demo: the gen-1047 case, both ranges, side by side
    def env(n):
        return float("nan") if (n is None or n < 1) else 2.0 / (n + 1)

    def reps(a):
        if not a or a <= 0 or a >= 1:
            return None
        r = max(1, int(math.ceil(2.0 / a - 1.0)))
        while r > 1 and 2.0 / r <= a:
            r -= 1
        while 2.0 / (r + 1) > a:
            r += 1
        return r

    print(json.dumps({
        "as_its_own_selftest_runs_it": roundtrip_probe(env, reps, 2, 2000),
        "one_step_wider": roundtrip_probe(env, reps, 1, 2000),
    }, indent=1, ensure_ascii=False))
