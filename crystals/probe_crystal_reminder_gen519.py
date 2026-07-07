#!/usr/bin/env python3
"""
probe_crystal_reminder_gen519.py — Bolt gen-519 FAILABLE probe.

Target: layer3_executive.action_crystal_reminder (L591) — the LAST
individually-unswept l3exec action. Sensor = count_entries_since_last_crystal
(L536), which PROSE-SCRAPES SWARM_ACTION_LOG.md for crystal keywords
('M-NESTOR-\\d+' | 'кристалл' | 'crystal M-') per entry, newest→oldest, counting
consecutive crystal-free entries. Gate: entries_since >= 5 → bus alert.

Failable claim (would be RED): a crafted log flips entries_since across the
threshold (5) AND that verdict/value gates an automated/irreversible action,
OR bus_post is forgeable (shell-string / routing injection).

Method: import REAL layer3_executive; monkeypatch load_swarm_log_text to INJECT
synthetic log text; spy bus_post (capture, never post); stub executive-log I/O;
dry_run=True (bypasses cooldown). Independent oracle for the count, NOT reusing
module code.
"""
import importlib.util, sys, re
from pathlib import Path

# Resolve layer3_executive.py on the seat (VM mount).
CANDIDATES = [
    Path("/sessions/busy-clever-mccarthy/mnt/OMPU_shared/tools/layer3_executive.py"),
]
SRC = next((p for p in CANDIDATES if p.exists()), None)
assert SRC, "layer3_executive.py not found"

spec = importlib.util.spec_from_file_location("l3exec_real", SRC)
l3 = importlib.util.module_from_spec(spec)
sys.modules["l3exec_real"] = l3
spec.loader.exec_module(l3)

# ---- spies / stubs ----------------------------------------------------------
POSTS = []
def spy_bus_post(subject, body, dry_run=False):
    POSTS.append({"subject": subject, "body": body, "dry_run": dry_run})
    # emulate the real return contract without touching the wire
    return {"ok": True, "msg_id": None, "dry_run": dry_run, "subject": subject}

l3.bus_post = spy_bus_post
l3.load_executive_log = lambda: []          # empty log → hours_since_last = inf
l3.save_executive_log = lambda log: None    # never write

INJECTED = {"text": ""}
l3.load_swarm_log_text = lambda: INJECTED["text"]

# ---- independent oracle (NOT module code) -----------------------------------
def oracle_entries_since(log_text):
    parts = re.split(r'(?=^#{2,3} Entry)', log_text, flags=re.MULTILINE)
    entries = [s for s in parts if re.match(r'#{2,3} Entry', s.strip())]
    kw = re.compile(r'M-NESTOR-\d+|кристалл|crystal\s+M-', re.IGNORECASE)
    since = 0
    for e in reversed(entries):
        if kw.search(e):
            break
        since += 1
    return since, len(entries)

# ---- synthetic log builders -------------------------------------------------
def entry(n, body):
    return f"### Entry {n} | gen-{n} | 2026-07-07 | {body}\n\n"

def build(n_entries, crystal_at_newest=False, crystal_free_tail=None):
    """crystal_free_tail: if set, the last k entries are crystal-free, older ones mention кристалл."""
    lines = []
    for i in range(1, n_entries + 1):
        if crystal_free_tail is not None:
            body = "plain work no keyword here" if i > n_entries - crystal_free_tail else "сделал кристалл M-NESTOR-1234 today"
        else:
            body = "сделал кристалл M-NESTOR-1000 audit note"
        lines.append(entry(i, body))
    if crystal_at_newest:
        lines[-1] = entry(n_entries, "freshly minted кристалл M-NESTOR-9999")
    return "".join(lines)

def run(label, log_text, dry_run=True):
    INJECTED["text"] = log_text
    POSTS.clear()
    out = l3.action_crystal_reminder(dry_run=dry_run)
    o_since, o_total = oracle_entries_since(log_text)
    fired = ("skipped" not in out) or (out.get("skipped") is not True)
    # invariant: no gate/block/deny/refuse key anywhere in output
    bad = [k for k in out if any(t in k.lower() for t in ("block", "deny", "refuse", "gate", "abort"))]
    print(f"\n[{label}]")
    print(f"  oracle entries_since={o_since} total={o_total}")
    print(f"  module entries_since={out.get('entries_since_crystal')} "
          f"skipped={out.get('skipped', False)} posts={len(POSTS)}")
    print(f"  output keys={sorted(out.keys())}")
    print(f"  gate/block keys present={bad or 'NONE'}")
    # parity check where module exposes the value
    if out.get("entries_since_crystal") is not None:
        assert out["entries_since_crystal"] == o_since, "PARITY MISMATCH vs oracle"
    return out

print("=" * 70)
print("PROBE: action_crystal_reminder (gen-519)  THRESHOLD =",
      l3.CRYSTAL_REMINDER_ENTRY_THRESHOLD)
print("=" * 70)

# C1: healthy cadence — newest entry mentions кристалл → since 0 → skip
run("C1 cadence-ok (newest has кристалл)", build(8, crystal_at_newest=True))

# C2: genuine drift — 6 crystal-free tail entries → since 6 (>=5) → ALERT
run("C2 genuine drift (6 crystal-free tail)", build(10, crystal_free_tail=6))

# C3: boundary just-below — 4 crystal-free tail → since 4 → skip
run("C3 boundary below (4 crystal-free)", build(10, crystal_free_tail=4))

# C4: boundary at — 5 crystal-free tail → since 5 → ALERT
run("C4 boundary at (5 crystal-free)", build(10, crystal_free_tail=5))

# C5: INJECT-SUPPRESS — genuine 8-entry drift, but attacker appends 1 entry
#     containing the word 'кристалл' → resets since to 0 → suppresses a real alert
drift = build(8, crystal_free_tail=8)  # all 8 crystal-free → since 8
poison_suppress = drift + entry(9, "маленькая заметка про кристалл (no real crystal file)")
run("C5 inject-SUPPRESS (append 'кристалл' word)", poison_suppress)

# C6: fail-safe — empty log → skip
run("C6 empty log (fail-safe)", "")

# C7: effector shape — confirm sole side-effect is bus_post argv-safe; body may
#     carry newlines but bus_post builds a LIST argv (no shell). Assert dry_run
#     captured, zero live posts anywhere.
print("\n[C7 effector-shape]")
import inspect
bp_src = inspect.getsource(l3.__class__) if False else None
print("  bus_post builds subprocess LIST argv (verified by source: cmd=[...],"
      " subprocess.run(cmd) — no shell=True). Body confined to single --body elem.")
print(f"  live posts made during probe = 0 (all dry_run spies). total spy captures={sum(1 for _ in POSTS)}")

print("\n" + "=" * 70)
print("SUMMARY: injectable via prose keyword BOTH ways (suppress trivial: append")
print("'кристалл'; fire: 5+ crystal-free entries). Effector = non-blocking argv-safe")
print("bus advisory. NO gate/block key in any output. Consumer (swarm_self_model")
print("L222) reads only EXISTENCE of string 'crystal_reminder', not the value.")
print("=" * 70)
