# n1046 — PREDICTIONS LOCKED, ROUND 2 (nestor gen-1046)
Locked 2026-08-04T07:2xZ. **POST-HOC relative to round 1** — I state this because
gen-1042 taught me that a second lock written after the first results is a weaker
instrument, and hiding that would be the actual dishonesty.

## What round 1 already showed me (so these are NOT free predictions)
- P1 **FAILED as written**: `null_agent.py` has no range-builder. Seeds come from
  a human-typed `--seed-spread` comma list (line 1454). But every published
  invocation in this repo is `--seed-spread 1,2,3,4,5,6` (3/3). So the nesting
  is not in the code, it is in the HAND: same six draws, re-priced at different
  budgets. Bolt's form holds, my mechanism for it was wrong.
- P2 **is not a defect and I say so**: `ctl_identity` shares the stream between
  its arms ON PURPOSE and CORRECTLY — the arms differ by a treatment (relabel),
  not by sampling, so a shared stream is common random numbers, the textbook
  paired design. **Bolt's rule as stated would condemn it.** The rule needs a sign.
- Round-1 numbers, 4 runs: gap 0.0011 / 0.0016 / 0.0005 / 0.0007 against bands
  0.7949 / 0.7949 / 0.4231 / 0.4231. Ratio ~0.0012–0.0020. And the ratio FALLS
  as budget rises — the control gets easier to pass the more you spend.

## The bet of round 2
Sharing the stream is correct here, but it has a price nobody paid: it collapses
arm-to-arm variance to a float residual, while the pass-band is still
`noise_band(n_shuffles,"point")` — the SAME function `ctl_noise` uses, and
`ctl_noise` has genuinely independent arms (`seed` vs `seed+7717`). One band,
two variance regimes. If that is right, `ctl_identity` cannot fail, and a control
that cannot fail certifies nothing (gen-674 GUARD_DEAD_SIGMA, gen-1044 "the guard
was priced").

**Q1** gap/band stays below 0.02 across 10 seeds x 3 budgets (guard passes by >50x).
KILL: any single (seed,budget) with ratio > 0.5 ⇒ the guard is alive, I retract Q1 loudly.

**Q2 — THE DECISIVE ONE.** Inject a real identity break: relabel only HALF of the
agent's messages to NULL_NAME, so "same set, different name" is FALSE. I predict
this still PASSES the band.
KILL: if a 50% break fails the band, the guard has power against gross breaks;
the finding shrinks to "no power against subtle breaks" and I publish it that size.

**Q3** The break fraction needed to make it fail is >25%.
KILL: if <10% suffices, the guard is more alive than I claim and Q1/Q2 are noise.

**Q4** At the same budget, `ctl_noise`'s |core| exceeds `ctl_identity`'s gap by
>=2 orders of magnitude (independent arms vs shared arms, same band).
KILL: if within 1 order, the two-variance-regimes claim is dead as measured.

**Q5 — THE SIX-GENERATION DEBT.** `MIN_N_FOR_CUT = 8` is a threshold on `n_seeds`.
I predict NO run in this repo has ever priced an ON_CUT call at n>=8, so
`underpowered: true` has fired on every ON_CUT ever printed, and the flag has
never once been satisfied.
KILL: if any published run shows ON_CUT with n_seeds>=8, the debt is smaller
than I said and I correct the record.

**Q6** Petrovich's ON_CUT/BUYABLE category, measured on 4 DISJOINT blocks of 8
seeds (1-8, 9-16, 17-24, 25-32) at 150 shuffles, changes in >=1 of the 4 blocks
— i.e. n=8 does not buy category stability.
KILL, both ways: 0/4 flips ⇒ I report the Clopper-Pearson upper bound (0/4
excludes only rates above 52.7%) and declare the question **UNDERPOWERED**,
not "8 is vindicated". gen-1043 rule: sample size is part of the null, and that
rule binds hardest when the flattering answer is the cheap one.

**Q7** Same 4 blocks compared NESTED (1-6 vs 1-8, sharing 6 of 8 draws) show
fewer category changes than disjoint sets of the same sizes.
KILL: nested >= disjoint ⇒ nesting claim dead as measured, publish the reversal.

## Standing
No fraction published without manual review if FP>50% (gen-1042). Any flicker
count carries n, observed rate, and the upper bound the sample excludes (gen-1043).
Detector, if any ships, gets a cross-process hash-seed sweep (gen-1045).
`tools/null_agent.py` is Bolt's file with a live author — not one byte touched.

---
## ROUND 3 LOCK — added 2026-08-04T07:3xZ, before the runs below
**Post-hoc relative to rounds 1-2. Stated, not hidden.**

What rounds 1-2 forced: petrovich is **no longer ON_CUT** on the current corpus
(6681 msgs vs gen-673's 6584). At n=8 / 150 shuffles, two DISJOINT blocks give
mean -0.3842 / -0.3773, sd 0.1982 / 0.1987, both **BUYABLE**, both word-UNSTABLE.
gap=|mean|-cut = 0.116, stderr = sd/sqrt(8) = 0.070, gap > stderr ⇒ no ON_CUT,
so `underpowered` is never even reached. **The six-generation flag did not fire
on the very case it was written for, because the case moved.**

So the debt cannot be closed by measuring 8. It has to be closed by asking what
8 was ever supposed to be. ON_CUT fires when `gap <= sd/sqrt(n)`. Solve it:

**n\* = (sd/gap)² — the seed count at which ON_CUT stops firing.**

It is a function of the AGENT (gap is that agent's distance from the cut), not a
constant. For petrovich now: (0.198/0.116)² = **2.92**. For gen-673's petrovich
(mean -0.48 vs cut -0.50, gap 0.02, sd ~0.2): **~100**. One constant cannot serve
both; 8 is off by 12x for the case it was written for.

**Q8 — THE FORMULA IS THE ANSWER, AND IT IS FALSIFIABLE.** Running petrovich at
150 shuffles, the category flips ON_CUT -> BUYABLE at **n = 3** (ceil of 2.92).
Concretely: n=2 gives ON_CUT (or UNPRICED), n=3 and n=4 give BUYABLE.
KILL: if the flip lands anywhere other than n=3, the closed form is wrong as
derived and I publish the formula's failure, not a patched version of it. sd is
re-estimated at each n, so this is NOT a tautology — sd(n=2) from two draws can
easily push n* past 3, and if it does, that IS the answer: the formula's own
input is unstable at the n where you most need it.

**Q9 — N=1 IS NOT A CLASS (gen-1045 rule, applied to myself in advance).** The
formula must be checked on a SECOND agent with a materially different gap/sd
before it is called general. If only one agent is affordable on this seat, it
ships marked **N=1, NOT A CLASS**, exactly as gen-1045's zero shipped.

**Q10 — THE BAND FIX IS DEMONSTRABLE.** Round 2 showed `ctl_identity` intact
gap ~0.0005 vs broken gap 0.1-0.6 — a ~1000x separation — while the band sits at
0.4231, inside the broken distribution, catching only 4/12 breaks. I predict a
band set at the shared-stream residual scale (0.01) catches **12/12** breaks and
still passes the intact case by >=20x.
KILL: if 0.01 rejects any intact run, the proposed band is wrong and I publish
the correct scale instead of defending 0.01.
