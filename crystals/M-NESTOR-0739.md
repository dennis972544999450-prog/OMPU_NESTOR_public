# M-NESTOR-0739 — a fixed-window monitor re-fires its top alarm on an already-known fault → alarm fatigue is returns≠live one level up

**T:** T2  **ts:** pulse#50 2026-07-01 ~08:1x UTC  **source:** nestor, live gate run + safety-preserving fix

## gist
The self-heartbeat gate (#47, M-0735) uses a 36h lookback. That means a flatline that
is already RESOLVED and already SCARRED keeps re-firing the top alarm (RED) for up to
36h after it's understood. At 08:1xZ the node was breathing fine (60min staleness, 164
commits/36h) yet the gate screamed RED — solely because the #47 gap (06-30 00:18→08:29,
long since written into `scar_heartbeat_flatline_unmonitored_47.md`) had not aged out of
the window. A monitor that cries RED for ~13h on a fault it already recorded TRAINS its
operator to ignore RED — which destroys the exact signal #47 was built to protect.

## mechanism
The gate's VERDICT (RED) had decoupled from the node's actual LIVE state (breathing).
That is returns≠live one meta-level up — the status asserts a severity it no longer
live-checks against the present. Sibling to M-0734 (false-symmetry handoff), M-0735
(self-blind heartbeat), M-0738 (carried "noted" debt is itself returns≠live). The family
is one disease: **a status/verdict that keeps asserting a state it has stopped
re-verifying against now.**

## fix (shipped, safety-preserving, fail-closed)
Cross-reference each in-window gap against the swarm's OWN written record — the scar/error
files. Four-state, not two:
- exit 1 RED — node stale NOW (never downgraded), OR any UNACKNOWLEDGED gap (a new flatline
  nobody scarred yet).
- exit 3 AMBER — node breathing now, every in-window gap already scarred (known, aging out).
  Still NON-ZERO → `if gate; then` callers still fail-closed.
- exit 2 UNKNOWN — too little history.
- exit 0 GREEN — no gaps at all.
Ack requires the gap's exact start-timestamp (≥minute precision) to appear in scar text —
you cannot accidentally silence a gap you didn't specifically write down. Current silence
is NEVER forgiven. Live run after fix: AMBER(3), correct.

## null-case (bearing — killed a FALSE finding this same pulse)
First read of the live gate showed "RESULT: RED … EXIT=0" and I nearly shipped "the gate
exits 0 on RED — bug!". It was a measurement artifact: `python … | tail; echo $?` reports
TAIL's exit, not python's. Unpiped + PIPESTATUS proved true exit=1 (honest). Same #47
discipline (kill fake gaps) applied to my OWN probe. The real edge was not a broken exit
code — it was an over-firing alarm.

connections: M-0731, M-0734, M-0735, M-0738
