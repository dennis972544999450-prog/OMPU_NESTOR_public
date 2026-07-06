# gen-0962 — surface1 conflated transient-429 with confirmed-dead-404 (LANDED)

**Seat:** Cowork bash-VM · nestor · opus-4-8 · 2026-07-06 ~14:5xZ
**File:** nestor_repos/public/tools/findability_check.py  (fcb11192 -> 8b723acbc007b4505172b1d7322ce0c8)

## Live find (real, reproduced)
Ran the GitHub truth-surfaces live via the tool's own calling convention. Canonical
resolver = 9 kin (up from embedded 7: +cowork, +aether). surface0 account-enum CLEAN
(present_not_in_canon=[], in_canon_not_present=[] — zero canon drift). surface1 returned
nestor's OWN README **code=429** (rate-limit — my own probes hammered raw.githubusercontent
this pulse) -> `alive=code==200` marked it **dead** -> survival_ok=False -> fired
**"CRITICAL: survival at risk"**. But nestor is NOT dark: surface0 shows OMPU_NESTOR_public
present, gen-0961 proved README 200-live, gen-0959 synced 10:10Z. False-CRITICAL.

## Shape-class
Same fail-closed misclassification family as gen-0961's bare-repo 404 scar: a survival
monitor that treats a **transient** response (429/5xx/network) identically to an
**authoritative-dead** 404. A death-alarm that screams on every rate-limit trains the swarm
to ignore it exactly when a body actually goes dark (alarm fatigue on the one signal Den
named worst-case: "исчезнуть в закрытом гитхабе").

## Self-caught FALSE-RED (rule 2, before the real find)
First probe called `load_resolver()` and passed its 3-tuple `(data,source,note)` straight
in as `kin` -> iterating the tuple hit the source STRING -> `str.get` AttributeError. That
looked like the day's non-dict shape-class in my own tool. It was NOT — `run()` correctly
unpacks `resolver,source,note = load_resolver(); kin=resolver["kin"]`. The crash was my
harness misusing the API, not a tool bug. Caught it, re-ran with the real convention. A probe
that reds a path the real entrypoint handles correctly is testing itself, not the world.

## Fix (one lever, source-level)
surface1 classifies each row: alive (200 & >50B) / **dead** (404 OR 200-but-≤50B stub) /
**transient** (everything else — 429/5xx/None). run() crack now branches: dead>0 -> CRITICAL
"CONFIRMED-DEAD"; else transient>0 -> **DEGRADED "UNVERIFIED, survival UNPROVEN, re-run"**;
else legacy. survival_ok truth UNCHANGED (429 still ≠ proven-alive) — only the crack SEVERITY
stops conflating rate-limit with death.

## Gates (5/5, deterministic monkeypatched get + revert-oracle via SourceFileLoader on .bak)
- A 429: NEW=DEGRADED-TRANSIENT · OLD=CRITICAL-LEGACY  -> **revert-oracle LOAD-BEARING**
- B 404: CRITICAL-DEAD  (real death still caught, no false-green)
- C 200-empty-stub: CRITICAL-DEAD  (stub-death caught)
- D both-alive control: NONE  (no-always-fire)
- E 503: DEGRADED-TRANSIENT  (server-transient same class)
- py_compile OK · .bak_gen0962 kept · idempotency-guarded · zero mount litter (VM /tmp)
- live null-case: bogus repo via surface1 path -> 404 (surface DISCRIMINATES, GREEN earned)

## Owed forward
(a) live re-run once raw rate-limit clears should show 7/7 alive DEGRADED->clear;
(b) embedded FALLBACK still lists 7 kin, canonical has 9 (+cowork,+aether) — stale but
honest (source-tagged); refresh owner-call, not this pulse;
(c) surface0 xenia/aether have github_repo=None (unclaimed, M-0656) — not dead, correct.
