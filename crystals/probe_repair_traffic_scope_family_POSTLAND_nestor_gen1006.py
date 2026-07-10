#!/usr/bin/env python3
"""Nestor gen-1006 — POST-LAND VERIFY of scope-family fix (Cure C-lite) on
tools/repair_traffic.py.

Axis: gen-560 -> gen-0995 -> gen-561 -> gen-1005 (Cure B land) -> Petrovich
second-eye 1783667748 (V8 scope-family FALSE-GREEN) -> Bolt gen-592 (matrix,
"fix = BOTH predicates") -> THIS LAND (nestor gen-1006).

Landed change: scope_family() + domain-aware covers() + family-aware
conflicts() == symmetric covers. Oracle == Bolt gen-592 probe (1037f67b),
reimplemented independently here.

Contract (locked BEFORE run):
  F1-F3   gen-592 P1-P3 survive (Cure B core intact).
  F4      gen-592 P4 FLIPS: all -> all-sites equal-tier force = SCOPE_REFUSED,
          universal holder survives.
  F5      gen-592 P5 FLIPS: worker:* -> site:* force = clean COEXIST (no
          blocker, no preempt, worker holder alive).
  F6      gen-592 P6 FLIPS: after F5, check worker:oags-dev = LEASE_OK with
          the WORKER holder; site:* does NOT cover it.
  F7      gen-592 P10 survives: all-sites <-> site:* equal-tier handoff legal.
  F8      gen-592 P9 closed: conflicts(worker:*, site:*) now False.
  M       full 8x8 matrix live covers() vs oracle: 0 divergent cells (was 16).
  V-A     (semantic change, predicted) exact target 'test:repair-board'
          coexists under all-sites without force (old: HELD).
  V-B     check 'all' with only site:* + worker:* held = NO_LEASE (old:
          false green via covers(site:*, all)=True).
  V-C     universal escalation legal: site:* held, 'all' force equal-tier
          subsumes (universal not "strictly narrower", broader-filter empty
          in the refuse direction... precisely: covers(site:*,'all')=False =>
          not broader => preempt proceeds).
  V-D     '*' <-> 'all' mutual-universal handoff legal (P10-analog).
  V-E     cross-family MEMBERS coexist without force: site:x held,
          worker:y acquire -> ACQUIRED, both active.
  V-F     priority gate still FIRST: low-tier force under same-family
          wildcard -> HELD (not SCOPE_REFUSED).
  H       hygiene: throwaway tempdir, live repair_leases.json untouched,
          backup md5 == a1af8956 (pre-land bytes), live engine md5 stable
          across probe (pre==post), state purity per-case reset.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import sys
import tempfile
from pathlib import Path

S = Path(os.environ.get("OMPU_SHARED", "/sessions/brave-beautiful-pasteur/mnt/OMPU_shared"))
ENGINE = S / "tools" / "repair_traffic.py"
BACKUP = S / "tools" / "repair_traffic.py.bak_nestor_gen1006_preScopeFamily_a1af8956"
PRELAND_MD5 = "a1af8956c0c59ea78469a38f451d1261"

def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()

md5_pre = md5(ENGINE)
assert md5_pre != PRELAND_MD5, "engine still pre-land? fix not applied"
assert md5(BACKUP) == PRELAND_MD5, "backup does not hold pre-land bytes!"

spec = importlib.util.spec_from_file_location("rt", ENGINE)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

TMP = Path(tempfile.mkdtemp(prefix="rt_gen1006_"))
rt.ROOT = TMP
rt.STATE_PATH = TMP / "repair_leases.json"
rt.DASHBOARD_PATH = TMP / "BOARD.md"
rt.LOCK_PATH = TMP / ".lock"

LIVE_STATE = S / "repair_traffic" / "repair_leases.json"
live_state_md5_pre = md5(LIVE_STATE) if LIVE_STATE.exists() else None

def reset():
    if rt.STATE_PATH.exists():
        rt.STATE_PATH.unlink()

def acquire(owner, target, force=False, minutes=30):
    ns = argparse.Namespace(owner=owner, target=target, action="probe",
                            note="", minutes=minutes, force=force)
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        rc = rt.cmd_acquire(ns)
    return rc, out.getvalue() + err.getvalue()

def check(target, owner=None):
    ns = argparse.Namespace(target=target, owner=owner)
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        rc = rt.cmd_check(ns)
    return rc, out.getvalue() + err.getvalue()

def active_targets():
    st = rt.load_state()
    return sorted((x["owner"], x["target"]) for x in st.get("leases", [])
                  if x.get("status") == "active")

# ---------------- independent oracle (== gen-592, reimplemented) -------------
def fam(tok):
    if tok in ("all", "*"): return ("universal", True)
    if tok in ("all-sites", "site:*"): return ("site", True)
    if tok == "worker:*": return ("worker", True)
    if tok.startswith("site:"): return ("site", False)
    if tok.startswith("worker:"): return ("worker", False)
    return ("exact", False)

def covers_oracle(held, query):
    if held == query: return True
    hf, hw = fam(held); qf, _ = fam(query)
    if hf == "universal": return True
    if qf == "universal": return False
    return hw and hf == qf

results = []
def report(name, pred, fact, note=""):
    ok = pred == fact
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: predicted={pred!r} fact={fact!r} {note}")

print("=" * 78)
print("PHASE 1 — gen-592 fixtures: survivors F1-F3, F7; flips F4-F6; P9 close F8")
print("=" * 78)

reset(); acquire("nestor", "all-sites")
rc, msg = acquire("phi", "site:x", force=True)
report("F1 (P1) SCOPE_REFUSED narrow-under-broad survives",
       (1, True, [("nestor", "all-sites")]),
       (rc, "SCOPE_REFUSED" in msg, active_targets()))

reset(); acquire("nestor", "site:x")
rc, msg = acquire("phi", "site:x", force=True)
report("F2 (P2) narrow-vs-narrow preempt survives", (0, [("phi", "site:x")]),
       (rc, active_targets()))

reset(); acquire("nestor", "site:x")
rc, msg = acquire("phi", "all-sites", force=True)
report("F3 (P3) broad-subsumes-narrow survives", (0, [("phi", "all-sites")]),
       (rc, active_targets()))

reset(); acquire("petrovich", "all")
rc, msg = acquire("phi", "all-sites", force=True)
report("F4 (P4 FLIP) all->all-sites force = SCOPE_REFUSED, universal survives",
       (1, True, [("petrovich", "all")]),
       (rc, "SCOPE_REFUSED" in msg, active_targets()))

reset(); acquire("nestor", "worker:*")
rc, msg = acquire("petrovich", "site:*", force=True)
report("F5 (P5 FLIP) worker:* + site:* COEXIST (no preempt)",
       (0, [("nestor", "worker:*"), ("petrovich", "site:*")]),
       (rc, active_targets()))

rc, msg = check("worker:oags-dev")
report("F6 (P6 FLIP) check worker:oags-dev -> WORKER holder, not site:*",
       (0, True), (rc, "owner=nestor" in msg),
       note="coverage must come from worker:*")
report("F6b covers(site:*, worker:oags-dev) is False",
       False, rt.covers("site:*", "worker:oags-dev"))

reset(); acquire("nestor", "all-sites")
rc, msg = acquire("phi", "site:*", force=True)
report("F7 (P10) same-family handoff all-sites -> site:* stays legal",
       (0, [("phi", "site:*")]), (rc, active_targets()))

report("F8 (P9 close) conflicts(worker:*, site:*) now False",
       False, rt.conflicts("worker:*", "site:*"))

print("=" * 78)
print("PHASE 2 — M: full 8x8 covers() matrix vs oracle (predict 0 divergent)")
print("=" * 78)
TOKENS = ["all", "*", "all-sites", "site:*", "site:x", "worker:*",
          "worker:oags-dev", "oags-landing"]
div = [(h, q) for h in TOKENS for q in TOKENS
       if rt.covers(h, q) != covers_oracle(h, q)]
report("M 8x8 matrix divergent cells (was 16)", [], div)

print("=" * 78)
print("PHASE 3 — nestor divergent vectors (beyond gen-592 battery)")
print("=" * 78)

reset(); acquire("nestor", "all-sites")
rc, msg = acquire("bolt", "test:repair-board", force=False)
report("V-A exact target coexists under all-sites (SEMANTIC CHANGE, predicted)",
       (0, [("bolt", "test:repair-board"), ("nestor", "all-sites")]),
       (rc, active_targets()))

reset(); acquire("nestor", "site:*"); acquire("bolt", "worker:*")
rc, msg = check("all")
report("V-B check 'all' under site:*+worker:* = NO_LEASE (false-green closed)",
       (1, True), (rc, "NO_LEASE" in msg))

reset(); acquire("petrovich", "site:*")
rc, msg = acquire("phi", "all", force=True)
report("V-C universal escalation site:*->all force subsumes (legal)",
       (0, [("phi", "all")]), (rc, active_targets()))

reset(); acquire("petrovich", "*")
rc, msg = acquire("phi", "all", force=True)
report("V-D '*'<->'all' mutual-universal handoff legal",
       (0, [("phi", "all")]), (rc, active_targets()))

reset(); acquire("nestor", "site:x")
rc, msg = acquire("bolt", "worker:y", force=False)
report("V-E cross-family members coexist without force",
       (0, [("bolt", "worker:y"), ("nestor", "site:x")]),
       (rc, active_targets()))

reset(); acquire("nestor", "site:*")
rc, msg = acquire("jee", "site:x", force=True)   # jee = default tier 10 < nestor
report("V-F priority gate FIRST: low-tier force -> HELD, not SCOPE_REFUSED",
       (1, True, False), (rc, "HELD" in msg, "SCOPE_REFUSED" in msg))

print("=" * 78)
print("PHASE 4 — hygiene")
print("=" * 78)
report("H1 live engine md5 stable across probe", md5_pre, md5(ENGINE))
report("H2 live repair_leases.json untouched", live_state_md5_pre,
       md5(LIVE_STATE) if LIVE_STATE.exists() else None)
report("H3 backup holds pre-land bytes", PRELAND_MD5, md5(BACKUP))

n_pass = sum(results); n = len(results)
print("=" * 78)
print(f"VERDICT: {n_pass}/{n} {'ALL GREEN' if n_pass == n else 'FAILURES PRESENT'}")
print(f"engine post-land md5: {md5_pre}")
sys.exit(0 if n_pass == n else 1)
