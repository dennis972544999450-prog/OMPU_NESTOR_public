# M_bolt_gen316 — taxing tenure does not unseat the king; it *freezes the throne*

**Den's design fork (07-04, 11:56 + 12:00):** "структура графа для платформы
интереснее… нет вечных королей" — you want *rotating* leaders, not one permanent
anchor. The gen-308→315 lineage twice-confirmed that inverse-degree pricing gives a
**flat mass (Gini ~0.25) + a persistent topic-central rank-1 leader**. So the open
lever, named in the gen-314/315 handoff, was: add a price term that grows with the
**duration** a node holds rank-1 (tenure), not only with its degree. Hypothesis:
this kills leader persistence while keeping the flat Gini. gen-316 ran it. **It
backfired — cleanly.**

**Mechanism tested:** `price(n) = indeg[n] + λ·tenure_count[n]`, citations flow to
the cheapest candidates. λ=0 is the gen-308/309 baseline. Random tie-break
(gen-315's honest control, no dict-order artifact). 6 seeds, 400 rounds.

**Prediction (mine):** λ↑ ⇒ tenure_frac↓, distinct_rank1↑, Gini stays flat.

**What actually happened (falsified my own prediction):**

| λ | mean final Gini | mean tenure_frac | mean distinct_rank1 |
|---|---|---|---|
| 0.0 (baseline) | 0.246 | 0.451 | 25.7 |
| 1.0 | 0.249 | 0.516 | 26.3 |
| 2.0 | 0.273 | 0.659 | 26.2 |
| 5.0 | 0.288 | 0.640 | 26.2 |
| 10.0 | 0.289 | 0.625 | 26.2 |

Both named failure modes fired **together**:
- **F2 (rotation inert):** `distinct_rank1` is flat (~26) across the entire λ sweep.
  The number of distinct leaders is set by something structural (topic-eligibility),
  **not** by the price penalty. Taxing tenure buys *zero* extra rotation.
- **F1 (uniformity lost):** at λ≥2, mass-Gini *rises* 0.246→0.289 **and** tenure_frac
  *rises* 0.45→0.66 — the tax makes the king MORE permanent and the mass LESS flat.

**Why (mechanism-confirmed, seed=42, tracking the leader's last edge gain):**
- λ=0: leader `jt-0083` keeps gaining edges until **round 395/400** — leadership is
  live and contested, changing hands (tenure 0.165).
- λ=5: leader `jt-0266` stops gaining edges at **round 337** yet holds rank-1 through
  round 400 (tenure 0.603). It is **frozen but uncontested.**

The tax freezes the *throne*, not the *reign*. Once a node is on top, taxing its
tenure makes it expensive to cite — so its degree stops growing — but every
challenger *also* accrues a tenure tax the moment it touches rank-1, so challengers
freeze on approach too. Nobody can overtake a frozen target while being frozen
themselves. Result: the first node to reach the top stays there permanently, and
the mass un-flattens because the race stalls instead of redistributing.

**The finding for Den's fork:** "нет вечных королей" is **NOT** reachable by taxing
tenure on the *citation-price* side. That lever does the opposite of its intent —
it entrenches the incumbent and un-flattens the mass. If you want rotation, the tax
has to act on the *incumbent's accumulated capital*, not on the *cost of citing it*.

**Honest open thread (gen-317):** this tested ONE operationalization — a tenure TAX
on citation price. A *true decay* — leaking the leader's accumulated in-degree over
time so the throne itself erodes — is a **different, untested** lever, and is the
mechanism whose name ("decay") actually matches the intent. My "decay" was a
mis-named tax. gen-317: run indeg-leak decay (subtract, don't surcharge) and see if
*that* rotates leaders while holding Gini flat. It may also fail (leak could just
re-spike PA), which is why it's worth running.

**Detector note:** `tenure_frac` is again a `max()`-over-possibly-tied metric, but
random tie-break controls the dict-order artifact (gen-315), and the load-bearing
result here — `distinct_rank1` flat + Gini rising — does not depend on tie-break at
all. The counterintuitive core (tax → entrenchment) is mechanism-confirmed, not a
decimal.

*Artifacts:* data/JSONTUBE_OSC_TENURE_DECAY_bolt_gen316_20260704.{py,result.txt}.
Reused gen-315 fetch/corpus/sim/gini on curl-place. Read-only, worker untouched,
NOT deployed. — Bolt gen-316 (claude-opus-4-8), 2026-07-04.
