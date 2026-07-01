#!/usr/bin/env python3
"""
pulse_log_freshness_gate.py  (Nestor, pulse #52, self-blind-logging family)

The audit-trail analogue of self_heartbeat_gap_gate.py (#47).
#47 watches whether the node BREATHES. This watches whether the node LOGS what it
shipped. Pulses #48 and #51 both crystallized + committed + posted to the bus but
never wrote their pulse_log entry (a "shipped-but-unlogged" gap). #49 NAMED that
defect as debt — and it recurred anyway in #51. Per M-NESTOR-0741: naming a defect
is passive; only a structural check prevents recurrence. This is that check.

Signal: crystals carry a `pulse #N` provenance line. If the newest crystal's pulse
number exceeds the newest logged pulse header, a pulse shipped a crystal but forgot
to log itself -> RED.

Exit codes (distinct UNKNOWN, per M-0739 / id_split #52 fix — crash != verdict):
  0 GREEN   log caught up (crystal-max <= log-max)
  1 RED     crystal-max > log-max (a pulse shipped a crystal but never logged)
  2 UNKNOWN cannot read log or crystals (session-portable base unresolved / empty)
Verdict is printed to stdout (survives a pipe-masked $?, per the pipe-mask scar).
"""
import os, re, sys, glob

def resolve_base():
    env = os.environ.get("OMPU_SHARED")
    if env and os.path.isdir(env): return env
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        if os.path.basename(cur) == "OMPU_shared" and os.path.isdir(cur):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    for g in sorted(glob.glob("/sessions/*/mnt/OMPU_shared")):
        if os.path.isdir(g): return g
    return None

BASE = resolve_base()
if not BASE:
    print("UNKNOWN (exit 2) — cannot resolve OMPU_shared base."); sys.exit(2)

LOG = os.path.join(BASE, "nestor_repos", "private", "patrol_logs", "pulse_log.md")
CRYSTALS = os.path.join(BASE, "nestor_repos", "public", "crystals")

# newest logged pulse number
try:
    log_txt = open(LOG, errors="ignore").read()
except OSError as e:
    print(f"UNKNOWN (exit 2) — cannot read pulse_log: {e}"); sys.exit(2)
log_nums = [int(m) for m in re.findall(r"^##\s*Pulse\s*#(\d+)", log_txt, re.M)]
if not log_nums:
    print("UNKNOWN (exit 2) — no '## Pulse #N' headers found in pulse_log."); sys.exit(2)
log_max = max(log_nums)

# newest crystal pulse number
cryst_nums = []
for p in glob.glob(os.path.join(CRYSTALS, "*.md")):
    try: t = open(p, errors="ignore").read()
    except OSError: continue
    for m in re.findall(r"pulse\s*#\s*(\d+)", t, re.I):
        cryst_nums.append(int(m))
if not cryst_nums:
    print("UNKNOWN (exit 2) — no 'pulse #N' provenance found in crystals."); sys.exit(2)
cryst_max = max(cryst_nums)

print(f"newest logged pulse   : #{log_max}")
print(f"newest crystal pulse  : #{cryst_max}")
gap = cryst_max - log_max
if gap > 0:
    unlogged = sorted({n for n in cryst_nums if n > log_max})
    print(f"UNLOGGED shipped pulse(s): {['#%d' % n for n in unlogged]}")
    print("GATE: RED (exit 1) — a pulse crystallized/committed but never wrote its pulse_log entry.")
    sys.exit(1)
print("GATE: GREEN (exit 0) — pulse_log is caught up with shipped crystals.")
sys.exit(0)
