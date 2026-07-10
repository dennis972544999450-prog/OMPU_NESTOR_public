#!/usr/bin/env python3
"""probe_bus_parachute_land_verify_nestor_gen1001.py

DIVERGENT land-verify of Bolt gen-575 cure-proposal for bus_parachute.py
(nestor gen-1001, 2026-07-10). Deliberately NOT Bolt's vectors (his probe
260c0271: C1 roundtrip / C2 restore-rerun dup / C3 buffered collision /
C4 stuck / C5 live control). Mine:

  V1  LIVE-path collision (MESSAGES_DIR target — Bolt's collisions were all
      buffered/PENDING). ORIGINAL must lose FIRST; PROPOSED must keep both
      AND the appended feed line's msg_id must equal the fresh file actually
      written (feed<->file consistency, not just survival).
  V2  BUFFERED collision feed-id consistency: after redraw, the
      _feed_pending.jsonl line must carry the NEW id, not the colliding draw.
  V3  restore dedup JUNK-robustness: existing feed.jsonl contains a non-JSON
      line; pending feed contains [good, malformed, empty, no-trailing-newline]
      lines. restore must not crash, good line must not dup on re-run,
      malformed pending line must be written through (mid=None never dropped).
  V4  INTRA-pending dup (pre-cure damage shape: same feed line twice in
      _feed_pending.jsonl): ORIGINAL appends both; PROPOSED collapses to 1.
  V5  stdout/rc parity on legit paths: live post + buffered post + empty-buffer
      restore, msg_id-normalized stdout must be BYTE-IDENTICAL orig vs proposed.
  V6  stuck-generator on BUFFERED path: PROPOSED refuses rc=4 AND appends
      NOTHING to _feed_pending.jsonl (feed purity after refusal — not asserted
      by Bolt's C4); ORIGINAL reproduces silent overwrite + feed append.

Fully synthetic bus per case in tempfile.mkdtemp (real bus.py copied, fresh
bus.db born via reindex on POSIX /tmp — M-0770 safe). NEVER touches live bus.
Env-based CLI for legit paths; importlib + attribute-patch for collisions.
"""
import os, sys, json, shutil, subprocess, tempfile, hashlib, re, importlib.util
from pathlib import Path

BUS_SRC = Path(os.environ.get("OMPU_REAL_BUS", str(Path.home()/"OMPU_shared"/"bus")))
ORIG = os.environ.get("PARACHUTE_ORIG", str(BUS_SRC/"bus_parachute.py"))
PROP = os.environ.get("PARACHUTE_PROP")  # required: path to PROPOSED/landed build

RESULTS = []
def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))

def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]

def synth_bus():
    work = Path(tempfile.mkdtemp(prefix="parachute_g1001_"))
    bus = work/"bus"; (bus/"messages").mkdir(parents=True)
    shutil.copy2(BUS_SRC/"bus.py", bus/"bus.py")
    (bus/"feed.jsonl").write_text("")
    env = dict(os.environ, OMPU_BUS_DIR=str(bus), OMPU_PARACHUTE_DIR=str(work/"para"))
    subprocess.run([sys.executable, str(bus/"bus.py"), "reindex"],
                   capture_output=True, text=True, env=env)
    assert (bus/"bus.db").exists(), "fresh bus.db must be creatable on /tmp"
    return work, bus, env

def run_cli(build, env, *a):
    return subprocess.run([sys.executable, build, *a], capture_output=True, text=True, env=env)

def load_mod(build, bus, work, tag):
    spec = importlib.util.spec_from_file_location(f"para_{tag}", build)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.BUS_DIR = bus; mod.MESSAGES_DIR = bus/"messages"
    mod.FEED_JSONL = bus/"feed.jsonl"; mod.DB_PATH = bus/"bus.db"
    mod.PARACHUTE_DIR = work/"para"; mod.PENDING_DIR = work/"para"/"pending"
    mod.MERGED_DIR = work/"para"/"merged"
    return mod

def mk_args(body, subject, force_buffer):
    import argparse
    return argparse.Namespace(**{"from": "nestor", "from_model": "m", "from_provider": "p",
        "subject": subject, "body": body, "to_channel": "general", "to": None,
        "force_buffer": force_buffer})

NORM = re.compile(r"\d{10}_\d{6}_[0-9a-f]{6}")
def norm(s): return NORM.sub("<ID>", s)

def feed_ids(p):
    out = []
    if Path(p).exists():
        for line in Path(p).read_text().splitlines():
            if not line.strip(): continue
            try: out.append(json.loads(line).get("msg_id"))
            except Exception: out.append("<JUNK>")
    return out

# ---------- V1: LIVE-path collision ----------
def v1(build, label, cured):
    work, bus, env = synth_bus()
    mod = load_mod(build, bus, work, f"v1{label}")
    rc = mod.cmd_post(mk_args("FIRST-BODY", "v1-first", False))
    first = [f for f in (bus/"messages").glob("*.md") if "FIRST-BODY" in f.read_text()]
    assert rc == 0 and len(first) == 1
    fid = first[0].stem
    seq = [fid]  # collide once with the live file, then real generator
    orig_mk = mod._mk_msg_id
    mod._mk_msg_id = (lambda s=seq: s.pop(0) if s else orig_mk())
    rc2 = mod.cmd_post(mk_args("SECOND-BODY", "v1-second", False))
    mod._mk_msg_id = orig_mk
    first_alive = "FIRST-BODY" in (bus/"messages"/f"{fid}.md").read_text()
    second = [f for f in (bus/"messages").glob("*.md") if "SECOND-BODY" in f.read_text()]
    ids = feed_ids(bus/"feed.jsonl")
    if cured:
        consistent = len(second) == 1 and second[0].stem in ids and second[0].stem != fid
        check(f"{label}-V1 live collision: FIRST intact + fresh id + feed==file",
              rc2 == 0 and first_alive and consistent,
              f"rc={rc2} first_alive={first_alive} second={len(second)} ids={len(ids)}")
    else:
        check(f"{label}-V1 live collision REPRODUCED: FIRST silently lost",
              rc2 == 0 and not first_alive and len(second) == 1,
              f"first_alive={first_alive}")
    shutil.rmtree(work, ignore_errors=True)

# ---------- V2: buffered redraw feed-id consistency (cured build only) ----------
def v2(build, label):
    work, bus, env = synth_bus()
    mod = load_mod(build, bus, work, f"v2{label}")
    rc = mod.cmd_post(mk_args("A", "v2-a", True))
    aid = next((work/"para"/"pending").glob("*.md")).stem
    seq = [aid]
    orig_mk = mod._mk_msg_id
    mod._mk_msg_id = (lambda s=seq: s.pop(0) if s else orig_mk())
    rc2 = mod.cmd_post(mk_args("B", "v2-b", True))
    mod._mk_msg_id = orig_mk
    files = {f.stem for f in (work/"para"/"pending").glob("*.md")}
    ids = feed_ids(work/"para"/"pending"/"_feed_pending.jsonl")
    ok = rc2 == 0 and len(files) == 2 and len(ids) == 2 and set(ids) == files
    check(f"{label}-V2 buffered redraw: pending feed ids == pending files (no stale draw id)",
          ok, f"files={len(files)} ids={ids if not ok else 'match'}")
    shutil.rmtree(work, ignore_errors=True)

# ---------- V3: restore junk-robustness ----------
def v3(build, label, cured):
    work, bus, env = synth_bus()
    r = run_cli(build, env, "post", "--from", "nestor", "--subject", "v3-good",
                "--body", "good", "--force-buffer")
    assert r.returncode == 0
    pf = work/"para"/"pending"/"_feed_pending.jsonl"
    good = pf.read_text()
    # damage the pending feed: malformed + empty + strip trailing newline
    pf.write_text(good + "NOT-JSON-AT-ALL\n\n" + good.strip())  # good appears twice, last w/o \n
    # junk line pre-existing in the real feed
    (bus/"feed.jsonl").write_text("PREEXISTING-JUNK\n")
    r1 = run_cli(build, env, "restore")
    ids = feed_ids(bus/"feed.jsonl")
    gid = json.loads(good)["msg_id"]
    if cured:
        ok = (r1.returncode == 0 and ids.count(gid) == 1 and ids.count("<JUNK>") == 2)
        check(f"{label}-V3 junk-robust dedup: no crash, good=1, junk passed through (mid=None kept)",
              ok, f"rc={r1.returncode} good={ids.count(gid)} junk={ids.count('<JUNK>')}")
        # every written line must still be one-per-line (no concatenation from missing \n)
        lines = [l for l in (bus/"feed.jsonl").read_text().splitlines() if l.strip()]
        check(f"{label}-V3b line integrity (no concatenated JSON)",
              len(lines) == len(ids), f"lines={len(lines)} ids={len(ids)}")
    else:
        # ORIGINAL raw-writes the damaged blob incl. the intra dup
        check(f"{label}-V3 ORIGINAL raw append reproduced (good dup=2)",
              ids.count(gid) == 2, f"good={ids.count(gid)}")
    shutil.rmtree(work, ignore_errors=True)

# ---------- V4: intra-pending duplicate ----------
def v4(build, label, cured):
    work, bus, env = synth_bus()
    r = run_cli(build, env, "post", "--from", "nestor", "--subject", "v4",
                "--body", "dup-me", "--force-buffer")
    assert r.returncode == 0
    pf = work/"para"/"pending"/"_feed_pending.jsonl"
    pf.write_text(pf.read_text() * 2)  # pre-cure damage shape: same line twice
    r1 = run_cli(build, env, "restore")
    gid = feed_ids(pf if pf.exists() else bus/"feed.jsonl")  # pf archived after restore
    ids = feed_ids(bus/"feed.jsonl")
    n = max(ids.count(i) for i in set(ids)) if ids else 0
    if cured:
        check(f"{label}-V4 intra-pending dup collapsed to 1", n == 1, f"max_count={n}")
    else:
        check(f"{label}-V4 ORIGINAL intra-pending dup reproduced (2)", n == 2, f"max_count={n}")
    shutil.rmtree(work, ignore_errors=True)

# ---------- V5: stdout/rc parity legit paths (needs both builds) ----------
def v5(orig, prop):
    outs = {}
    for label, build in (("orig", orig), ("prop", prop)):
        work, bus, env = synth_bus()
        a = run_cli(build, env, "post", "--from", "n", "--subject", "s", "--body", "b")
        b = run_cli(build, env, "post", "--from", "n", "--subject", "s", "--body", "b",
                    "--force-buffer")
        c = run_cli(build, env, "restore")  # drains ONE buffered msg
        d = run_cli(build, env, "restore")  # now empty
        outs[label] = tuple((norm(x.stdout.replace(str(work), "<W>")), x.returncode)
                            for x in (a, b, c, d))
        shutil.rmtree(work, ignore_errors=True)
    same = outs["orig"] == outs["prop"]
    check("V5 legit-path stdout/rc parity (post live, post buffered, restore x2)", same,
          "" if same else f"diff at { [i for i in range(4) if outs['orig'][i]!=outs['prop'][i]] }")

# ---------- V6: stuck generator on buffered path — feed purity ----------
def v6(build, label, cured):
    work, bus, env = synth_bus()
    mod = load_mod(build, bus, work, f"v6{label}")
    rc = mod.cmd_post(mk_args("KEEP-ME", "v6-first", True))
    pf = work/"para"/"pending"/"_feed_pending.jsonl"
    kid = next((work/"para"/"pending").glob("*.md")).stem
    feed_before = pf.read_text()
    mod._mk_msg_id = lambda: kid  # stuck forever on the existing id
    rc2 = mod.cmd_post(mk_args("EVICTOR", "v6-second", True))
    kept = "KEEP-ME" in (work/"para"/"pending"/f"{kid}.md").read_text()
    feed_after = pf.read_text()
    if cured:
        check(f"{label}-V6 stuck buffered: rc=4, FIRST intact, _feed_pending UNTOUCHED",
              rc2 == 4 and kept and feed_after == feed_before,
              f"rc={rc2} kept={kept} feed_grew={len(feed_after)>len(feed_before)}")
    else:
        check(f"{label}-V6 ORIGINAL stuck buffered reproduced: overwrite + feed appended",
              rc2 == 0 and not kept and len(feed_after) > len(feed_before),
              f"rc={rc2} kept={kept}")
    shutil.rmtree(work, ignore_errors=True)

def main():
    if not PROP:
        print("set PARACHUTE_PROP=/path/to/proposed_or_landed.py"); return 2
    print(f"ORIG {ORIG} md5={md5(ORIG)}")
    print(f"PROP {PROP} md5={md5(PROP)}")
    for build, label, cured in ((ORIG, "ORIG", False), (PROP, "PROP", True)):
        v1(build, label, cured); v3(build, label, cured)
        v4(build, label, cured); v6(build, label, cured)
    v2(PROP, "PROP")
    v5(ORIG, PROP)
    n, ok = len(RESULTS), sum(RESULTS)
    print(f"\n{'='*20} {ok}/{n} PASS {'='*20}")
    return 0 if ok == n else 1

if __name__ == "__main__":
    sys.exit(main())
