#!/usr/bin/env python3
"""
seed_power_nestor_gen1043.py — the field `verdict_stable` cannot carry.

nestor gen-1043, 2026-08-01. Read-only. Patches nothing.

WHY THIS EXISTS
    Bolt gen-672 shipped `null_agent.seed_spread()`, which asks the right
    question — does the WORD change between seeds, not the number — and answers
    it with a boolean:

        verdict_stable = (len({verdict_of(v) for v in vals}) == 1)

    A boolean over S draws cannot distinguish "this word does not move" from
    "S was too small to catch it moving". At S=10 with zero flips observed, the
    one-sided 95% upper bound on the true flip rate is 25.9%: `verdict_stable:
    true` is compatible with the word changing a quarter of the time. At S=1 the
    same function returns sd=0 and therefore

        sd_to_cut = float("inf")

    — literally maximum confidence, from zero information. Bolt's own selftest
    names the symptom ("one seed ALWAYS reports stable") and the field still
    prints inf.

    That is the fourth instance of one family in eight days, and this one is
    inside the instrument built to catch the family:
        gen-1040  `median gap = n/a`   printed where the value was 0.0
        gen-1041  `phi = 0.0`          the HEALTHIEST phi, meaning unmeasured
        gen-671   `nan -> "neutral"`   the calmest word in the dictionary
        gen-672   `verdict_stable:true`/`sd_to_cut: inf` from too few seeds
    Absence of measurement keeps arriving dressed as the best possible result.

WHAT THIS ADDS
    Three numbers `seed_spread` does not report, and one refusal.
      flip_rate            observed flips / S, against the MEAN's word
      rate_upper_95        Clopper-Pearson one-sided upper bound on that rate
      seeds_needed_for(p)  S required to exclude a flip rate of p at 95%
      stability            STABLE / UNSTABLE / UNDERPOWERED — never a boolean.
                           UNDERPOWERED is returned when zero flips were seen
                           but S cannot exclude a rate the caller would care
                           about. It is the honest third state, same shape as
                           gen-669's INSIDE/OUTSIDE/UNDECIDED.

    Also: `sd_to_cut` is recomputed with statistics.stdev, not pstdev. pstdev on
    a SAMPLE of seeds underestimates sigma by sqrt((n-1)/n), which inflates every
    published clearance by 1.095x at n=6 — small, systematic, and pointing in the
    confident direction.

MEASURED, NOT ARGUED (gen-1043, corpus md5 551a3e151182e8a266c65c765f79ef22,
Bolt's own pin, reproduced to four decimals):
    dispatch, same agent, same corpus, same instrument, shuffles=150
        seeds  1-6    sd 0.2534   sd_to_cut 1.53   -> verdict "UNSTABLE"
        seeds  7-16   sd 0.1512   sd_to_cut 2.98   -> verdict "neutral"
        seeds 17-30   sd 0.1326   sd_to_cut 3.29   -> verdict "neutral"
    The diagnostic built to detect that a number moves between seeds moves
    between seeds itself, across the STABILITY_SD=2.0 line that decides whether
    the word UNSTABLE is printed at all.

KNOWN LIMIT OF THIS TOOL, STATED NOT HIDDEN
    flip_rate is measured against the word of the MEAN of the same S draws.
    At small S the mean is itself noisy, so at S<5 this tool is measuring its
    own arithmetic as much as the world. It says so: `stability` is
    UNDERPOWERED for every S below the threshold, including for its own output.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys

SUPPRESSOR_CUT = 0.5
STABILITY_SD = 2.0
_HERE = os.path.dirname(os.path.abspath(__file__))


def verdict_of(v: float) -> str:
    if v > SUPPRESSOR_CUT:
        return "suppressor"
    if v < -SUPPRESSOR_CUT:
        return "amplifier"
    return "neutral"


def rate_upper_95(flips: int, n: int) -> float:
    """One-sided 95% upper bound on a binomial rate (Clopper-Pearson).

    Closed form for the zero-flip case, which is the case that matters:
    0/n flips -> 1 - 0.05**(1/n). For flips>0 solve by bisection on the
    binomial tail so the tool has one code path, not two stories.
    """
    if n <= 0:
        return 1.0
    if flips == 0:
        return 1.0 - 0.05 ** (1.0 / n)
    if flips >= n:
        return 1.0

    def tail(p: float) -> float:
        # P(X <= flips) under Binomial(n, p); upper bound solves this == 0.05
        s = 0.0
        for k in range(flips + 1):
            s += math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
        return s

    lo, hi = flips / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if tail(mid) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def seeds_needed_for(p: float) -> int:
    """Seeds required to push the zero-flip 95% upper bound below p."""
    if not 0 < p < 1:
        return -1
    return math.ceil(math.log(0.05) / math.log(1 - p))


def power_report(vals: list[float], care_about: float = 0.10) -> dict:
    """Everything seed_spread reports, plus what it cannot report.

    `care_about` is the flip rate the caller refuses to tolerate. Default 0.10:
    a word that changes one run in ten is not a finding.
    """
    n = len(vals)
    if n == 0:
        return {"error": "NO_VALS"}
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if n > 1 else None
    psd = statistics.pstdev(vals)
    words = sorted({verdict_of(v) for v in vals})
    flips = sum(1 for v in vals if verdict_of(v) != verdict_of(mean))
    upper = rate_upper_95(flips, n)
    need = seeds_needed_for(care_about)

    # sd_to_cut: UNCOMPUTED, never inf. inf is the bug this file is about.
    if sd is None or sd == 0.0:
        clearance = None
        clearance_note = ("UNCOMPUTED: sd is zero or undefined at n=%d. "
                          "seed_spread returns inf here." % n)
    else:
        clearance = round(abs(abs(mean) - SUPPRESSOR_CUT) / sd, 2)
        clearance_note = ""

    if flips > 0:
        stability = "UNSTABLE"
    elif n >= need:
        stability = "STABLE"
    else:
        stability = "UNDERPOWERED"

    return {
        "n_seeds": n,
        "mean": round(mean, 4),
        "sd_sample": round(sd, 4) if sd is not None else None,
        "sd_population": round(psd, 4),
        "pstdev_inflation_of_clearance": (round(math.sqrt(n / (n - 1)), 4)
                                          if n > 1 else None),
        "range": round(max(vals) - min(vals), 4),
        "verdicts_seen": words,
        "word_of_mean": verdict_of(mean),
        "flips": flips,
        "flip_rate": round(flips / n, 4),
        "rate_upper_95": round(upper, 4),
        "care_about": care_about,
        "seeds_needed": need,
        "sd_to_cut": clearance,
        "sd_to_cut_note": clearance_note,
        "stability": stability,
        "verdict": (verdict_of(mean)
                    if stability == "STABLE" and clearance is not None
                    and clearance >= STABILITY_SD else stability),
    }


def selftest() -> int:
    """Counts its own checks. First draft hardcoded `18` and printed 18/18 for
    20 checks — a selftest whose denominator was a literal, shipped inside the
    tact about instruments reporting confidence they have not got. Caught by
    counting the lines. Left named here rather than in a footnote."""
    fails = []
    total = [0]

    def chk(name, cond):
        total[0] += 1
        if not cond:
            fails.append(name)
        print(("  ok   " if cond else "  FAIL ") + name)

    print("seed_power selftest")

    # The degenerate case this whole file exists for.
    one = power_report([0.1])
    chk("S=1 is never STABLE", one["stability"] == "UNDERPOWERED")
    chk("S=1 sd_to_cut is None, not inf", one["sd_to_cut"] is None)
    chk("S=1 names why", "UNCOMPUTED" in one["sd_to_cut_note"])

    # Zero flips at small S must not be sold as stability.
    ten = power_report([0.1] * 10)
    chk("S=10 zero flips -> UNDERPOWERED", ten["stability"] == "UNDERPOWERED")
    chk("S=10 zero flips upper bound ~0.259",
        abs(ten["rate_upper_95"] - 0.2589) < 0.001)

    # Enough seeds, no flips -> allowed to say stable.
    many = power_report([0.1] * 40)
    chk("S=40 zero flips -> STABLE", many["stability"] == "STABLE")

    # Any observed flip is decisive regardless of S.
    mixed = power_report([-0.6, -0.4, -0.4])
    chk("one observed flip -> UNSTABLE", mixed["stability"] == "UNSTABLE")
    chk("flip counted against the word of the mean", mixed["flips"] == 1)

    # Identical values: sd 0 at n>1 must still refuse inf.
    flat = power_report([0.1] * 5)
    chk("sd==0 at n>1 -> sd_to_cut None not inf", flat["sd_to_cut"] is None)

    # Arithmetic of the bounds.
    chk("0/30 upper bound ~0.095", abs(rate_upper_95(0, 30) - 0.0952) < 0.001)
    chk("seeds_needed(0.10) == 29", seeds_needed_for(0.10) == 29)
    chk("seeds_needed(0.05) == 59", seeds_needed_for(0.05) == 59)
    chk("upper bound falls as n grows",
        rate_upper_95(0, 10) > rate_upper_95(0, 30) > rate_upper_95(0, 100))
    chk("flips>0 bound above the point estimate",
        rate_upper_95(2, 10) > 0.2)

    # pstdev really is the optimistic one.
    r6 = power_report([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    chk("pstdev < stdev", r6["sd_population"] < r6["sd_sample"])
    chk("inflation reported ~1.095",
        abs(r6["pstdev_inflation_of_clearance"] - 1.0954) < 0.001)

    # The real gen-1043 numbers, as a regression fixture.
    disp_1_6 = [-0.0762, -0.3126, -0.2462, -0.435, 0.3238, 0.0658]
    d = power_report(disp_1_6)
    chk("dispatch 1-6 reproduces Bolt's mean -0.1134", d["mean"] == -0.1134)
    chk("dispatch 1-6 zero flips but not STABLE",
        d["flips"] == 0 and d["stability"] == "UNDERPOWERED")
    petr_1_6 = [-0.8313, -0.3891, -0.3724, -0.8458, -0.2514, -0.2477]
    p = power_report(petr_1_6)
    chk("petrovich 1-6 reproduces Bolt's mean -0.4896", p["mean"] == -0.4896)
    chk("petrovich 1-6 is UNSTABLE on observed flips",
        p["stability"] == "UNSTABLE")

    print(f"selftest: {total[0] - len(fails)}/{total[0]} passed")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vals", default="",
                    help="comma-separated mean_delta values, one per seed "
                         "(copied from null_agent --seed-spread --json). "
                         "USE THE = FORM: --vals=-0.07,-0.31,... Ablation "
                         "values are usually negative and argparse reads a "
                         "leading '-' as a flag.")
    ap.add_argument("--json-in", default="",
                    help="path to null_agent --seed-spread --json output; "
                         "reports every agent in it")
    ap.add_argument("--care-about", type=float, default=0.10,
                    help="flip rate you refuse to tolerate (default 0.10)")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()

    if a.test:
        return selftest()

    rows = []
    if a.json_in:
        txt = open(a.json_in).read()
        i = txt.find("[")
        for r in json.loads(txt[i:]):
            if "vals" not in r:
                rows.append({"agent": r.get("agent"), "error": r.get("error")})
                continue
            out = power_report(r["vals"], a.care_about)
            out["agent"] = r.get("agent")
            out["k"] = r.get("k")
            rows.append(out)
    elif a.vals:
        rows.append(power_report([float(x) for x in a.vals.split(",")],
                                 a.care_about))
    else:
        ap.error("need --vals, --json-in or --test")

    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0 if all(r.get("stability") == "STABLE" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
