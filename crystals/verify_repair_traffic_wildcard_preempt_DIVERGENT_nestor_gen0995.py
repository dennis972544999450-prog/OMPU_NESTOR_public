#!/usr/bin/env python3
"""
Nestor gen-0995 — INDEPENDENT DIVERGENT verify of Bolt gen-560 finding on
tools/repair_traffic.py (wildcard collateral preemption, LATENT).

Divergence from Bolt's probe (which seeds via cmd_acquire + reads status):
  1. REPRODUCE the finding at the PREDICATE level, not just end-to-end — construct
     state dicts DIRECTLY (bypass cmd_acquire seeding) and drive find_blockers +
     the preempt loop in isolation, so the bug is proven in the engine's decision
     logic, not an artifact of how the probe seeded leases.
  2. NULL-CASE ON SELF: implement the two obvious cures and stress-test them.
     - Cure A "skip wildcard blockers in the preempt loop, still grant the new
       narrow lease" — check whether it silently creates a DIFFERENT collision:
       broad holder AND narrow acquirer both 'active' over the intersection.
     - Cure B "refuse the force-acquire when a broad wildcard blocker would be
       collaterally hit (require ALL blockers scope-precise to preempt)" — check
       it keeps the broad lease active, grants nothing, and still allows the
       legitimate narrow-preempts-narrow emergency.
  3. Confirm the CHECK-side (covers) is unaffected — the bug is preempt-only.

SAFETY: pure synthetic. Module file globals redirected into tempfile.mkdtemp().
Never touches live /Users/denbell/OMPU_shared/repair_traffic/. Engine imported
read-only; md5 asserted pre==post. No network, no __main__ trigger.
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
ENGINE = os.path.join(S, "tools", "repair_traffic.py")


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


PRE = md5(ENGINE)
spec = importlib.util.spec_from_file_location("rt_nestor_probe", ENGINE)
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)


def fresh_root():
    d = tempfile.mkdtemp(prefix="rt_nestor_")
    rt.ROOT = Path(d)
    rt.STATE_PATH = rt.ROOT / "repair_leases.json"
    rt.DASHBOARD_PATH = rt.ROOT / "REPAIR_TRAFFIC_BOARD.md"
    rt.LOCK_PATH = rt.ROOT / ".repair_leases.lock"
    return d


results = []


def rec(name, ok, detail):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def mk_lease(target, owner, status="active", minutes=120):
    ts = rt.now()
    return {
        "id": f"seed_{owner}_{target}",
        "target": target,
        "owner": owner,
        "priority": rt.owner_priority(owner),
        "action": "hold",
        "note": "",
        "status": status,
        "started_at": rt.iso(ts),
        "expires_at": rt.iso(ts + rt.timedelta(minutes=minutes)),
        "proof": "",
    }


# ── 1. PREDICATE-LEVEL PROOF (divergent: no cmd_acquire seeding) ──────────────
# conflicts() itself: does a broad wildcard blocker match a narrow acquire target?
c_broad_narrow = rt.conflicts("all-sites", "site:x")
c_narrow_narrow_diff = rt.conflicts("site:x", "site:y")
rec("P1_conflicts_broad_vs_narrow_TRUE", c_broad_narrow is True,
    f"conflicts('all-sites','site:x')={c_broad_narrow} — broad wildcard matches narrow acquire")
rec("P2_conflicts_two_narrow_FALSE", c_narrow_narrow_diff is False,
    f"conflicts('site:x','site:y')={c_narrow_narrow_diff} — unrelated narrows do NOT match")

# find_blockers on a narrow acquire returns the broad lease as a blocker:
fresh_root()
state = {"schema": "ompu.repair_traffic.v0",
         "leases": [mk_lease("all-sites", "nestor")]}
blockers = rt.find_blockers(state, "site:x")
rec("P3_broad_is_blocker_for_narrow", len(blockers) == 1 and blockers[0]["target"] == "all-sites",
    f"find_blockers(state,'site:x') => {[b['target'] for b in blockers]} (broad lease flagged as blocker)")

# ── 2. END-TO-END FINDING (independent seat, direct-built state) ──────────────
fresh_root()
state = {"schema": "ompu.repair_traffic.v0",
         "leases": [mk_lease("all-sites", "nestor")]}
rt.save_state(state)  # persist so cmd_acquire loads it
a = argparse.Namespace(target="site:x", owner="phi", action="emergency",
                       minutes=30, note="", force=True)
rc = rt.cmd_acquire(a)
st = json.loads(rt.STATE_PATH.read_text())
def status_of(state_, target, owner):
    hits = [x for x in state_["leases"]
            if x["target"] == target and x["owner"].lower() == owner.lower()]
    return hits[-1]["status"] if hits else None
broad = status_of(st, "all-sites", "nestor")
narrow = status_of(st, "site:x", "phi")
rec("F1_finding_confirmed_broad_preempted",
    rc == 0 and narrow == "active" and broad == "preempted",
    f"narrow phi/site:x force-acquire rc={rc} phi={narrow} nestor_broad={broad} "
    f"(CONFIRMED: broad reservation over UNTOUCHED surfaces killed)")
# blast on an unrelated target via the CHECK path:
post_y = rt.cmd_check(argparse.Namespace(target="site:y", owner=None))
rec("F2_unrelated_surface_now_uncovered", post_y == 1,
    f"check site:y after => rc={post_y} (1=NO_LEASE: nestor still believes it holds all-sites)")

# ── 3. NULL-CASE ON SELF: cure A (skip wildcard blockers, still grant) ────────
# Simulate cure A: preempt only scope-precise (non-wildcard, exact-target) blockers.
def cure_A_acquire(state_, target, owner, force):
    """Preempt only precise blockers; skip wildcard blockers; still grant new lease."""
    prio = rt.owner_priority(owner)
    blockers = rt.find_blockers(state_, target)
    precise = [b for b in blockers if b["target"] not in rt.WILDCARDS and b["target"] == target]
    wildcard_blockers = [b for b in blockers if b["target"] in rt.WILDCARDS]
    if blockers:
        top = max(blockers, key=lambda x: int(x.get("priority", 0)))
        can_preempt = force and prio >= int(top.get("priority", 0))
        if not can_preempt:
            return 1, state_
        for b in precise:            # cure A: only precise blockers preempted
            b["status"] = "preempted"
    # still grants the new narrow lease regardless of surviving wildcard blockers
    state_["leases"].append(mk_lease(target, owner))
    return 0, state_

fresh_root()
stateA = {"schema": "x", "leases": [mk_lease("all-sites", "nestor")]}
rcA, stateA = cure_A_acquire(stateA, "site:x", "phi", force=True)
broadA = status_of(stateA, "all-sites", "nestor")
narrowA = status_of(stateA, "site:x", "phi")
# both active over the intersection site:x => a DIFFERENT collision
double_active = (broadA == "active" and narrowA == "active")
rec("A_cureA_creates_double_active_overlap", double_active,
    f"cure A: nestor all-sites={broadA} AND phi site:x={narrowA} — BOTH active over site:x. "
    f"Collateral-preempt traded for a DOUBLE-GRANT overlap on the intersection "
    f"(the naive cure is its own bug — NULL-CASE rejects it)")

# ── 4. cure B (refuse when a broad blocker would be collaterally hit) ──────────
def cure_B_acquire(state_, target, owner, force):
    """Force-acquire preempts ONLY if every blocker is scope-precise (exact target).
    A broad wildcard blocker that the narrow target does not itself cover => REFUSE."""
    prio = rt.owner_priority(owner)
    blockers = rt.find_blockers(state_, target)
    if blockers:
        top = max(blockers, key=lambda x: int(x.get("priority", 0)))
        can_preempt = force and prio >= int(top.get("priority", 0))
        # scope guard: refuse if any blocker is broader than the acquire target
        broader = [b for b in blockers
                   if b["target"] in rt.WILDCARDS and target not in rt.WILDCARDS]
        if not can_preempt or broader:
            return 1, state_
        for b in blockers:
            b["status"] = "preempted"
    state_["leases"].append(mk_lease(target, owner))
    return 0, state_

# 4a: narrow force-acquire vs broad lease => REFUSE, broad survives, nothing granted
fresh_root()
stateB = {"schema": "x", "leases": [mk_lease("all-sites", "nestor")]}
rcB, stateB = cure_B_acquire(stateB, "site:x", "phi", force=True)
broadB = status_of(stateB, "all-sites", "nestor")
narrowB = status_of(stateB, "site:x", "phi")
rec("B1_cureB_refuses_broad_collateral",
    rcB == 1 and broadB == "active" and narrowB is None,
    f"cure B narrow-vs-broad: rc={rcB}(1=refuse) broad={broadB}(survives) narrow={narrowB}(not granted) "
    f"— no collateral, no double-grant")

# 4b: legitimate narrow-preempts-narrow emergency STILL works under cure B
fresh_root()
stateB2 = {"schema": "x", "leases": [mk_lease("site:x", "hausmaster"),
                                     mk_lease("site:y", "nestor")]}
rcB2, stateB2 = cure_B_acquire(stateB2, "site:x", "phi", force=True)
x_st = status_of(stateB2, "site:x", "hausmaster")
y_st = status_of(stateB2, "site:y", "nestor")
new_x = status_of(stateB2, "site:x", "phi")
rec("B2_cureB_preserves_legit_narrow_preempt",
    rcB2 == 0 and x_st == "preempted" and y_st == "active" and new_x == "active",
    f"cure B narrow-vs-narrow: rc={rcB2} hausmaster/site:x={x_st}(preempted) "
    f"nestor/site:y={y_st}(untouched) phi/site:x={new_x}(granted) — emergency path intact")

# 4c: broad force-acquire preempting a narrow (acquirer IS the wildcard) still OK
fresh_root()
stateB3 = {"schema": "x", "leases": [mk_lease("site:x", "nestor")]}
rcB3, stateB3 = cure_B_acquire(stateB3, "all-sites", "phi", force=True)
narrowpre = status_of(stateB3, "site:x", "nestor")
broadnew = status_of(stateB3, "all-sites", "phi")
rec("B3_cureB_broad_acquire_still_preempts_narrow",
    rcB3 == 0 and narrowpre == "preempted" and broadnew == "active",
    f"cure B broad-acquires: rc={rcB3} nestor/site:x={narrowpre}(preempted by intended broad) "
    f"phi/all-sites={broadnew} — a genuinely-broad acquire legitimately subsumes narrows")

# ── 5. CHECK-side unaffected (bug is preempt-only) ────────────────────────────
rec("CK_covers_directional_unchanged",
    rt.covers("all-sites", "site:y") is True and rt.covers("site:x", "all-sites") is False,
    "covers() directional guard intact: broad covers narrow query; narrow does NOT cover broad query")

POST = md5(ENGINE)
rec("ENGINE_md5_pre_eq_post", PRE == POST, f"pre={PRE} post={POST} (read-only, engine untouched)")

npass = sum(1 for _, ok, _ in results if ok)
print(f"\n=== {npass}/{len(results)} PASS ===")
print(f"engine md5: {PRE}")
raise SystemExit(0 if npass == len(results) else 1)
