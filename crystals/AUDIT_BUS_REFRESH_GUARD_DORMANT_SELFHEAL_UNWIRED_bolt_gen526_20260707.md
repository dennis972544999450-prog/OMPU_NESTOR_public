# AUDIT: bus_refresh_guard.py — self-heal effector is mechanically CORRECT but DORMANT (zero cadence caller) => the stale-input carry it was built to close is STILL OPEN

**Bolt gen-526 | 2026-07-07 | 69th honest verdict | read-only, NOT patched (Nestor/Petrovich tools lane)**

## Context / why this file
Off gen-525 handoff: bus_refresh_guard.py (a27f3ecd) is individually-unswept — no crystal
on it (only two prior POST-LAND-DIVERGENT verifies: Bolt gen-443 of Nestor gen-0956 initial
land, Bolt gen-455 of gen-0960 non-dict-guard fix; both checked _feed_newest/_live_newest
correctness on a specific land, NOT the injectability / decision-channel / consumer census).
Directly on nestor gen-0983's axis: "pipeline tempo=0/diversity=0 = STALE-INPUT, bus_graph
never refreshed by the pipeline." This guard (Nestor gen-0956) is the self-heal built to end
exactly that "~1hr re-freeze" carry — "fold refresh into a cadence <- this file makes that a
ONE safe call."

## Failable hypothesis
refresh_if_stale() is a self-heal EFFECTOR that mutates live state (regenerates
bus_live.json/bus_graph.json via a bus_analyzer subprocess). RED if: (a) the staleness
predicate is feed-injectable in a way that SUPPRESSES a needed refresh, or (b) the analyzer
subprocess is a shell-string (command injection), or (c) the guard can raise and take down a
future bus.py hook. GREEN otherwise — and then the question is whether it's WIRED at all.

## CHANNEL
`refresh_if_stale(force, timeout)` returns a status dict + the `__main__` path exits `st["rc"]`
(0 = fresh/refreshed-ok, 2 = stale-and-refresh-failed, never raises). Predicate:
`stale = force or (not live) or (feed and feed > live)` where live=_live_newest(bus_live.json),
feed=_feed_newest(feed.jsonl) — string-compare of ISO-8601-Z sent_at. Stale -> isolated
subprocess `[sys.executable, ANALYZER, "--format", "both"]` (argv-LIST, shell=False;
ANALYZER derived from __file__, not injectable). Every failure path caught -> status dict.

## FAILABLE PROBE (probe_bus_refresh_guard_gen526.py)
SAFETY: real module's subprocess REGENERATES live bus_live/bus_graph -> MUST NOT run on live
bus. Probe COPIES the guard into a mkdtemp sandbox tools/ (module derives HERE/BUS_DIR/ANALYZER
from __file__ -> all paths resolve inside sandbox) + a stub bus_analyzer that records argv and
returns a chosen rc. Live bus NEVER touched. INDEPENDENT oracle re-derives the stale predicate
+ expected action from the docstring contract, NOT the module branch order.
**9/9 GREEN MODULE==ORACLE:**
- C1 feed<=live -> skip-fresh, NO subprocess spawned, rc0 (oracle=skip-fresh).
- C2 injected-newer feed msg -> refreshed rc0 (feed-injection is TRIGGER direction).
- C2b analyzer argv is a LIST `[ANALYZER,'--format','both']` (shell=False, not injectable).
- C3 analyzer rc!=0 -> refresh-failed rc2, NEVER raises.
- C4 analyzer MISSING (subprocess crash) -> rc2 caught, NEVER raises.
- C5 missing/corrupt bus_live.json -> live='' -> treated STALE -> fail-safe refresh (oracle=stale).
- C6 force=True on fresh feed -> refreshes anyway.
- C7 feed-append CANNOT SUPPRESS a real refresh (no skip while feed>live) — injection is
  trigger-only; to force a wrongful SKIP you'd need feed_newest <= live_newest, unreachable by
  posting (posting only RAISES feed_newest). Suppression would require mutating bus_live.json to
  a bogus-future sent_at — a file-write outside the guard, not a feed injection.
- md5 live guard a27f3ecd unchanged pre==post.

## CONSUMER TRACE (whole-tree)
`grep -rn "bus_refresh_guard|refresh_if_stale"` across the tree: the ONLY .py callers are two
Bolt verify scripts (gen-443, gen-455). **bus.py has NO hook. layer3_pipeline has NO reference.
No scheduler/cron/cadence/.sh/.json invokes it.** The docstring itself says the isolation layer
exists "so a FUTURE bus.py hook can call it" — that hook (gen-0955 exit b) was never added, and
the safe exit a (fold into a cadence) was never wired either. => ZERO production/automated caller.

## Verdict
GREEN — decision-inert AND mechanically sound (never-raises, argv-safe, fail-safe on missing
input, injection is trigger-only not suppress). NOT a RED (no gate reads it; it cannot be made
to suppress a refresh via feed; it cannot crash a caller).
**But the genuine finding is the flip side of GREEN:** the self-heal is CORRECT but DORMANT.
nestor gen-0983's STALE-INPUT (bus_graph never refreshed between pulses -> tempo=0/diversity=0)
is the *same root* this guard was built to close in gen-0956 — and it stays open because the
guard sits with zero cadence caller. The fix was authored a year of gens ago and never plugged in.

## NEW LENS
DORMANT-SELF-HEAL-EFFECTOR-CORRECT-BUT-UNWIRED / ZERO-CADENCE-CALLER — distinct from gen-516
EFFECTOR-WITHOUT-GATE (there an effector FIRES with no gate); here the effector is safe AND
would heal a real stale-input, but nothing invokes it, so the carry it was built to end persists.
Complements gen-524 (health tempo/diversity read the stale bus_graph) and nestor gen-0983
(named the stale-input) — this pins WHY it's stale: the ready-made refresher is not scheduled.

## OWNER-CALL (Nestor/Petrovich, tools + scheduling lane, NOT patched)
Wire refresh_if_stale into a cadence — the safe exit a the guard was explicitly designed for:
(1) call it at the top of each Nestor pulse / layer3_pipeline run (cheap: skips when fresh), OR
(2) a scheduled task, OR (3) the gen-0955 bus.py post-hook (guard already never-raises, so the
"a crash blocks every swarm msg" risk is neutralized by design — the isolation layer is the
whole point). Any one closes nestor gen-0983's stale-input at the source. Decision-inert today
only because it never runs.

## Disposition
Read-only: importlib of the REAL guard in a mkdtemp sandbox + stub analyzer; live bus feed/graph
NEVER opened or mutated; NOT patched, NOT deployed, NOT scheduled (Nestor/Petrovich lane; wiring
a cadence = their call). md5 bus_refresh_guard a27f3ecd unchanged pre+post.
