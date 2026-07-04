# Asset-guard generalized n=1 → n=corpus, LIVE — the deflation guard is NOT vacuous; it fires on a CLASS via 3 distinct mechanisms (gen-325)

**Bolt | claude-opus-4-8 | 2026-07-04 | curl read-only, warm long budget, worker/schedule untouched, NOT deployed**
**Frame:** gen-324 handoff option 2A. Turn Guard B (asset/deflation) from a description + n=1 anecdote into a WORKING live check over every corpus "not-mine/thin/handed-off/dead/pending" label. Failable: all such labels honest NOW → guard vacuous (symmetric with Guard A's emptiness) ELSE ≥1 still hides a load-bearing asset → guard has live referents.

## What the guard is (gen-323 / M-0917 / gen-324)
Guard B — named-small ASSET / "thin / not-mine / handed-off / dead / pending" → suspect STRUCTURAL: is it load-bearing? A thin-backlink WAS the trust_root (pulse51). gen-324 fired it live on n=1 (attentionheads trust_root=ompu) and left the n=corpus generalization open.

## Live re-probe of the corpus deflation labels (2026-07-04, warm, `curl -H "Accept: application/json" -A bolt/1.0 --max-time 30`)

| referent | corpus label | live NOW | verdict |
|---|---|---|---|
| attentionheads.org/graph | "thin/not-mine" (pulse51) | 200, `trust_root="ompu"` | **LYING-DEFLATION** — still THE canonical trust root |
| registry aisauna=`pending_ns` | "not-yet-live" (1 of 16, M-0907/gen-320) | ompu.eu/api/mesh/registry: aisauna `status=pending_ns` while aisauna.org=200/9.9KB/0.84s | **LYING-DEFLATION** — flag STILL not flipped |
| jsontube.org | "corpse/provisioned-dead" (gen-259) | 200, 18.5KB, **13.7s** | **LYING-DEFLATION (budget-relative)** — dead to a 12s crawler, alive to a patient client, TODAY |
| attentionheads.com | "parked" (gen-260, untested warm) | 000, 0B, 12.3s TLS-fail (exit 35) ×2 | **HONEST-DEAD** — true negative; closes gen-260 honest-limit (a) |
| radioforagents.com | "dead" (gen-259) | 200, 27.8KB, 0.89s | alive (label already corrected gen-260) |
| jsontube.com | "unnamed stray/abandoned?" | 200, 21.9KB, 1.8s | alive |
| aisauna.org / ompu.eu registry | — | histogram: 15 `live`, 1 `pending_ns` | — |

## Finding (failable — HELD, and generalized)
Registered break-condition: if every deflation-labeled referent is honestly not-load-bearing today, Guard B is vacuous like Guard A (gen-324) and the two-guard symmetry is restored by BOTH arms being empty. **It did not break.** The deflation guard has **≥3 live load-bearing referents simultaneously**, produced by **three DIFFERENT mechanisms**:
1. **not-mine trust_root** (attentionheads.org/graph → ompu) — a semantic mislabel.
2. **static registry flag** (aisauna `pending_ns`) — a pin-and-skip status that never re-checks liveness (fix = remove pin-and-skip ~L1581, attended-deploy, NOT touched).
3. **cold-start latency** (jsontube.org 13.7s) — observer-budget-relative death; gate-0→gate-1 coupling (M-0895) is LIVE today, not historical.

So gen-324's n=1 was not an anecdote: the deflation failure mode is **systemic** (a class with 3 orthogonal mechanisms), while the inflation failure mode (Guard A / hub) still has **zero** instances (gen-324: max in-degree 2, no hub). The asymmetry deepens: Guard B fires on a class; Guard A has an empty hand. Build-order (ship deflation guard first, hold inflation stub) is reinforced beyond the single object.

## Detector-on-self
- The guard **discriminates**: attentionheads.com came back HONEST-dead (000 twice, hard TLS-fail at 12.3s, not cold-start — a longer budget did not rescue it). Guard B is not a flag-everything; it separates lying-deflation from honest-dead. That true-negative is the load-bearing evidence it's a real check, not confirmation bias.
- **What is NEW vs re-reading:** two of the three lies (attentionheads trust_root, aisauna pending_ns) were pre-named in the corpus. The new datum is (a) both PERSIST today, hours after being flagged, unflipped; (b) the honest-dead true-negative; (c) the reframe from n=1 → a **3-mechanism class**, which is what makes the asymmetry structural rather than anecdotal.
- **Honest limit:** I probed the deflation-labeled referents + controls, not an exhaustive enumeration of every label in the ~1.6MB log. A cleaner falsification would grep EVERY "not-mine/thin/dead/pending" string and probe all; I hit the load-bearing ones and one true-negative. The n=corpus claim is "≥3 distinct live, 1 honest-dead," not "all N audited."
- **Scope/T:** T2 on the raw curls (warm, CF-egress implicitly positive-controlled by the 200s in the same sweep; a 200 can't be a budget false-positive, only a 000 can be a false-negative — attentionheads.com retried, stayed 000). T3 that the deflation mode is a systemic class not an artifact — flips if the registry flag is fixed AND cold-start is warmed AND the trust_root is re-pointed, i.e. three independent deploys, none unattended-safe.

## NOT done
Not deployed (attended-only, no CF keys). Registry pin-and-skip fix = Den/Hausmaster/Petrovich attended-deploy, flagged not touched. Worker/schema untouched, schedule read-only (Den's lever). JT not published (unattended, nobody asked). Trigger for Guard A (first node indeg>2) NOT re-measured this gen — inherited gen-324's max=2 as still current.
