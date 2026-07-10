#!/usr/bin/env python3
"""Divergent verify of Bolt gen-573 cure-proposal. Nestor gen-1000.
Own vectors, NOT Bolt's battery. Stubs run() at module level; asserts rc AND which fail-message fired."""
import importlib.util, io, sys, contextlib
from subprocess import CompletedProcess

ORIG = "/sessions/funny-quirky-carson/mnt/OMPU_shared/bus/smoke_auto_resolve_protected.py"
PROP = "/sessions/funny-quirky-carson/mnt/OMPU_shared/nestor_repos/public/crystals/smoke_auto_resolve_protected_PROPOSED_gen573.py"

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

UNIT_OK = CompletedProcess([], 0, stdout="...\nPASS: 5/5\n", stderr=None)
def live(out, rc=0): return CompletedProcess([], rc, stdout=out, stderr=None)

SHIELD = "3 deliberately-open thread(s) shielded\n"
MARK = "[dry-run] Would auto-resolve"

# vector: (name, unit_cp, live_cp, expect_orig_rc, expect_patched_rc, patched_fail_substr_or_None)
VECTORS = [
 ("V1 GOOD ctrl", UNIT_OK, live(SHIELD+MARK+"\n  - thread old-chat\n"), 0, 0, None),
 ("V2 case-drift+leak (MY drift variant)", UNIT_OK,
   live(SHIELD+"[dry-run] would auto-resolve\n  - LEASE: seat-7\n"), 0, 1, "candidate marker"),
 ("V3 double-marker, leak after 1st", UNIT_OK,
   live(SHIELD+MARK+"\n  - LEASE: x\n"+MARK+"\n  - clean\n"), 1, 1, None),
 ("V4 lowercase leak no over-tighten", UNIT_OK,
   live(SHIELD+MARK+"\n  - lease: informal word\n"), 0, 0, None),
 ("V5 unit-fail short-circuit", CompletedProcess([],1,stdout="boom",stderr=None),
   live(SHIELD+MARK+"\n"), 1, 1, "isolated"),
 ("V6 no-shield-report order", UNIT_OK, live("nothing here\n"), 1, 1, "shield report"),
 ("V7 shielded=0 order", UNIT_OK,
   live("0 deliberately-open thread(s) shielded\n"), 1, 1, "shield count is zero"),
 ("V8 SPINE leak parity", UNIT_OK, live(SHIELD+MARK+"\n  - SPINE rebuild\n"), 1, 1, None),
]

def drive(mod, unit_cp, live_cp):
    calls = {"n": 0}
    def stub(cmd):
        calls["n"] += 1
        return unit_cp if calls["n"] == 1 else live_cp
    mod.run = stub
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = mod.main()
    return rc, err.getvalue()

fails = 0
for name, u, l, eo, ep, psub in VECTORS:
    ro, _ = drive(load(ORIG, "orig"), u, l)
    rp, perr = drive(load(PROP, "prop"), u, l)
    ok = (ro == eo and rp == ep and (psub is None or psub in perr))
    print(f"{'PASS' if ok else 'FAIL'} {name}: orig rc={ro} (exp {eo}), patched rc={rp} (exp {ep})"
          + (f", patched-fail-msg has {psub!r}: {psub in perr}" if psub else ""))
    if not ok: fails += 1
print(f"\n{'ALL GREEN' if fails==0 else f'{fails} FAILED'} / {len(VECTORS)} vectors")
sys.exit(1 if fails else 0)
