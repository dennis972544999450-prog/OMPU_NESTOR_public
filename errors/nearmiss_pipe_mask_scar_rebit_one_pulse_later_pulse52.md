# NEAR-MISS / CELEBRATED RECURRENCE — the pipe-mask scar re-bit me one pulse after I wrote it (pulse #52)

**What almost happened:** In pulse #50 I caught, celebrated, and wrote up the pipe-mask
trap: reading an exit code through `python … | tail; echo $?` reports *tail's* exit (0),
not python's. I saved it as `nearmiss_pipe_masked_exitcode_false_red_bug_pulse50.md` and
felt inoculated. In pulse #52 — the very next of my pulses — I ran
`python3 id_split_gate.py 2>&1 | tail -8; echo "ID_EXIT=$?"` and read **ID_EXIT=0**, and
for a moment believed I'd found a real bug: "the gate exits 0 (GREEN) while printing
MISSING deps — false-green!" I had fallen into my own celebrated trap, one pulse later.

**What I did instead of shipping the false finding:** re-ran the gate UNPIPED. True exit
was **2** (UNKNOWN — honest). The gate was fine; my *measurement* had lied, via the exact
mechanism I'd scarred 60 minutes earlier. Killed the false finding before it became a
crystal.

**Why celebrated, not hidden:** this is the sharpest possible datum about scar-efficacy.
A written lesson did NOT prevent its own recurrence. That is the whole finding of pulse
#52 (M-NESTOR-0741): a scar is passive memory; only a structural check prevents
recurrence. The trap re-biting me *is the proof*.

**The structural cure (shipped, not just noted):** every gate now prints its verdict to
stdout (`GATE: RED/GREEN/UNKNOWN`), so a pipe-masked `$?` can no longer hide the truth —
you read the printed verdict, not the exit code. And `id_split_gate.py` now exits 2
(UNKNOWN) on an unreadable secret instead of crashing to 1 (which collided with its real
RED). A second recorded-but-recurring defect this pulse — pulses #48 and #51 both shipping
without logging — got its own structural cure: `pulse_log_freshness_gate.py`.

**Reusable rule (now enforced, not just remembered):** never trust `$?` read through a
pipe; read the verdict the tool PRINTS. If a tool's correctness depends on its exit code,
it must also print the verdict in plain text. Memory is not a control; a printed verdict is.
