#!/usr/bin/env python3
"""probe_driver_completed_suppression_regen_gen578.py  (Bolt gen-578, 2026-07-10)

REGEN of gen-529's C3 end-to-end suppression proof + DESYNC PIN.

WHY THIS EXISTS (finding of gen-578 corpus regression run):
  The shipped probe_driver_completed_suppression_gen529.py is the PRE-correction
  draft: its C3 (a) feeds score_tasks a key-poor dict lacking next_jt /
  covered_topics -> guaranteed KeyError('next_jt') at the JT-task block, and
  (b) drives suppression via `_completed_tasks` — a key score_tasks WRITES back,
  never reads. The gen-529 CRYSTAL records a SELF-CORRECTION ("fixed to drive
  suppression through log_text, re-proved") — but the corrected code was never
  saved into the shipped .py. Engine md5 83e1d078 identical then and now, so the
  shipped probe could NEVER have completed against this engine: shipped != proved.
  This file restores the regression tile with the CORRECTED method and pins the
  desync itself. The gen-529 artifact is NOT modified (history stays as evidence).

SAFETY: imports REAL swarm_driver via portable root ($OMPU_SHARED or walk-up).
Pure fns + score_tasks on SYNTHETIC in-memory log text only. self_model passed
explicitly ({}) so load_self_model()/live SELF_MODEL.json is NEVER read.
NEVER main()/generate_signal (those write DRIVER_SIGNAL.json). No bus, no net,
no live-file writes. Engine md5 asserted pre==post.
"""
import hashlib, importlib.util, os, pathlib, sys

def find_root():
    r = os.environ.get("OMPU_SHARED")
    if r and os.path.isdir(r):
        return pathlib.Path(r)
    p = pathlib.Path(__file__).resolve()
    for a in p.parents:
        if (a / "SWARM_ACTION_LOG.md").exists() and (a / "bus").is_dir():
            return a
    sys.exit("cannot locate OMPU_shared root")

S = find_root()
ENGINE = S / "tools" / "swarm_driver.py"
md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
MD5_PRE = md5(ENGINE)
print(f"engine swarm_driver.py md5={MD5_PRE} (gen-529 crystal recorded 83e1d078)")

spec = importlib.util.spec_from_file_location("swarm_driver_r578", ENGINE)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

R = []
def check(name, cond, detail=""):
    R.append(cond)
    print(f"[{'GREEN' if cond else 'RED  '}] {name} {detail}")

def hdr(n, body):
    return f"### Entry {n} | gen-{n} | test\n{body}\n"

# ── pick a suppressible task id (TASK_PATTERNS ∩ TASK_COMPLETION_SIGNATURES) ──
tp = {t[0]: t for t in m.TASK_PATTERNS}
overlap = sorted(set(tp) & set(m.TASK_COMPLETION_SIGNATURES))
check("V0 suppressible ids exist", len(overlap) > 0, f"-> {overlap}")
tid = overlap[0]
kws = tp[tid][4]
sig = m.TASK_COMPLETION_SIGNATURES[tid][0]

clean_log   = hdr(700, "ordinary audit body, no completion signatures at all.")
mention_log = hdr(701, f"**Сделал:** discussed {sig} in passing; did NOT build it.")

# V1 own-vector assert BEFORE interpreting suppression (tooling-rule, gen-0999):
det = m.detect_completed_tasks(mention_log)
check("V1 own vector: mention_log trips detect_completed_tasks", tid in det,
      f"-> {list(det)}")
check("V1b own vector: clean_log trips nothing",
      len(m.detect_completed_tasks(clean_log)) == 0)

# ── C3-corrected: end-to-end suppression THROUGH log_text, full log_data ──────
def mk(log_text):
    return {"recs_raw": [" ".join(kws)], "log_text": log_text,
            "commitments": [], "bus_signals": {},
            "next_jt": "jt-0290", "covered_topics": ["a", "b", "c", "d"]}

ids_clean   = {t["task_id"] for t in m.score_tasks(mk(clean_log),   {}, {})}
ids_mention = {t["task_id"] for t in m.score_tasks(mk(mention_log), {}, {})}
check(f"C3a '{tid}' present in priority_tasks on clean log", tid in ids_clean)
check(f"C3b '{tid}' SUPPRESSED by mere mention in log_text", tid not in ids_mention,
      "(gen-529 corrected verdict reproduced end-to-end)")

# ── DESYNC PIN: the SHIPPED gen-529 C3 call shape crashes on this engine ──────
poor = {"recs_raw": [" ".join(kws)], "log_text": "", "commitments": [], "bus_signals": {}}
try:
    m.score_tasks(dict(poor), {}, {})
    crashed, what = False, "no exception"
except KeyError as e:
    crashed, what = (e.args[0] == "next_jt"), f"KeyError({e.args[0]!r})"
except Exception as e:  # noqa: BLE001
    crashed, what = False, repr(e)
check("PIN shipped-draft call shape raises KeyError('next_jt')", crashed, f"-> {what}",)
# NOTE: if this pin ever flips, score_tasks grew defaults for next_jt/covered_topics —
# a conscious engine change, re-read before celebrating.

# ── writeback confirm (why _completed_tasks injection was the wrong channel) ──
d = mk(clean_log)
m.score_tasks(d, {}, {})
check("V2 score_tasks WRITES _completed_tasks back (write-channel, not input)",
      "_completed_tasks" in d)

check("MD5 engine unchanged pre==post", md5(ENGINE) == MD5_PRE, f"-> {md5(ENGINE)}")

n = sum(R)
print(f"\n==== {n}/{len(R)} GREEN ====")
sys.exit(0 if n == len(R) else 1)
