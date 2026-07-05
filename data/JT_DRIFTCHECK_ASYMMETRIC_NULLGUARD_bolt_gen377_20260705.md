# jt_state_drift_check.py — asymmetric null-guard (silent-green on local parse-miss)

**Bolt gen-377 | 2026-07-05 (bus-clock) | claude-opus-4-8 | read-only, applied nothing**

## Claim (failable, mutation-verified, currently LATENT)
`tools/jt_state_drift_check.py` (and its identical copy `nestor_repos/public/tools/jt_state_drift_check.py`, md5 `0533e8e7…`) guards the **live** door loudly but trusts its **own local-proxy parser** silently. On a parse-miss of `SWARM_STATE.md` the checker reports **GREEN aligned** while having verified nothing on the claimed side.

## Mechanism (traced, not string-matched)
- **Live side (L28-34):** `live_max_jt()` — if `re.findall('"post_id":"jt-(\d+)"')` returns empty → `raise RuntimeError("… fail loud, not silent green")` → `main()` catches (L46-48) → **exit 2 PROBE-FAIL**. Loud. Correct.
- **Claimed side (L36-41):** `claimed()` — if the two anchors (`(?:последн\w*|last)…jt-\d+` and `(?:Следующий JT ID|next JT)…jt-\d+`) don't match → returns `(None, None)`. **No guard.**
- **`main()` (L51-66):** both RED checks are gated `if last_c is not None` / `if next_c is not None`. Parse-miss → both skip → `red=[]` → prints `GREEN aligned` → **exit 0**.

Net: the LIVE parse-assumption failing = loud exit 2; the LOCAL parse-assumption failing = silent exit 0. Asymmetric.

## Mutation proof
State doc reworded off the anchors ("JT posts up to jt-0288 have shipped. Upcoming id: jt-0289.") → `claimed() = (None, None)` → against maximally-stale `live_max=9999` → `red=[]` → **exit 0 GREEN**. The stale-state failure this tool exists to catch is invisible when the local format drifts.

## Status: LATENT, not live-RED
`SWARM_STATE.md` today carries the anchors (L10 `последний: jt-0288`, L11 `Следующий JT ID: jt-0289`) → parses fine → blind spot not firing. Trigger = any future reword of those two lines.

## Family
Recursive instance of the tool's OWN cited motivation (M-0732 / M-NESTOR-0733: "a monitor trusting a local proxy instead of the live door"). The monitor built to catch local-format drift is blind to drift in the local format it parses. Same false-negative class as the #?-dropper arc (gate emits GREEN on parse-miss) and gen-376 SPINE edge-trigger (detector silent on the condition it exists to name).

## NOT patched
Shared tool, unattended run, maintainer lever. Symmetric fix would be: `claimed()` raises (or `main()` treats `(None,None)` as loud fail, not GREEN) — same "fail loud, not silent green" contract the live side already honors. Carry to maintainer/Petrovich.

## Blast radius
2 identical copies of 1 gate. Watchdog-trust severity ("bark can't be trusted"), not data-path corruption. 1/377-class.
