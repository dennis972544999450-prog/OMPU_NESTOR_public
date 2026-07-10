#!/usr/bin/env python3
"""Probe: proposed fail-closed cure for smoke_auto_resolve vacuous-anchor (gen-559 finding).
Technique = gen-559: spec_from_file_location import + monkeypatched module-level run().
NEVER touches live bus.py / bus.db / network. Engine file on seat NOT touched.
Runs the SAME battery against ORIGINAL and PATCHED to prove the flip."""
import importlib.util, io, subprocess, sys, contextlib
from pathlib import Path

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

UNIT_OK = "...\nPASS: 5/5\n"
SHIELD = "3 deliberately-open thread(s) shielded\n"
GOOD_LIVE   = SHIELD + "[dry-run] Would auto-resolve 4 thread(s):\n - old chatter\n - stale ping\n"
LEAK_LIVE   = SHIELD + "[dry-run] Would auto-resolve 4 thread(s):\n - LEASE: repair window\n"
DRIFT_LEAK  = SHIELD + "Would resolve (dry-run) 4 thread(s):\n - LEASE: repair window\n"   # header drifted, protected subject IS listed
DRIFT_CLEAN = SHIELD + "Would resolve (dry-run) 2 thread(s):\n - old chatter\n"            # header drifted, no leak
NO_SHIELD   = "[dry-run] Would auto-resolve 1 thread(s):\n - old chatter\n"

def cp(out, rc=0):
    return subprocess.CompletedProcess(args=[], returncode=rc, stdout=out, stderr="")

def run_main(mod, live_out):
    calls = {"n": 0}
    def fake_run(cmd):
        calls["n"] += 1
        return cp(UNIT_OK) if calls["n"] == 1 else cp(live_out)
    mod.run = fake_run
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        rc = mod.main()
    return rc, out.getvalue() + err.getvalue()

CASES = [  # (name, live_output, expected_rc_original, expected_rc_patched)
    ("GOOD control PASS",          GOOD_LIVE,   0, 0),
    ("B1 leak, correct header",    LEAK_LIVE,   1, 1),
    ("B2 leak under DRIFTED header", DRIFT_LEAK, 0, 1),  # THE FLIP: false-green -> fail-closed
    ("A2 drifted header, clean",   DRIFT_CLEAN, 0, 1),  # vacuous PASS -> loud fail (axis unverifiable)
    ("B3 shield anchor drift",     NO_SHIELD,   1, 1),
]

def battery(path, col):
    mod_path = Path(path)
    ok = 0
    for name, live, exp_orig, exp_patch in CASES:
        exp = exp_orig if col == "orig" else exp_patch
        mod = load(mod_path, f"smoke_{col}_{ok}")
        rc, _ = run_main(mod, live)
        status = "PASS" if rc == exp else f"FAIL (rc={rc}, expected {exp})"
        print(f"  [{col}] {name}: {status}")
        ok += (rc == exp)
    return ok

if __name__ == "__main__":
    orig = sys.argv[1]; patched = sys.argv[2]
    print("original engine (expected: documents the bug):")
    a = battery(orig, "orig")
    print("patched proposal (expected: bug cured, no regression):")
    b = battery(patched, "patch")
    total = a + b
    print(f"TOTAL {total}/{len(CASES)*2}")
    sys.exit(0 if total == len(CASES)*2 else 1)
