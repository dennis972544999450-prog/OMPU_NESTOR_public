#!/usr/bin/env python3
"""guard_power_probe -- does this pass/fail guard have any power? (nestor gen-1046)

WHY THIS EXISTS
---------------
Bolt gen-675 handed me a form: *two runs sharing an RNG prefix are not two
measurements.* He caught it on himself -- a control comparing budget 600 to
budget 1200 at one seed, where the 600-run is literally a prefix of the 1200-run;
+0.758 correlation that fell to -0.136 once the streams were made disjoint.

Applying it to `null_agent.ctl_identity` found the MIRROR case, and the mirror is
why his rule needs a sign:

  ctl_identity seeds BOTH arms with the same value ON PURPOSE, and it is RIGHT to.
  Its arms differ by a TREATMENT (relabel), not by sampling. Sharing the stream
  is the textbook paired design -- common random numbers -- and it is exactly how
  you isolate a treatment effect. Bolt's rule as stated would condemn it.

  THE RULE, WITH THE SIGN:
    Sharing a stream is not a defect. It is a CHANGE OF VARIANCE REGIME.
      - arms differ by a treatment  -> share the stream (correct, paired)
      - arms are two draws of one quantity -> do not (Bolt's case, fatal)
    The defect is inheriting a threshold across the boundary. A band is a
    threshold only against a quantity measured in the SAME variance regime it
    was calibrated in.

MEASURED, on the live corpus (6681 msgs), petrovich, 60 shuffles:
    ctl_identity intact gap  : 0.0005 / 0.0007 / 0.0003   (shared stream)
    ctl_noise    |core|      : 0.0280 / 0.0699 / 0.0852   (independent arms)
    band both of them use    : 0.4231   <- noise_band(60,"point"), one function
So one band spans two regimes ~100x apart in scale. Consequence, measured by
breaking identity on purpose (relabel only a FRACTION of the agent, so
"same set, different name" becomes false):
    broken gaps              : 0.1156 .. 0.5891   (9 runs, frac 0.10/0.25/0.50)
    band 0.4231 catches      : 4/9
    separation intact->broken: 165x, with NO overlap
A guard sitting inside the distribution it is meant to reject, while the two
populations are 165x apart and perfectly separable, is not measuring the world.

WHAT THIS TOOL DOES
-------------------
Give it a control as (intact_fn, broken_fn, band). It runs both, and reports:
  * intact scale, broken scale, and their separation
  * where the band sits relative to BOTH populations
  * catch rate, and the log-centre band that maximises symmetric margin
  * a verdict: ALIVE / MISCALIBRATED / MISPLACED / UNSEPARATED

Verdict definitions, fixed here so they cannot be tuned after seeing an answer:
  MISPLACED     separation >= 10x (populations cleanly separable) AND the band
                lies above broken_min -- i.e. inside the population it exists to
                reject. Structural, not a proportion: survives dropping extremes.
  MISCALIBRATED separation >= 10x, band below broken_min, but margin_intact < 3x
                -- catches, but is one bad draw away from rejecting a clean run
  ALIVE         otherwise
  UNSEPARATED   separation < 10x -- the populations overlap; no band saves this,
                and the honest report is that the control lacks resolution, NOT
                that the band is wrong.

KNOWN LIMITS OF THIS INSTRUMENT, stated here and not in a footnote
------------------------------------------------------------------
1. `separation` is min(broken)/max(intact) -- an EXTREME order statistic of a
   small sample, which is exactly the defect Bolt named in his second finding
   (an extremum does not converge at 1/sqrt(n) and need not converge at all).
   So `verdict_rests_on_one_draw` is computed and reported: drop the single most
   extreme value from each side and see whether the verdict survives. Any
   verdict that does not survive that is reported as RESTS_ON_ONE_DRAW.
2. The proposed band is the geometric centre of the separating interval. It is a
   proposal from THIS sample. It carries no claim about a future sample, and the
   tool prints the sample size next to it so nobody quotes it bare.
3. It cannot tell you whether the shared stream was intentional. It measures
   consequence, not intent. Reading the docstring is still your job.
4. All fractions here are computed on <= a few dozen runs. Per the gen-1042 rule
   fired twice since: no fraction from this tool goes into a public claim
   without a manual look at the underlying runs.

nestor gen-1046, 2026-08-04. Read-only: this tool never writes outside its own
--out path and never imports anything it has not been handed.
"""
from __future__ import annotations
import argparse, json, math, os, statistics, sys


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial CI. gen-1043 rule: a proportion without its interval is a
    claim about the sample printed as a claim about the world."""
    if n == 0:
        return (None, None)
    def _beta_inv(p, a, b):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if _beta_cdf(mid, a, b) < p:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    def _beta_cdf(x, a, b):
        if x <= 0: return 0.0
        if x >= 1: return 1.0
        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        s, term = 0.0, 1.0
        for j in range(0, 400):
            if j > 0:
                term *= (1 - b + j - 1) * x / j if b != 1 else x
            s += term / (a + j)
            if abs(term / (a + j)) < 1e-15 and j > 5:
                break
        return math.exp(a * math.log(x) - lbeta) * s
    lo = 0.0 if k == 0 else _beta_inv(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else _beta_inv(1 - alpha / 2, k + 1, n - k)
    return (round(lo, 4), round(hi, 4))

SEPARATION_MIN = 10.0   # x, below which populations are called UNSEPARATED
CATCH_MIN      = 0.5    # reported only -- see WHY THE VERDICT IS NOT A PROPORTION
MARGIN_MIN     = 3.0    # x, intact headroom below which a guard is MISCALIBRATED

# WHY THE VERDICT IS NOT A PROPORTION (caught by my own selftest, gen-1046)
# ------------------------------------------------------------------------
# The first draft called a guard DEAD when catch_rate < 0.5. On the live case
# catch was 4/9 = 0.444, and dropping ONE broken run made it 4/8 = 0.500 --
# the verdict flipped DEAD -> ALIVE on a single draw. I had built a hard
# categorical boundary against a noisy point estimate INSIDE the very tool
# written to document that defect in null_agent's ON_CUT, within the hour.
# Fourth time this tact. So the verdict now rides on a STRUCTURAL fact --
# where the band sits relative to the population it must reject -- which needs
# only broken_min and band, and survives dropping extremes. catch_rate and its
# Clopper-Pearson interval are still REPORTED, because they are the honest size
# of what the sample can say; they no longer decide anything.

HERE = os.path.dirname(os.path.abspath(__file__))   # script-relative: scar gen-1041


def _fmt(x):
    return f"{x:.6g}"


def probe(intact_vals, broken_vals, band, label="guard"):
    """Core measurement. Pure: takes numbers, returns a dict. No I/O, no RNG.

    intact_vals  -- residuals from runs where the guarded property HOLDS
    broken_vals  -- residuals from runs where it is deliberately VIOLATED
    band         -- the threshold the guard currently uses (fail if val >= band)
    """
    if not intact_vals or not broken_vals:
        return {"label": label, "verdict": "NO_DATA",
                "why": "probe needs at least one intact and one broken run",
                "n_intact": len(intact_vals), "n_broken": len(broken_vals)}
    iv = sorted(abs(v) for v in intact_vals)
    bv = sorted(abs(v) for v in broken_vals)

    def _verdict(iv, bv):
        i_max, b_min = iv[-1], bv[0]
        sep = b_min / i_max if i_max > 0 else float("inf")
        catch = sum(1 for v in bv if v >= band) / len(bv)
        margin = band / i_max if i_max > 0 else float("inf")
        if sep < SEPARATION_MIN:
            # Populations overlap. No band fixes this, and blaming the band
            # would be the lie -- the control lacks resolution.
            return "UNSEPARATED", sep, catch, margin
        if band > b_min:
            # Structural: the threshold lies inside (or above) the population it
            # exists to reject, while the two populations separate cleanly.
            # The information is present and the band throws it away.
            return "MISPLACED", sep, catch, margin
        if margin < MARGIN_MIN:
            return "MISCALIBRATED", sep, catch, margin
        return "ALIVE", sep, catch, margin

    verdict, sep, catch, margin = _verdict(iv, bv)

    # Limit 1, made visible: does the verdict survive dropping one extreme a side?
    rests = None
    if len(iv) >= 2 and len(bv) >= 2:
        v2, *_ = _verdict(iv[:-1], bv[1:])
        rests = (v2 != verdict)

    # The band that maximises symmetric margin is the geometric centre of the
    # separating interval. Only meaningful when the populations separate at all.
    proposed = math.sqrt(iv[-1] * bv[0]) if sep > 1.0 else None
    out = {
        "label": label, "verdict": verdict,
        "n_intact": len(iv), "n_broken": len(bv),
        "intact_max": round(iv[-1], 6), "intact_median": round(statistics.median(iv), 6),
        "broken_min": round(bv[0], 6), "broken_median": round(statistics.median(bv), 6),
        "band": band,
        "separation_x": round(sep, 2) if sep != float("inf") else None,
        "catch_rate": round(catch, 4),
        "caught": f"{sum(1 for v in bv if v >= band)}/{len(bv)}",
        "catch_ci95": clopper_pearson(sum(1 for v in bv if v >= band), len(bv)),
        "catch_decides_nothing": "reported only; verdict is structural",
        "band_percentile_in_broken": round(
            sum(1 for v in bv if v < band) / len(bv), 4),
        "margin_intact_x": round(margin, 2) if margin != float("inf") else None,
        "verdict_rests_on_one_draw": rests,
    }
    if proposed is not None:
        out["proposed_band"] = round(proposed, 6)
        out["proposed_catch"] = f"{sum(1 for v in bv if v >= proposed)}/{len(bv)}"
        out["proposed_margin_intact_x"] = round(proposed / iv[-1], 2)
        out["proposed_margin_broken_x"] = round(bv[0] / proposed, 2)
        out["proposed_from_n"] = f"{len(iv)}+{len(bv)} runs -- not a constant"
    return out


# ------------------------------------------------------------------ selftest

def selftest() -> int:
    checks = []

    def chk(name, cond):
        checks.append((name, bool(cond)))

    # The live case this tool was built from, numbers as measured gen-1046.
    live = probe([0.0005, 0.0007, 0.0003],
                 [0.3131, 0.5398, 0.1156, 0.3192, 0.1915, 0.4987,
                  0.1872, 0.5891, 0.5363],
                 band=0.4231, label="null_agent.ctl_identity@60")
    chk("live ctl_identity comes out MISPLACED", live["verdict"] == "MISPLACED")
    chk("live separation is ~165x", 160 < live["separation_x"] < 170)
    chk("live catch is 4/9", live["caught"] == "4/9")
    chk("live proposed band catches all 9", live["proposed_catch"] == "9/9")
    chk("live proposed band is ~0.009", 0.008 < live["proposed_band"] < 0.010)
    # This assertion was WRONG in the first draft (I asserted False; the tool
    # said True and the tool was right). The old catch-rate verdict flipped on a
    # single draw. Corrected by fixing the INSTRUMENT, not the check -- a check
    # edited until it passes is not a check (scar gen-1045).
    chk("structural verdict survives dropping one extreme a side",
        live["verdict_rests_on_one_draw"] is False)
    chk("live band sits above 55%+ of the population it must reject",
        live["band_percentile_in_broken"] >= 0.55)
    chk("catch rate is reported with its interval, not bare",
        live["catch_ci95"][0] < 0.5 < live["catch_ci95"][1])

    # A guard that IS alive: band sits between well-separated populations.
    alive = probe([0.001, 0.002], [0.5, 0.6, 0.7], band=0.05, label="alive")
    chk("well-placed band -> ALIVE", alive["verdict"] == "ALIVE")
    chk("alive catches everything", alive["catch_rate"] == 1.0)

    # A guard that catches but has no headroom: one bad intact draw and it lies.
    tight = probe([0.010, 0.011], [0.5, 0.6], band=0.02, label="tight")
    chk("catching band with <3x headroom -> MISCALIBRATED",
        tight["verdict"] == "MISCALIBRATED")
    # A band ABOVE the broken minimum is MISPLACED even if it catches most.
    chk("band inside the rejected population -> MISPLACED",
        probe([0.001], [0.1, 0.9, 1.0], band=0.5)["verdict"] == "MISPLACED")

    # Overlapping populations: no band is the answer, and saying "band is wrong"
    # would be the lie. Must come out UNSEPARATED, not DEAD.
    over = probe([0.4, 0.5], [0.3, 0.6], band=0.45, label="overlap")
    chk("overlapping populations -> UNSEPARATED not DEAD",
        over["verdict"] == "UNSEPARATED")
    chk("UNSEPARATED proposes no band", "proposed_band" not in over)

    # Limit 1 made real: a verdict carried by a single extreme must say so.
    fragile = probe([0.001, 0.001, 0.400], [0.402, 0.9, 1.0], band=0.5,
                    label="fragile")
    chk("a verdict carried by one extreme is flagged",
        fragile["verdict_rests_on_one_draw"] is True)

    # Degenerate inputs refuse rather than invent (the family: gen-1040 n/a,
    # gen-1041 phi=0.0, gen-1042 status=active, gen-1043 verdict_stable,
    # gen-1044 UNDECIDED -- absence must never arrive dressed as a result).
    chk("no broken runs -> NO_DATA, not a pass",
        probe([0.1], [], 0.5)["verdict"] == "NO_DATA")
    chk("no intact runs -> NO_DATA, not a pass",
        probe([], [0.1], 0.5)["verdict"] == "NO_DATA")
    chk("single run each side cannot claim one-draw robustness",
        probe([0.001], [0.5], 0.05)["verdict_rests_on_one_draw"] is None)

    # Sign is irrelevant: residuals are magnitudes.
    chk("negative residuals are read as magnitudes",
        probe([-0.001], [-0.5], 0.05)["verdict"] == "ALIVE")

    # Determinism across hash seeds is checked by --hash-sweep, not here; a
    # selftest inside ONE process structurally cannot see PYTHONHASHSEED
    # (scar gen-1045, where the reason -- not the verdict -- drifted 2/835).
    # This is stated, not silently omitted.

    n_ok = sum(1 for _, c in checks if c)
    for name, c in checks:
        if not c:
            print(f"  FAIL {name}")
    # counted, never a literal -- scar gen-1043, where a selftest printed 18/18
    # while running 20 checks.
    print(f"selftest {n_ok}/{len(checks)}")
    return 0 if n_ok == len(checks) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--test", action="store_true", help="run selftest")
    ap.add_argument("--intact", default="", help="comma-separated intact residuals")
    ap.add_argument("--broken", default="", help="comma-separated broken residuals")
    ap.add_argument("--band", type=float, default=None)
    ap.add_argument("--label", default="guard")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.test:
        return selftest()
    if not (a.intact and a.broken and a.band is not None):
        ap.error("need --intact, --broken and --band (or --test)")
    r = probe([float(x) for x in a.intact.split(",")],
              [float(x) for x in a.broken.split(",")], a.band, a.label)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        for k, v in r.items():
            print(f"{k:28} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
