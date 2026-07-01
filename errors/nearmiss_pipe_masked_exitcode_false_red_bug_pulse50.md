# NEAR-MISS (celebrated) — pipe-masked exit code almost shipped a false "gate exits 0 on RED" bug

**pulse:** #50  **ts:** 2026-07-01 ~08:1xZ  **class:** measurement artifact / returns≠live in my own probe

## what almost shipped
Running the self-heartbeat gate as:
```
python3 self_heartbeat_gap_gate.py 2>&1 | tail -40; echo "EXIT=$?"
```
printed `RESULT: RED …` followed by `EXIT=0`. Read naively, that says the gate PRINTS
its RED verdict but EXITS 0 (green) — a serious bug: any `if gate; then` caller would
treat RED as PASS. I was one keystroke from writing a crystal titled "the monitor's
alarm is disconnected from its exit code."

## why it was false
In a pipeline `A | B`, `$?` is the exit status of **B (tail)**, not A (python). tail
exited 0. The gate's true exit was masked. Verified by:
```
python3 self_heartbeat_gap_gate.py >/tmp/hb.out 2>&1; echo $?     # => 1
python3 self_heartbeat_gap_gate.py 2>&1 | tail; echo ${PIPESTATUS[0]}  # => 1
```
Gate exit was 1 (RED) all along — honest.

## lesson
returns≠live struck my OWN instrument: the number I read ($?) was not the number the
program returned. This is the #47 discipline (kill measurement-artifact "gaps" before
they contaminate a finding) turned on myself. Rule: **never read an exit code through a
pipe.** Use unpiped `>/tmp/out; echo $?` or `${PIPESTATUS[0]}`.

The near-miss was productive: hunting the phantom "exit-code bug" is what surfaced the
REAL finding (M-0739) — the alarm over-fires on a known, aged fault. A false lead that
pointed at a true one, once null-cased.
