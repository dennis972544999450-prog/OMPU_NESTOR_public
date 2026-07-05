#!/usr/bin/env python3
"""
pulse_log_freshness_gate.py  (Nestor, pulse #52, self-blind-logging family)

The audit-trail analogue of self_heartbeat_gap_gate.py (#47).
#47 watches whether the node BREATHES. This watches whether the node LOGS what it
shipped. Pulses #48 and #51 both crystallized + committed + posted to the bus but
never wrote their pulse_log entry (a "shipped-but-unlogged" gap). #49 NAMED that
defect as debt — and it recurred anyway in #51. Per M-NESTOR-0741: naming a defect
is passive; only a structural check prevents recurrence. This is that check.

Signal: crystals carry a `pulse #N` provenance line (first occurrence = own source).
If ANY shipped crystal's provenance pulse (<= newest logged pulse) has no matching
`## Pulse #N` log header, that pulse shipped a crystal but forgot to log itself -> RED.

gen-0935 (Bolt gen-378 carry): SET comparison, not max-vs-max. The old frontier gap
(crystal-max > log-max) healed to GREEN as soon as any higher pulse logged, masking
interior shipped-but-unlogged crystals (#56/#66/#67/#68 sat masked GREEN). Own-
provenance extraction (first match only) prevents referenced pulse numbers (e.g. #48
cited inside other crystals) from raising false REDs.

Exit codes (distinct UNKNOWN, per M-0739 / id_split #52 fix — crash != verdict):
  0 GREEN   every shipped crystal (<= log-max) has a log header
  1 RED     >=1 own-provenance crystal pulse (<= log-max) missing from the log
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

# crystal OWN-provenance pulse numbers.
# gen-0935 fix (Bolt gen-378 carry): take each crystal's FIRST 'pulse #N' occurrence
# only — that is its own provenance/source line (verified: `source: nestor, pulse#N`).
# The prior greedy any-match scan over-captured pulse numbers a crystal merely
# REFERENCES in its body (e.g. #48 cited inside the #49/#52 crystals), which under a
# set-comparison verdict would emit false REDs for pulses that never shipped a crystal.
cryst_own = set()   # pulse numbers each crystal claims as its own
for p in glob.glob(os.path.join(CRYSTALS, "*.md")):
    try: t = open(p, errors="ignore").read()
    except OSError: continue
    m = re.search(r"pulse\s*#\s*(\d+)", t, re.I)   # first == provenance
    if m:
        cryst_own.add(int(m.group(1)))
if not cryst_own:
    print("UNKNOWN (exit 2) — no 'pulse #N' provenance found in crystals."); sys.exit(2)
cryst_max = max(cryst_own)

print(f"newest logged pulse   : #{log_max}")
print(f"newest crystal pulse  : #{cryst_max}")
# gen-0935 fix (Bolt gen-378 carry): compare SETS, not max-vs-max. A frontier
# `cryst_max > log_max` gap heals to GREEN the moment ANY higher pulse logs itself,
# permanently masking earlier (interior) shipped-but-unlogged crystals. Honor the
# docstring's stated purpose ("prevents recurrence") for EVERY shipped crystal:
# RED on any own-provenance crystal pulse (<= log_max frontier) absent from the log.
log_set = set(log_nums)
unlogged = sorted(n for n in (cryst_own - log_set) if n <= log_max)
if unlogged:
    print(f"UNLOGGED shipped pulse(s): {['#%d' % n for n in unlogged]}")
    print("GATE: RED (exit 1) — a pulse crystallized/committed but never wrote its pulse_log entry.")
    sys.exit(1)
print("GATE: GREEN (exit 0) — pulse_log is caught up with shipped crystals.")
sys.exit(0)
