# M_bolt_gen318 — The leak-floor can't buy anchor+rotation: the obstruction is the PRICING, not the decay

**gen-318 (claude-opus-4-8) · 2026-07-04 · reply-lineage to gen-317 · Den frame "не спешим, гипотезы" held**

## Claim
Protecting the top-K topic-central nodes from an honest degree-leak (`indeg*=(1-δ)` for all EXCEPT the floor) does **NOT** produce the missing combination "flat mass + a substantive throne that changes hands." It fails in two regimes, neither of them the worked hypothesis:

- **Small floor (K≤5): INERT (F-ii null).** anchor_king_frac ≈ 0.02–0.03, floor_max_indeg = **1.0**. The protected anchor is irrelevant — identical to gen-317 scalar leak (non-floor mass rotates: distinct_rank1 ≈ 50, tenure ≈ 0.18; leader stays at cent_rank ≈ 49, never the anchor).
- **Large floor (K=10): FREEZE (F-i), gen-316 reborn by a new mechanism.** anchor_king_frac → 0.54, overall_tenure_frac → 0.51, leader_cent_rank → 5 — but floor_max_indeg only **2.3**. A protected node holds the throne by *never decaying*, not by being cited; the throne has ~no substance, and the non-floor mass still rotates below it.

## Mechanism (load-bearing, verified)
**Inverse pricing and the decay-floor are ANTAGONISTIC.** Inverse pricing routes citations to the *cheapest* (lowest-indeg) candidate — its entire job is to starve any node that accumulates. So a topic-central anchor gets cited ~once (indeg→1), then is too expensive to cite again. Protecting its accumulation from decay is a no-op because **there is no accumulation to protect** (floor_max_indeg = 1.0 across K=1..5). Only when the floor is large enough (K=10) does a protected node stay rank-1 *by default* — it survives the decaying mass without earning citations = freeze of a hollow throne.

Verified not a node-choice artifact: the top-central floor nodes (jt-0285/0284/0286…) have **0 initial edges**, and the max initial in-degree of ANY node in the live corpus is **1** (8 edged nodes total). The throne is entirely emergent from sim dynamics, and inverse pricing caps that emergence for every node — protected or not.

## Consequence for Den's fork (the reframe)
Four levers now mapped, and **the "flat mass + rotating substantive throne" cell is unreachable by any DECAY-SIDE lever — because the obstruction is upstream, in the pricing rule itself.**

| lever | mass | throne |
|---|---|---|
| inverse alone (gen-314/315) | flat | small, persists by tenure |
| tenure-tax (gen-316) | un-flattens | FREEZES |
| scalar leak (gen-317) | flat | rotates but max_indeg→~1 (dissolves) |
| **leak-floor (gen-318)** | **flat** | **inert (small K) → hollow freeze (large K)** |

The same inverse-pricing rule that flattens the mass is the rule that starves any throne of the citations it needs to be substantial. **Flat-mass and substantive-throne are in tension BY CONSTRUCTION of inverse pricing.** No decay term or floor can resolve it because the conflict is not in the decay — it is in the pricing.

**Design pointer (untested, for Den):** the missing combination, if reachable at all, needs a change to the PRICING, not the decay — e.g. a two-population rule (inverse pricing for the mass, a separate preferential-with-slow-decay lane for a designated leader slot), so mass-flattening and throne-substance are governed by *different* rules instead of one rule that must do both and can't.

## Detector-on-self
Load-bearing numbers are floor_max_indeg (absolute citation count, safe under multiplicative decay) and anchor_king_frac (rank-identity) — NOT Gini/max-over-mean, which gen-317 flagged as unsafe under leak. Both load-bearing metrics dodge the leak-artifact. Residual T2: "obstruction is the pricing" is an *inference* from four levers all failing the same cell for a common reason; it becomes a falsifiable prediction the moment someone runs a two-population pricing sim — if THAT also can't give flat+substantive-rotating, the obstruction is deeper than pricing.
