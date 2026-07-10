#!/usr/bin/env python3
"""probe_bus_parachute_cure_proposal_gen575.py — dual battery ORIGINAL vs PROPOSED.

Proves gen-549 findings on ORIGINAL bus/bus_parachute.py (f2b60f02) and their
cure in crystals/bus_parachute_PROPOSED_gen575.py:
  #1 restore feed non-idempotence (re-run after partial crash duplicates feed line)
  #2 msg_id collision -> buffered message silently OVERWRITTEN (data loss)

Technique = gen-549 synthetic-bus + gen-573 dual-battery:
  - fully synthetic bus per case in tempfile.mkdtemp (copy of real bus.py,
    fresh bus.db born via `bus.py reindex` on POSIX /tmp — M-0770 safe);
  - OMPU_BUS_DIR / OMPU_PARACHUTE_DIR env-overrides; subprocess for CLI cases,
    spec_from_file_location + monkeypatched _mk_msg_id for collision cases;
  - NEVER touches live bus.db / feed.jsonl / messages/ / network / __main__;
  - md5 of live engine asserted unchanged at the end.
"""
import os, sys, json, hashlib, shutil, sqlite3, subprocess, tempfile
import importlib.util
from pathlib import Path

S = Path(os.environ.get("OMPU_SHARED", str(Path.home() / "OMPU_shared")))
ORIGINAL = S / "bus" / "bus_parachute.py"
PROPOSED = S / "nestor_repos" / "public" / "crystals" / "bus_parachute_PROPOSED_gen575.py"
BUS_PY = S / "bus" / "bus.py"
EXPECT_ORIG_MD5 = "f2b60f02"

results = []
def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))

def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]

def synth_bus():
    """Fresh synthetic bus + parachute dirs on /tmp. Returns (bus_dir, para_dir, env)."""
    work = Path(tempfile.mkdtemp(prefix="probe_parachute_g575_"))
    bus = work / "bus"; (bus / "messages").mkdir(parents=True)
    shutil.copy2(BUS_PY, bus / "bus.py")
    (bus / "feed.jsonl").write_text("")
    env = dict(os.environ, OMPU_BUS_DIR=str(bus), OMPU_PARACHUTE_DIR=str(work / "parachute"))
    # birth of fresh bus.db on POSIX /tmp (M-0770: impossible on FUSE, fine here)
    r = subprocess.run([sys.executable, str(bus / "bus.py"), "reindex"],
                       capture_output=True, text=True, env=env)
    assert (bus / "bus.db").exists(), f"synthetic bus.db not born: {r.stdout} {r.stderr}"
    return bus, work / "parachute", env

def run_cli(build, env, *a):
    return subprocess.run([sys.executable, str(build), *a],
                          capture_output=True, text=True, env=env)

def feed_count(bus, mid):
    n = 0
    for line in (bus / "feed.jsonl").read_text().splitlines():
        if line.strip() and json.loads(line).get("msg_id") == mid:
            n += 1
    return n

def db_count(bus, subject):
    c = sqlite3.connect(bus / "bus.db")
    n = c.execute("SELECT count(*) FROM messages WHERE subject=?", (subject,)).fetchone()[0]
    c.close(); return n

def load_module(build, env):
    """In-process load with env pre-set (module reads env at import)."""
    os.environ.update({k: env[k] for k in ("OMPU_BUS_DIR", "OMPU_PARACHUTE_DIR")})
    spec = importlib.util.spec_from_file_location(f"para_{abs(hash(str(build)))}", build)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def mk_args(mod, body, force_buffer=True):
    import argparse
    return argparse.Namespace(**{"from": "bolt", "subject": "collision-case",
        "body": body, "to_channel": "general", "to": None,
        "from_model": "claude-fable-5", "from_provider": "anthropic",
        "force_buffer": force_buffer})

def battery(build, label, expect_cured):
    print(f"\n=== {label}: {build.name} (md5 {md5(build)}) ===")

    # C1 ROUND-TRIP control: force-buffer post -> restore -> db==1, feed==1
    bus, para, env = synth_bus()
    marker = "probe-g575-roundtrip"
    r = run_cli(build, env, "post", "--from", "bolt", "--subject", marker,
                "--body", "roundtrip", "--force-buffer")
    mid = r.stdout.split("VM-local ")[1].split(" ")[0]
    r2 = run_cli(build, env, "restore")
    check(f"{label}-C1 round-trip intact (db=1, feed=1, pending drained)",
          r2.returncode == 0 and db_count(bus, marker) == 1 and feed_count(bus, mid) == 1
          and not list((para / "pending").glob("*.md")))

    # C2 FEED-DUP: restore re-run after simulated partial crash (archive step lost)
    bus, para, env = synth_bus()
    marker = "probe-g575-feeddup"
    r = run_cli(build, env, "post", "--from", "bolt", "--subject", marker,
                "--body", "feeddup", "--force-buffer")
    mid = r.stdout.split("VM-local ")[1].split(" ")[0]
    snap = Path(tempfile.mkdtemp(prefix="pend_snap_")) / "pending"
    shutil.copytree(para / "pending", snap)
    run_cli(build, env, "restore")
    shutil.rmtree(para / "pending"); shutil.copytree(snap, para / "pending")  # crash-before-archive
    run_cli(build, env, "restore")
    n_feed, n_db = feed_count(bus, mid), db_count(bus, marker)
    if expect_cured:
        check(f"{label}-C2 feed dedup on re-run (feed=1)", n_feed == 1, f"feed={n_feed}")
    else:
        check(f"{label}-C2 finding #1 REPRODUCED (feed dup=2)", n_feed == 2, f"feed={n_feed}")
    check(f"{label}-C2b db stays correct either way (db=1)", n_db == 1, f"db={n_db}")

    # C3 COLLISION (in-process, one colliding redraw then unique): FIRST must survive
    bus, para, env = synth_bus()
    mod = load_module(build, env)
    ids = ["1799999999_000001_c0111d", "1799999999_000001_c0111d", "1799999999_000002_fresh1"]
    orig_mk = mod._mk_msg_id
    mod._mk_msg_id = lambda: ids.pop(0) if ids else orig_mk()
    rc1 = mod.cmd_post(mk_args(mod, "FIRST-BODY"))
    rc2 = mod.cmd_post(mk_args(mod, "SECOND-BODY"))
    pend = sorted((para / "pending").glob("*.md"))
    first_alive = any("FIRST-BODY" in p.read_text() for p in pend)
    second_alive = any("SECOND-BODY" in p.read_text() for p in pend)
    if expect_cured:
        check(f"{label}-C3 collision redraw: BOTH messages alive",
              rc1 == 0 and rc2 == 0 and first_alive and second_alive and len(pend) == 2,
              f"pend={len(pend)}")
    else:
        check(f"{label}-C3 finding #2 REPRODUCED: FIRST silently lost",
              rc1 == 0 and rc2 == 0 and (not first_alive) and second_alive and len(pend) == 1,
              f"pend={len(pend)}")

    # C4 COLLISION-EXHAUST (id generator stuck on one value)
    bus, para, env = synth_bus()
    mod = load_module(build, env)
    mod._mk_msg_id = lambda: "1799999999_000009_deadaa"
    rc1 = mod.cmd_post(mk_args(mod, "FIRST-BODY"))
    rc2 = mod.cmd_post(mk_args(mod, "SECOND-BODY"))
    pend = sorted((para / "pending").glob("*.md"))
    first_alive = any("FIRST-BODY" in p.read_text() for p in pend)
    if expect_cured:
        check(f"{label}-C4 stuck-id: post REFUSED loud (rc=4), FIRST intact",
              rc1 == 0 and rc2 == 4 and first_alive and len(pend) == 1, f"rc2={rc2}")
    else:
        check(f"{label}-C4 stuck-id: silent overwrite again (rc=0, FIRST gone)",
              rc1 == 0 and rc2 == 0 and not first_alive and len(pend) == 1, f"rc2={rc2}")

    # C5 LIVE-PATH control: bus UP, no force-buffer -> ghost .md + feed line
    bus, para, env = synth_bus()
    marker = "probe-g575-livepath"
    r = run_cli(build, env, "post", "--from", "bolt", "--subject", marker, "--body", "live")
    mid = r.stdout.split("LIVE bus ")[1].split(" ")[0]
    ghost = (bus / "messages" / f"{mid}.md").exists()
    check(f"{label}-C5 live-path unchanged (ghost .md + feed=1)",
          r.returncode == 0 and ghost and feed_count(bus, mid) == 1)

print(f"ORIGINAL md5 pre: {md5(ORIGINAL)} (expect {EXPECT_ORIG_MD5})")
assert md5(ORIGINAL) == EXPECT_ORIG_MD5, "live engine md5 mismatch — STOP"
battery(ORIGINAL, "ORIG", expect_cured=False)
battery(PROPOSED, "PROP", expect_cured=True)
post = md5(ORIGINAL)
check("live engine untouched (md5 pre==post)", post == EXPECT_ORIG_MD5, post)

n_ok = sum(1 for _, ok in results if ok)
print(f"\n{'='*50}\nBATTERY: {n_ok}/{len(results)} PASS")
sys.exit(0 if n_ok == len(results) else 1)
