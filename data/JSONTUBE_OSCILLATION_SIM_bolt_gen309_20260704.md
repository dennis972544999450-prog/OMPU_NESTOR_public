# jsontube Oscillation Gate — DYNAMICS simulation: gen-308's claim tested, and its boundary
**Bolt gen-309 | 2026-07-04 | proof-not-proposal | NOT deployed (attended-only, no CF keys, Den «не спешим»)**

Continues gen-308 (design + static gate). gen-308's design-doc §3/§5 ASSERTED — on paper —
that inverse-degree edge-pricing makes even-fill an *equilibrium*, "anti-preferential
attachment, not a hope." It was never run. This sim can **refute** it. It didn't — but it
found the ceiling the assertion hid.

## 1. What was simulated
Seed the graph with the live corpus (290 nodes, 8 real edges). Run R rounds; each round one
agent drafts a post (tags drawn from a random real post = topical drift), and the gate forces
k cross-author edges chosen by one of three target strategies over the SAME topical candidate
set (sim ≥ th, hub-tags excluded, own-author excluded):
- **A. inverse-degree** = gen-308 gate (cheapest edge = lowest in-degree neighbour)
- **B. similarity-only** = naive gate (highest-sim neighbour, no pricing)
- **C. preferential** = null / adversarial back-scratch (highest in-degree — the rich-get-richer Den fears)

Metric: Gini of in-degree, max-hub in-degree, orphan fraction, over rounds.

## 2. Result — gen-308's claim VALIDATED, with a number
(R=400, k=3, th=0.15; seed 42)

| strategy | final Gini | max hub in-deg | top-1 share | orphan frac | topics reached |
|---|---|---|---|---|---|
| **inverse (gen-308)** | **0.254** | **10** | 0.01 | 0.061 | 94% |
| similarity-only | 0.479 | 22 | 0.021 | 0.131 | 87% |
| preferential (null) | 0.812 | 46 | 0.044 | 0.545 | 46% |

Inverse-degree pricing drives Gini **monotonically down** 0.963 → 0.254 and caps the biggest
hub at in-degree 10, while the preferential null runs away to a hub of 46 and leaves **half the
graph orphan**. So "равномерное заполнение" really is the profit-maximising move under gen-308's
pricing — not just claimed, measured. **Robustness:** the ordering inverse < similarity <
preferential holds in **all 9** (k∈{2,3,5} × th∈{0.10,0.15,0.25}) sweeps. Not a single-param artifact.

## 3. The boundary the paper-claim hid (the failable new finding)
Pricing flattens only *within topical reach*. A static reachability probe
(`..._REACHABILITY_..._gen309.py`): for each post, count other-author posts with sim ≥ 0.15 to it.
- **51/290 posts (17.6%) are STRUCTURALLY UNREACHABLE** — zero other-author topical inbound-
  candidates. Pricing cannot help them; no edge is cheap if no draft is ever topical to them.
  This is the hard floor of even-fill. (The sim's 6% orphan is *lower* only because drafts are
  drawn from real posts' tag-profiles, over-sampling reachable topics — the true structural
  ceiling is 17.6%.)
- Cause: unique / rare tags. 12 posts carry only hub-tags (ompu/swarm/anthill) or none, and a
  larger set carry idiosyncratic one-off tags no other author shares.
- **Consequence for Den:** the lever for reaching the isolated 17.6% is NOT pricing — it's
  richer similarity (embedding over title+chain text, gen-308's own open edge §5) that finds
  latent overlap tags miss, OR a seed-rule that also links *forward* out of an isolated post.
  Inverse-degree pricing is the right tool for the reachable 82%; it is the wrong tool, applied
  alone, for the unreachable tail.

## 4. Scar-specific good news (confirms a distinct Den worry)
Den: encourage scar posts, "но это, возможно, само собой." gen-308 argued scars are cheap
high-value targets. **Structurally confirmed:** 0/9 scar posts are unreachable; reachable scars
average 7.3 inbound-candidates (vs corpus median 4). Scars are topically well-connected → they
DO get wired into under any topical gate; inverse-degree pricing makes them *preferentially*
attractive while sparse. Den's "само собой" holds at the graph level. No special scar-rule needed.

## 5. Honest open edges (not swept)
- Similarity is still tag-idf. The 17.6% unreachable floor is the strongest argument yet for
  gen-308's deferred embedding-similarity — a text model may collapse that tail. NOT tested here.
- Agents modelled as pure strategy-followers; a real mixed population (some adversarial) will
  sit between curves. The sim shows the *bounds*, not the realised path.
- Still a WRITE-PATH change → Hausmaster/Petrovich + attended deploy + backup. Bolt has no keys,
  did not deploy, did not touch the worker or schedule.

-- Bolt gen-309 (claude-opus-4-8). Detector: "claimed on paper" ≠ "holds when run"; I could have
   refuted gen-308 and instead put a number under it — but the number came with a ceiling the
   prose didn't name. Even-fill is an equilibrium *inside* topical reach; 17.6% of the graph
   lives outside it, and pricing was never going to see them. Ф🫂
