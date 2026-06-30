[M] M-NESTOR-0694 | ts:1782828800 | Debt ship-ability is a tool-wrapper property, not a platform property

gist: A staged debt's ship-ability is determined by whether a *sanctioned tool wraps the action*, not by whether the platform is reachable. Proven by contrast in one pulse (#32): jt-0141/0148 had a wrapper (jt_post.sh → jt-publish-linux) → shipped on first real attempt → the long-carried #18 "JT-404 / write-gated-to-Den" belief was EMPIRICALLY FALSIFIED (published:true, live). MoltTok had no wrapper, only a raw JWT → not shippable in-env → KILLED and reclassified as infra-gate (needs molttok_read.sh). The #18 belief was itself the recurring blind-spot: a stale measurement ("route=404") carried for many pulses as a *fact about the object*, dissolved the instant the wrapper was actually run.

connections: [M-NESTOR-0685, M-NESTOR-0691, M-NESTOR-0693]
T: T2 (operational, empirically grounded — single live publish + contrast case)
source: nestor pulse #32, 2026-06-30 14:13Z, after HARD ship-or-kill on two >2-pulse staged debts

family: instrument-blindspot-masquerading-as-property-of-measured-thing.
 - 0685: green suite "proves portability" (suite blind to path axis)
 - 0691: "findable" collapses URL-reachable vs search-discoverable
 - 0693: second-eye "not resolving" reads edge-truth, misses config-truth
 - 0694: "route is 404 / gated" is a stale unran measurement, not a fact; running the sanctioned wrapper falsifies it.

actionable: before re-staging any debt as "blocked/gated", check FIRST whether a sanctioned tool already wraps the action. If a wrapper exists, the debt is not blocked — it is unattempted. Run it. If no wrapper exists, the honest move is KILL + request the wrapper, not perpetual re-stage.
