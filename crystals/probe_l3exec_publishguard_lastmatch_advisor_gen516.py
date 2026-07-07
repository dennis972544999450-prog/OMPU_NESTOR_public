#!/usr/bin/env python3
"""
Bolt gen-516 — variant-3 genuinely-new failable audit.
TARGET: layer3_executive.action_publish_guard (L845) — semantic publish gate.
FIND-QUESTION: overlap_level/top_score are LAST-MATCH-scraped (no break) from
concept_index.py --query stdout. Input is genuinely flippable. DOES the flip
reach an irreversible/automated gate (a publish block/allow), or only a soft
advisory?  METHOD: import REAL layer3_executive, monkeypatch subprocess.run to
inject synthetic concept_index stdout, capture bus_post (dry_run=True => no
live post), read-only. Independent oracle for overlap parse (does NOT reuse
module code). NO live bus post, NO live file write.
"""
import sys, types, importlib.util, re, json
from pathlib import Path

TOOLS = Path("/sessions/sleepy-pensive-goodall/mnt/OMPU_shared/tools")
spec = importlib.util.spec_from_file_location("l3exec_g516", TOOLS/"layer3_executive.py")
L3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L3)

# ---- Independent oracle: parse overlap the honest way, LAST match wins (mirrors
# the source semantics but written independently, no import of module regex) ----
def oracle(stdout):
    score=0.0; level="unknown"
    for ln in stdout.splitlines():
        if "OVERLAP" in ln:
            m=re.search(r"\(([0-9.]+)\)", ln)
            if m: score=float(m.group(1))
            if "HIGH" in ln: level="HIGH"
            elif "PARTIAL" in ln: level="PARTIAL"
            elif "LOW" in ln: level="LOW"
    return level, score

# ---- Harness: run REAL action_publish_guard against injected concept_index stdout ----
CAPTURED = {"bus_calls": []}
def make_run(stdout):
    def fake_run(cmd, *a, **k):
        # concept_index.py --query <topic>  -> return synthetic stdout
        return types.SimpleNamespace(stdout=stdout, stderr="", returncode=0)
    return fake_run

# wrap bus_post to record (dry_run=True already prevents live post, but double-guard)
_real_bus = L3.bus_post
def spy_bus(subject, body, dry_run=False):
    CAPTURED["bus_calls"].append({"subject": subject, "dry_run": dry_run})
    # force dry_run True no matter what -> never touches live bus
    return _real_bus(subject, body, dry_run=True)
L3.bus_post = spy_bus

def run_guard(stdout, topic="test topic gen516"):
    CAPTURED["bus_calls"].clear()
    L3.subprocess.run = make_run(stdout)   # inject concept_index stdout
    entry = L3.action_publish_guard(topic, dry_run=True)  # dry_run => bus_post no-op
    return entry, list(CAPTURED["bus_calls"])

CI = "Query: '{t}'\nTop matches:\n  1. [{s}] jt-0141 (jt_post)\n"
HIGH = "  ⚠ HIGH OVERLAP ({v}): strong similarity\n"
LOW  = "  ✓ LOW OVERLAP ({v}): novel\n"
PARTIAL = "  ℹ️  PARTIAL OVERLAP ({v}): related\n"

cases = {
 "C1 clean HIGH":            CI.format(t="x",s="0.72") + HIGH.format(v="0.72"),
 "C2 clean LOW":             CI.format(t="x",s="0.10") + LOW.format(v="0.10"),
 "C3 POISON suppress HIGH->LOW (last-match)":  CI.format(t="x",s="0.72") + HIGH.format(v="0.72") + LOW.format(v="0.02"),
 "C4 POISON false HIGH LOW->HIGH (last-match)": CI.format(t="x",s="0.10") + LOW.format(v="0.10") + HIGH.format(v="0.99"),
}

print("=== action_publish_guard: injectable? + decision reach ===\n")
all_ok=True
for name,stdout in cases.items():
    entry,bus = run_guard(stdout)
    olv=entry.get("overlap_level"); osc=entry.get("top_score")
    ora_lv,ora_sc = oracle(stdout)
    parse_ok = (olv==ora_lv and abs((osc or 0)-ora_sc)<1e-9)
    warned = entry.get("warning_issued", False)
    blocked = entry.get("skipped") and "block" in str(entry.get("reason","")).lower()
    n_bus = len(bus)
    # invariant: warning only when HIGH; never blocks; bus_post always dry_run
    inv = (warned == (olv=="HIGH")) and (not blocked) and all(b["dry_run"] for b in bus)
    all_ok &= parse_ok and inv
    print(f"[{name}]")
    print(f"    parsed overlap={olv} score={osc}  oracle={ora_lv}/{ora_sc}  parse_match={parse_ok}")
    print(f"    warning_issued={warned}  blocked_publication={blocked}  bus_posts={n_bus} (all dry_run={all(b['dry_run'] for b in bus) if bus else 'n/a'})")
    print()

print("--- LAST-MATCH injectable confirmed:", 
      run_guard(cases["C3 POISON suppress HIGH->LOW (last-match)"])[0]["overlap_level"]=="LOW",
      "(genuine HIGH suppressed to LOW by trailing injected line)")
print("--- FALSE-HIGH injectable confirmed:",
      run_guard(cases["C4 POISON false HIGH LOW->HIGH (last-match)"])[0]["overlap_level"]=="HIGH",
      "(genuine LOW flipped to HIGH by trailing injected line)")
print("\nDECISION REACH: overlap_level gates ONLY bus_post warning (HIGH) or a display 'hint' (PARTIAL/LOW).")
print("action_publish_guard NEVER returns a block/refuse; docstring+body: 'НЕ блокирует публикацию'.")
print("bus_post here is argv-list (no shell) and forced dry_run in probe.")
print("\nALL GREEN" if all_ok else "\n*** CHECK ***")
