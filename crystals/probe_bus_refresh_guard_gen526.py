#!/usr/bin/env python3
# Bolt gen-526 FAILABLE PROBE of tools/bus_refresh_guard.py (a27f3ecd).
# Lens under test: is refresh_if_stale's decision channel feed-injectable, is the
# analyzer subprocess argv-safe (not shell-string), does it honor never-raises, and
# what is the exit-code/status contract? INDEPENDENT oracle re-derives the stale
# predicate + expected action from the docstring spec, NOT the module branch order.
#
# SAFETY: the REAL module invokes `subprocess.run([python, ANALYZER, --format both])`
# which REGENERATES live bus_live.json/bus_graph.json. We MUST NOT run that against
# the live bus. So we COPY the guard into a mkdtemp sandbox tools/ dir; the module
# derives HERE/BUS_DIR/ANALYZER from __file__, so all paths resolve inside the sandbox.
# A stub bus_analyzer.py records argv + returns a chosen rc. Live bus NEVER touched.
import os, sys, json, shutil, hashlib, tempfile, importlib.util, pathlib

S = os.environ.get("OMPU_SHARED")
if not S or not os.path.isdir(os.path.join(S, "tools")):
    cands = [p for p in __import__("glob").glob("/sessions/*/mnt/OMPU_shared") if os.path.isdir(p)]
    S = cands[0] if cands else S
LIVE_GUARD = os.path.join(S, "tools", "bus_refresh_guard.py")

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]

MD5_BEFORE = md5(LIVE_GUARD)

STUB_ANALYZER = r'''#!/usr/bin/env python3
# Stub bus_analyzer: records argv, optionally bumps bus_live.json to feed newest, exits chosen rc.
import sys, json, os, pathlib
HERE = pathlib.Path(__file__).resolve().parent
BUS = HERE.parent / "bus"
marker = BUS / "ARGV_MARKER.json"
json.dump(sys.argv, open(marker, "w"))
rc = int(os.environ.get("STUB_RC", "0"))
if rc == 0:
    # emulate a successful refresh: write bus_live.json newest == feed newest
    feed = ""
    try:
        for raw in open(BUS / "feed.jsonl"):
            m = json.loads(raw); sa = m.get("sent_at", "")
            if sa > feed: feed = sa
    except Exception: pass
    json.dump({"messages": [{"sent_at": feed}]}, open(BUS / "bus_live.json", "w"))
sys.exit(rc)
'''

def make_sandbox():
    d = tempfile.mkdtemp(prefix="brg_gen526_")
    tools = os.path.join(d, "tools"); bus = os.path.join(d, "bus")
    os.makedirs(tools); os.makedirs(bus)
    shutil.copy(LIVE_GUARD, os.path.join(tools, "bus_refresh_guard.py"))
    open(os.path.join(tools, "bus_analyzer.py"), "w").write(STUB_ANALYZER)
    return d, tools, bus

def load_guard(tools):
    # fresh import per sandbox so HERE resolves to this sandbox's tools dir
    for k in [k for k in list(sys.modules) if k == "bus_refresh_guard"]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location("bus_refresh_guard", os.path.join(tools, "bus_refresh_guard.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def write_feed(bus, sent_ats):
    with open(os.path.join(bus, "feed.jsonl"), "w") as f:
        for sa in sent_ats:
            f.write(json.dumps({"sent_at": sa, "from": "x"}) + "\n")

def write_live(bus, newest):
    if newest is None:
        return  # missing file
    json.dump({"messages": [{"sent_at": newest}]}, open(os.path.join(bus, "bus_live.json"), "w"))

# INDEPENDENT oracle straight from the docstring contract:
#   stale = force or (not live) or (feed and feed > live)
#   not stale -> action 'skip-fresh', rc 0
#   stale + analyzer rc0 -> 'refreshed', rc 0
#   stale + analyzer rc!=0 -> 'refresh-failed', rc 2
#   never raises in any case
def oracle(force, live, feed):
    stale = force or (not live) or (bool(feed) and feed > live)
    return "stale" if stale else "skip-fresh"

results = []
def check(name, cond, got=""):
    results.append((name, bool(cond), got));
    print(("PASS" if cond else "FAIL"), name, "|", got)

# ---- C1: FRESH (feed <= live) -> skip-fresh, NO subprocess, rc0 ----
d, tools, bus = make_sandbox()
write_live(bus, "2026-07-07T12:00:00Z"); write_feed(bus, ["2026-07-07T11:00:00Z"])
m = load_guard(tools); st = m.refresh_if_stale()
argv_exists = os.path.exists(os.path.join(bus, "ARGV_MARKER.json"))
check("C1 fresh->skip, no analyzer call, rc0",
      st["action"] == "skip-fresh" and st["rc"] == 0 and not argv_exists,
      f"action={st['action']} rc={st['rc']} analyzer_called={argv_exists} oracle={oracle(False,'2026-07-07T12:00:00Z','2026-07-07T11:00:00Z')}")

# ---- C2: STALE (feed newer, feed-INJECTION trigger direction) -> refreshed rc0 + argv is a LIST ----
os.environ["STUB_RC"] = "0"
d, tools, bus = make_sandbox()
write_live(bus, "2026-07-07T12:00:00Z"); write_feed(bus, ["2026-07-07T13:00:00Z"])  # injected newer msg
m = load_guard(tools); st = m.refresh_if_stale()
argv = json.load(open(os.path.join(bus, "ARGV_MARKER.json")))
check("C2 injected-newer-msg triggers refresh, rc0",
      st["action"] == "refreshed" and st["rc"] == 0,
      f"action={st['action']} rc={st['rc']}")
check("C2b analyzer argv is ARGV-LIST [ANALYZER,'--format','both'] (no shell string)",
      isinstance(argv, list) and argv[-2:] == ["--format", "both"] and argv[0].endswith("bus_analyzer.py"),
      f"argv={argv}")

# ---- C3: STALE + analyzer rc!=0 -> refresh-failed rc2, NEVER raises ----
os.environ["STUB_RC"] = "3"
d, tools, bus = make_sandbox()
write_live(bus, "2026-07-07T12:00:00Z"); write_feed(bus, ["2026-07-07T13:00:00Z"])
m = load_guard(tools)
try:
    st = m.refresh_if_stale(); raised = False
except Exception as e:
    raised = True; st = {"action": f"RAISED:{e!r}", "rc": -1}
check("C3 analyzer-fail->refresh-failed rc2, never raises",
      not raised and st["action"] == "refresh-failed" and st["rc"] == 2,
      f"raised={raised} action={st['action']} rc={st['rc']}")

# ---- C4: analyzer MISSING (subprocess crash) -> refresh-exception rc2, never raises ----
os.environ["STUB_RC"] = "0"
d, tools, bus = make_sandbox()
os.remove(os.path.join(tools, "bus_analyzer.py"))  # make the subprocess target vanish
write_live(bus, "2026-07-07T12:00:00Z"); write_feed(bus, ["2026-07-07T13:00:00Z"])
m = load_guard(tools)
try:
    st = m.refresh_if_stale(); raised = False
except Exception as e:
    raised = True; st = {"action": f"RAISED:{e!r}", "rc": -1}
# python running a missing file returns nonzero rc -> refresh-failed (still rc2, never raises)
check("C4 missing-analyzer-> rc2 caught, never raises",
      not raised and st["rc"] == 2 and st["action"] in ("refresh-failed", "refresh-exception"),
      f"raised={raised} action={st['action']} rc={st['rc']}")

# ---- C5: corrupt/missing bus_live.json -> _live_newest '' -> treated as STALE (fail-safe refresh) ----
os.environ["STUB_RC"] = "0"
d, tools, bus = make_sandbox()
write_live(bus, None)  # no bus_live.json at all
write_feed(bus, ["2026-07-07T13:00:00Z"])
m = load_guard(tools); st = m.refresh_if_stale()
check("C5 missing-bus_live -> stale -> refreshes (fail-safe, oracle='stale')",
      st["action"] == "refreshed" and st["rc"] == 0 and oracle(False, "", "2026-07-07T13:00:00Z") == "stale",
      f"action={st['action']} rc={st['rc']}")

# ---- C6: force=True on a FRESH feed -> refreshes anyway ----
d, tools, bus = make_sandbox()
write_live(bus, "2026-07-07T12:00:00Z"); write_feed(bus, ["2026-07-07T11:00:00Z"])
m = load_guard(tools); st = m.refresh_if_stale(force=True)
check("C6 force overrides fresh -> refreshed",
      st["action"] == "refreshed" and oracle(True, "2026-07-07T12:00:00Z", "2026-07-07T11:00:00Z") == "stale",
      f"action={st['action']}")

# ---- C7: SUPPRESSION test — can a feed poster make the guard SKIP a needed refresh? ----
# To skip, need feed_newest <= live_newest. A poster can only ADD msgs (raise feed_newest),
# never lower it below live. So injection cannot force skip-fresh when the feed is genuinely
# ahead. Confirm: with live behind feed, no amount of *appended* msgs yields skip.
d, tools, bus = make_sandbox()
write_live(bus, "2026-07-07T10:00:00Z")
write_feed(bus, ["2026-07-07T11:00:00Z", "2026-07-07T12:00:00Z", "2026-07-07T13:00:00Z"])
m = load_guard(tools); st = m.refresh_if_stale()
check("C7 feed-append cannot SUPPRESS a real refresh (no skip while feed>live)",
      st["action"] != "skip-fresh",
      f"action={st['action']} (injection is trigger-only, not suppress)")

# ---- md5 gate ----
MD5_AFTER = md5(LIVE_GUARD)
check("MD5 live guard unchanged pre==post (read-only, no live mutation)",
      MD5_BEFORE == MD5_AFTER, f"{MD5_BEFORE}=={MD5_AFTER}")

npass = sum(1 for _, ok, _ in results if ok)
print(f"\n=== {npass}/{len(results)} GREEN  (live guard md5 {MD5_BEFORE}->{MD5_AFTER}) ===")
sys.exit(0 if npass == len(results) else 1)
