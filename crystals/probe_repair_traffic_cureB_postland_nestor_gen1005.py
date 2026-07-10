#!/usr/bin/env python3
"""
probe_repair_traffic_cureB_postland_nestor_gen1005.py  (Nestor gen-1005)

POST-LAND DIVERGENT VERIFY of Cure B landed on tools/repair_traffic.py
(3a37a444 -> post-land md5 asserted below).

Divergence from Bolt gen-561 probe (f68105e1): his probe imports the REAL
predicates but MODELS the preempt-loop variants in probe code, because the
cures did not exist in the engine yet. This probe drives the REAL, LANDED
cmd_acquire end-to-end (argparse.Namespace -> cmd_acquire -> state on disk in
a throwaway tempdir). Any seam between "modeled loop" and "actual landed loop"
shows up here and nowhere else.

Lineage: gen-560 (Bolt, finding) -> gen-0995 (Nestor, Cure-A=double-grant,
Cure-B endorsed) -> gen-561 (Bolt, cure space closed, B recommended)
-> gen-1005 (Nestor, LAND under Den's 2026-07-10 zero-approvals directive).

Never touches live repair_leases.json / network. Engine opened read-only.
"""
import glob, importlib.util, tempfile, hashlib, io, sys, contextlib
from pathlib import Path
from argparse import Namespace

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
ENGINE = f"{S}/tools/repair_traffic.py"
BAK = f"{S}/tools/repair_traffic.py.bak_nestor_gen1005_preCureB_3a37a444"

md5 = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
md5_pre = md5(ENGINE)

spec = importlib.util.spec_from_file_location("rt_cureB_1005", ENGINE)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

TMP = tempfile.mkdtemp(prefix="rt_cureB_1005_")
rt.ROOT = Path(TMP)
rt.STATE_PATH = rt.ROOT / "repair_leases.json"
rt.DASHBOARD_PATH = rt.ROOT / "REPAIR_TRAFFIC_BOARD.md"
rt.LOCK_PATH = rt.ROOT / ".repair_leases.lock"

PASS = []
def check(name, cond):
    PASS.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def acq(target, owner, force=False, minutes=30):
    """Drive the REAL cmd_acquire; capture rc + stderr."""
    ns = Namespace(target=target, owner=owner, force=force,
                   minutes=minutes, action="probe", note="")
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = rt.cmd_acquire(ns)
    return rc, err.getvalue()

def reset(*leases):
    rt.STATE_PATH.write_text('{"leases": []}')
    for tgt, own in leases:
        rc, _ = acq(tgt, own)
        assert rc == 0, f"seed {own}/{tgt} failed"

def actives():
    st = rt.load_state()
    return [(x["target"], x["owner"]) for x in st["leases"] if x["status"] == "active"]

def covered(query):
    st = rt.load_state()
    return [x["owner"] for x in rt.find_coverage(st, query)]

print(f"engine md5 pre-run: {md5_pre}")

# V1 REPRO-FLIP: the original gen-560 collateral-preempt vector must now REFUSE.
reset(("all-sites", "nestor"))
rc, err = acq("site:x", "phi", force=True)
check("V1 narrow force under broad wildcard -> rc=1 SCOPE_REFUSED",
      rc == 1 and "SCOPE_REFUSED" in err)
check("V2 broad lease SURVIVES, nothing granted",
      actives() == [("all-sites", "nestor")])
check("V3 unrelated site:y still covered (the gen-560 collision window closed)",
      covered("site:y") == ["nestor"])

# V4 state-purity after refusal: no partial preempt, no phantom lease.
st = rt.load_state()
check("V4 refusal leaves exactly 1 lease total, zero 'preempted'",
      len(st["leases"]) == 1 and all(x["status"] == "active" for x in st["leases"]))

# V5 narrow-vs-narrow emergency STILL works (no over-refusal).
reset(("site:x", "bolt"), ("site:y", "nestor"))
rc, err = acq("site:x", "phi", force=True)
check("V5 narrow-vs-narrow force -> preempt + grant",
      rc == 0 and ("site:x", "phi") in actives() and ("site:x", "bolt") not in actives())
check("V6 unrelated narrow site:y untouched by V5 preempt",
      ("site:y", "nestor") in actives())

# V7 genuinely-broad acquire subsumes narrows (broad acquirer is NOT refused).
reset(("site:x", "phi"), ("site:y", "bolt"))
rc, _ = acq("all-sites", "petrovich", force=True)
check("V7 broad force over narrows -> both preempted, broad sole cover",
      rc == 0 and actives() == [("all-sites", "petrovich")])

# V8 wildcard-vs-wildcard: mutual coverage = not STRICTLY broader -> preempt allowed.
reset(("all", "nestor"))
rc, _ = acq("all-sites", "petrovich", force=True)
check("V8 wildcard-vs-wildcard force -> preempt+grant (mutual cover, no strict order)",
      rc == 0 and actives() == [("all-sites", "petrovich")])

# V9 non-force path unchanged: HELD, not SCOPE_REFUSED.
reset(("all-sites", "nestor"))
rc, err = acq("site:x", "phi", force=False)
check("V9 non-force under blocker -> HELD (legacy path intact)",
      rc == 1 and "HELD" in err and "SCOPE_REFUSED" not in err)

# V10 priority gate fires BEFORE Cure B: low-priority force under broad -> HELD.
reset(("all-sites", "petrovich"))          # priority 100
rc, err = acq("site:x", "nestor", force=True)  # priority 70
check("V10 low-prio force under high-prio broad -> HELD (priority gate first)",
      rc == 1 and "HELD" in err and "SCOPE_REFUSED" not in err)

# V11 same-tier >= co-note UNTOUCHED: equal-priority narrow force still preempts.
reset(("site:x", "nestor"),)
rc, _ = acq("site:x", "jee", force=True)   # both default/70? use real map
# nestor=70; jee likely default 10 -> would be HELD. Use two 100-tier owners instead.
reset(("site:x", "phi"),)
rc, _ = acq("site:x", "petrovich", force=True)
check("V11 same-tier (100 vs 100) narrow force still preempts (>= co-note preserved)",
      rc == 0 and actives() == [("site:x", "petrovich")])

# V12 check-side covers() untouched: narrow lease must NOT clear a broad check.
reset(("site:x", "phi"),)
check("V12 check-side directional covers() unchanged (gen-391 guard intact)",
      covered("all-sites") == [] and covered("site:x") == ["phi"])

# V13 bodies: engine read-only during probe; bak == pre-cure bytes.
check("V13 engine md5 pre==post run", md5(ENGINE) == md5_pre)
check("V14 backup exists and == 3a37a444 (rollback guaranteed)",
      md5(BAK) == "3a37a4446f22cda05ca0d8cd910ab136")

n_ok = sum(PASS)
print(f"\n{'GREEN' if all(PASS) else 'RED'}: {n_ok}/{len(PASS)}")
sys.exit(0 if all(PASS) else 1)
