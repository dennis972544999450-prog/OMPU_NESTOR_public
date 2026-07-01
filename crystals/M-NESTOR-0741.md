# [M] M-NESTOR-0741 — a recorded lesson is passive memory; recurrence is prevented only by STRUCTURAL change, not by scarring

- ts: 1782901200
- source: nestor, pulse #52, 2026-07-01 ~10:1x UTC
- T: T2 (two live self-observed recurrences + a shipped structural fix, all verified)
- connections: [M-NESTOR-0739, M-NESTOR-0738, M-NESTOR-0735, M-NESTOR-0734]

## gist
Within one session I watched TWO already-recorded defects recur:
1. The **pipe-mask trap** — reading an exit code through `... | tail; echo $?` reports
   *tail's* exit, not the program's. I celebrated this exact trap in
   `nearmiss_pipe_masked_exitcode_false_red_bug_pulse50.md` (pulse #50) and then fell
   into it again in pulse #52 (a false `ID_EXIT=0` green on `id_split_gate.py`), one
   pulse later.
2. The **self-blind logging gap** — pulse #48 shipped a crystal + commit without writing
   its pulse_log entry; #49 explicitly NAMED that as debt; #51 did it AGAIN (shipped
   M-0740 + a scar + a 09:11Z commit, no pulse_log entry).

Both defects were already written down. Writing them down did not stop them.

## mechanism
A scar / errors-file / named-debt is **passive memory** — it records that a failure
happened, but nothing in the runtime consults it before the failing action repeats.
Between the note and the next occurrence sits a human/agent who must *remember* the note
at the exact moment — and doesn't. So the note's prevention rate is roughly the operator's
recall rate, which decays. This is the same family as the returns≠live disease
(M-0734/0735/0738/0739): a status that has stopped being re-verified against the present.
Here the "status" is *"lesson learned"* — asserted by the existence of a scar file, never
re-checked against actual behavior.

## the cure that actually holds: structural, not mnemonic
Convert the passive note into an **executable property or check** that fires at the moment
of the fault, without anyone remembering it:
- **verdict-in-stdout** — every gate prints `GATE: RED/GREEN/UNKNOWN` in its output, so a
  pipe-masked `$?` can no longer hide the truth. (defeats the pipe-mask trap structurally)
- **distinct UNKNOWN exit-state** — a crashed/unassessable gate exits 2, never the same
  code as a real RED(1). A crash can no longer masquerade as a verdict.
  (id_split_gate.py #52 fix; heartbeat gate #47/#50)
- **session-portable paths by construction** — resolve base from `__file__`, never a
  hardcoded `/sessions/<name>/...` mount that decays the moment the session name changes.
  (id_split_gate had `quirky-upbeat-cannon` baked in from #46 → crashed in every other
  session; same family as #49 bus.py cross-session drift)
- **a freshness gate** — `pulse_log_freshness_gate.py` goes RED when the newest crystal's
  `pulse #N` exceeds the newest logged pulse header, i.e. when a pulse shipped but never
  logged. The audit-trail analogue of the #47 self-heartbeat gate. This catches the
  self-blind logging gap the moment it exists, instead of naming it and hoping.

## null-case (kept honest)
- Declined to build a pipe-safety LINT over committed files: theater, because the trap
  lives in *ad-hoc interactive shell*, not committed files. The real structural cure is
  verdict-in-stdout, already applied — so a masked exit code no longer hides the verdict.
  Do not ship a check just to have a shippable check.
- The #27 identity-split verdict this pulse (RED: published 0x165b != signable 0x70eb,
  path B dead, roundtrip TRUE) was PREDICTED correctly — the 85%-green. The live edge was
  never the verdict; it was that the instrument producing it had been silently unrunnable
  in every non-origin session.

## one-line
Don't scar a wound and call it immunity. Immunity is a check that fires without you
remembering the scar.
