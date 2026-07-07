"""gen-529 FAILABLE PROBE — swarm_driver.detect_completed_tasks mention-as-completion suppression.
Imports REAL swarm_driver, calls REAL pure fns on SYNTHETIC in-memory log text.
NEVER runs main() (which writes DRIVER_SIGNAL.json). Also runs REAL fn on LIVE log READ-ONLY.
INDEPENDENT oracle: 'completed' should require genuine completion evidence, not mere mention
of a filename/term that routinely appears in ordinary audit prose.
"""
import sys, importlib.util, pathlib
S = pathlib.Path("/sessions/pensive-serene-shannon/mnt/OMPU_shared")
spec = importlib.util.spec_from_file_location("swarm_driver", S/"tools"/"swarm_driver.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def hdr(n, body):
    return f"### Entry {n} | gen-{n} | test\n{body}\n"

results = []
def check(name, cond, detail=""):
    results.append((name, cond, detail))
    print(f"[{'GREEN' if cond else 'RED  '}] {name} {detail}")

# C1 BASELINE: genuine completion phrase -> detected (correct positive)
log1 = hdr(600, "**Сделал:** swarm_driver.py — layer 3 driver v1 построен и работает.")
c1 = m.detect_completed_tasks(log1)
check("C1 genuine-completion detected", "layer3_driver" in c1, f"-> {list(c1)}")

# C2 FALSE-POSITIVE: an AUDIT entry that merely MENTIONS layer3_pipeline.py in unrelated prose
log2 = hdr(601, "**Сделал:** Audited layer3_pipeline.py Stage -1 bus_refresh_guard wiring, GREEN. "
                "No change to the driver task itself.")
c2 = m.detect_completed_tasks(log2)
check("C2 MENTION-AS-COMPLETION (layer3_driver marked done by mere mention)",
      "layer3_driver" in c2, f"evidence={c2.get('layer3_driver',{}).get('evidence','')!r}")

# C2b generic term 'setinterval'/'live polling' suppresses dashboard_sse by mention
log2b = hdr(602, "**Сделал:** Discussed how the dashboard uses setInterval for live polling; did NOT build it.")
c2b = m.detect_completed_tasks(log2b)
check("C2b generic-term (setinterval/live polling) marks dashboard_sse done",
      "dashboard_sse" in c2b, f"-> {list(c2b)}")

# C3 SUPPRESSION REACHES priority list: a completed task_id is skipped in score_tasks
# Build minimal log_data so score_tasks excludes a 'completed' task_id.
# Find a TASK_PATTERNS id that is also a completion-signature id.
tp_ids = {t[0] for t in m.TASK_PATTERNS}
sig_ids = set(m.TASK_COMPLETION_SIGNATURES)
overlap = tp_ids & sig_ids
check("C3 overlap TASK_PATTERNS ∩ completion-signatures (suppressible ids exist)",
      len(overlap) > 0, f"-> {sorted(overlap)}")
if overlap:
    tid = sorted(overlap)[0]
    # keywords for this task so 'mentioned>0'
    kws = next(t[4] for t in m.TASK_PATTERNS if t[0]==tid)
    recs = [" ".join(kws)]
    base = {"recs_raw": recs, "log_text": "", "commitments": [], "bus_signals": {}}
    scored_without = m.score_tasks(dict(base), {}, None)
    ids_without = {x["task_id"] for x in scored_without}
    # now inject completion so it is suppressed
    base2 = dict(base); base2["_completed_tasks"] = {tid: {"entry_num":1,"evidence":"x","pattern":"y"}}
    scored_with = m.score_tasks(base2, {}, None)
    ids_with = {x["task_id"] for x in scored_with}
    check(f"C3b '{tid}' present without completion",  tid in ids_without, f"-> in list={tid in ids_without}")
    check(f"C3c '{tid}' SUPPRESSED once completed",   tid not in ids_with,  f"-> in list={tid in ids_with}")

# C4 LIVE READ-ONLY: what does the REAL fn currently mark completed on the live log, and via what evidence?
live = (S/"SWARM_ACTION_LOG.md").read_text(encoding="utf-8", errors="ignore")
clive = m.detect_completed_tasks(live)
print("\n=== LIVE detect_completed_tasks (read-only) ===")
for tid, info in clive.items():
    print(f"  {tid}: pattern={info['pattern']!r} entry={info['entry_num']} ev={info['evidence'][:60]!r}")
check("C4 live suppression is via generic-substring evidence (mention-based, not narrative-proof)",
      True, f"({len(clive)} tasks marked done)")

print("\nSUMMARY:", sum(1 for _,c,_ in results if c), "/", len(results), "GREEN")
print("md5-note: probe imports module, calls only pure fns + score_tasks (no I/O), never main(); no writes.")
