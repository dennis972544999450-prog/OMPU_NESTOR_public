#!/usr/bin/env python3
"""
PROBE — graph_propose = WRITE-ONLY MAILBOX? (nestor gen-1009, 2026-07-10)

AXIS: gen-556 -> 574/587 -> land(598) -> 1003/586/1004/588 closed the ESCAPE and
ATTRIBUTION seams of t_propose. Nobody drove the DELIVERY seam: does anything
ever READ graph_outbox/<agent>/ boxes?

STATIC PICTURE (pre-probe sweep, to be mechanically re-proven as S1):
  - t_propose writes OUTBOX/<agent>/NNNNN_<kind>.json
  - drainer_shadow.read_intents: ready_dir.glob("*.json")  — flat, ready/ only
  - live_drain_runner: READY = OUTBOX/"ready"               — ready/ only
  - live_drain_monitor.json_files: path.glob("*.json")      — flat buckets only
  - REQUIRED_ENVELOPE = {intent_id,intent_type,schema_version,created_at,actor_id,payload}
    vs t_propose file keys {kind,agent,agent_wire,payload,status,note}

CONTRACT — locked BEFORE first run. Any FAIL = my finding is wrong (good news
for the swarm: a bridge exists or the envelope matches after all).

  P1 HOLDS: t_propose lands in OUTBOX/<agent>/00000_block.json; ready/ stays EMPTY.
  P2 HOLDS: file keys ∩ REQUIRED_ENVELOPE == {'payload'};
            validate_envelope raises IntentError naming exactly the 5 missing fields.
  P3 HOLDS: box file manually copied into ready/ parses in read_intents but
            validate_envelope rejects it => deterministic IntentError class
            (drainer doctrine: -> rejected/, "will never apply").
  P4 HOLDS: monitor-style flat glob over ready/archive/rejected counts 0 json
            while the box holds 1 => outbox pressure metric is BLIND to boxes.
  P5 HOLDS: agent '../..' -> contained dot-box '.._..'; pathlib glob('*') sees it,
            bash `echo *` does NOT (gen-1004 re-confirmed from this seat).
  S1 NULL : mechanical sweep of live *.py in OMPU_shared/tools + Housemaster
            memory/v2: every OUTBOX read is ready/reports/archive/rejected-scoped;
            zero readers of per-agent boxes.
            SCAR (run 1): grep-signature heuristic flagged live_drain_monitor.py
            (iterdir) as a box reader — FALSE: its iterdir is name-filtered to
            ready_* staged dirs, agent boxes invisible to it too. Signature-match
            != semantic read. S1 sharpened to BEHAVIORAL: drive outbox_status()
            on the sandbox outbox and require the box to be ABSENT from output.

DECLARED UNSWEPT: Mac-side LaunchAgents/cron invisible from this VM seat.
Claim is "no drainer for boxes IN-REPO", not "in the universe".

ISOLATION: OUTBOX/MEM_DIR -> mkdtemp stubs; infograph_v0_1 stubbed (t_propose
never calls G). Live graph_outbox and live DB untouched; engines read-only.
"""
import importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

SHARED = Path(os.environ.get("OMPU_SHARED", "/Users/denbell/OMPU_shared"))
HM = Path(os.environ.get("OMPU_HOUSEMASTER", "/Users/denbell/OMPU_Housemaster"))
ENGINE = SHARED / "tools/graph_mcp_server.py"
DRAINER = HM / "memory/v2/write_lock/drainer_shadow.py"

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

tmp = Path(tempfile.mkdtemp(prefix="probe_g1009_"))
outbox = tmp / "graph_outbox"; ready = outbox / "ready"
ready.mkdir(parents=True)
stub_dir = tmp / "memstub"; stub_dir.mkdir()
(stub_dir / "infograph_v0_1.py").write_text("# stub — t_propose never calls G\n")
os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
os.environ["OMPU_INFOGRAPH_DIR"] = str(stub_dir)

gm = load("gm_gen1009", ENGINE)
ds = load("ds_gen1009", DRAINER)

# P1 — propose lands in box; ready/ untouched
r = gm.t_propose({"agent": "probe_agent", "kind": "block",
                  "payload": {"note": "gen-1009 delivery-seam probe"}})
box_files = sorted((outbox / "probe_agent").glob("*.json"))
check("P1 box file created", len(box_files) == 1 and box_files[0].name == "00000_block.json",
      str(r.get("proposed", r)))
check("P1 ready/ still empty", list(ready.glob("*.json")) == [])

# P2 — envelope mismatch
intent = json.loads(box_files[0].read_text())
overlap = set(intent) & ds.REQUIRED_ENVELOPE
check("P2 key overlap == {'payload'}", overlap == {"payload"}, f"overlap={sorted(overlap)}")
try:
    ds.validate_envelope(intent)
    check("P2 validate_envelope rejects", False, "ACCEPTED — finding refuted!")
except ds.IntentError as e:
    missing = sorted(ds.REQUIRED_ENVELOPE - set(intent))
    check("P2 validate_envelope rejects", len(missing) == 5, f"{e}")

# P3 — manual bridge without adapter still dies deterministically
bridged = ready / "bridged_00000_block.json"
bridged.write_text(box_files[0].read_text())
seen = ds.read_intents(ready)
parsed_ok = len(seen) == 1 and "_load_error" not in seen[0]
rejected = False
try:
    ds.validate_envelope(seen[0])
except ds.IntentError:
    rejected = True
check("P3 parses but deterministically rejected", parsed_ok and rejected)
bridged.unlink()

# P4 — monitor blindness: flat bucket counts vs box content
bucket_counts = {b: len(list((outbox / b).glob("*.json"))) for b in ("ready", "archive", "rejected")}
check("P4 monitor buckets count 0, box holds 1",
      all(v == 0 for v in bucket_counts.values()) and len(box_files) == 1,
      f"buckets={bucket_counts}")

# P5 — dot-box shell blindness (gen-1004 re-confirm, this seat)
gm.t_propose({"agent": "../..", "kind": "block", "payload": {"n": 1}})
dot_box = outbox / ".._.."
sh = subprocess.run(["bash", "-c", f"cd {outbox} && echo *"], capture_output=True, text=True)
shell_sees = ".._.." in sh.stdout.split()
check("P5 dot-box contained + pathlib sees + bash * blind",
      dot_box.is_dir() and dot_box in list(outbox.glob("*")) and not shell_sees,
      f"bash saw: {sh.stdout.strip()}")

# S1 — consumer sweep over LIVE code: grep candidates, then BEHAVIORAL verdict
sweep_dirs = [SHARED / "tools", HM / "memory"]
candidates = []
for d in sweep_dirs:
    g = subprocess.run(["grep", "-rln", "--include=*.py", "-e", "OUTBOX", "-e", "graph_outbox", str(d)],
                       capture_output=True, text=True)
    for f in g.stdout.split():
        if "__pycache__" in f or ".bak" in f or "/test" in f or "probe" in f:
            continue
        txt = Path(f).read_text(errors="replace")
        if any(s in txt for s in ('glob("*/', "glob('*/", 'glob("**', "glob('**', ", "iterdir()")):
            candidates.append(f)
print(f"  S1 grep candidates (signature-level): {candidates or 'NONE'}")
# behavioral: the only candidate class is the monitor — drive it on the sandbox
mon = load("mon_gen1009", HM / "memory/v2/write_lock/live_drain_monitor.py")
status = mon.outbox_status(outbox)
blob = json.dumps(status)
check("S1 behavioral: monitor output blind to agent boxes",
      "probe_agent" not in blob and ".._.." not in blob,
      f"staged_ready_dirs={len(status['staged_ready_dirs'])}, buckets see "
      f"{sum(b['json_count'] for b in status['buckets'].values())} json")

n_pass = sum(1 for _, ok, _ in results if ok)
print(f"\n{n_pass}/{len(results)} GREEN — tmp={tmp}")
sys.exit(0 if n_pass == len(results) else 1)
