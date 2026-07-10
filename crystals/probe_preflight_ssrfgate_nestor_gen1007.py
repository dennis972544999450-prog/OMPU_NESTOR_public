#!/usr/bin/env python3
"""probe_preflight_ssrfgate_nestor_gen1007 — POST-LAND DIVERGENT VERIFY of the
gen-557 cure land (validate-before-fetch + B-control validation + rc asymmetry).

Loads BOTH engines via importlib: ORIG = .bak_nestor_gen1007_preSSRFgate_f6a8d919,
NEW = live tools/preflight_membership_cure.py. fetch() monkeypatched to a
call-recording stub in BOTH — real network NEVER touched.

CONTRACT LOCKED BEFORE FIRST RUN:
 flips required (ORIG behavior -> NEW behavior):
  C2  invalid-A treated=127.0.0.1        : fetch 3 calls -> 0 ; rc 0 -> 1
  C3  invalid-A treated=attacker.example.com/x : fetch>0 -> 0
  C4  Namespace exp=C treated=evil.internal    : fetch>0 -> 0
  C5  valid-B + control=evil.internal (B-CONTROL GAP, genuinely-new):
      ORIG status BLOCKED_NO_DEN_GO + fetches evil.internal (hostile fetch under
      VALID status — worse class than Bolt's C2) -> NEW INVALID_REQUEST + 0 fetch
  C9  B control==treated : ORIG BLOCKED + double fetch -> NEW INVALID + 0 fetch
 survivors required (no over-tighten):
  C1  valid-A pair   : BLOCKED_NO_DEN_GO both, 2 domains fetched both, rc0 both
  C6  valid-B pair   : BLOCKED_NO_DEN_GO both, 2 domains fetched both
  C7  valid-B solo   : BLOCKED_NO_DEN_GO both, 1 domain fetched both
 invariants:
  C8  GO/PROCEED/DEPLOY status never emitted, either engine, any case
  C11 argparse bad experiment letter -> SystemExit rc2 both engines
  C12 NEW INVALID_REQUEST payload keeps full JSON shape, baseline == []
  C10 md5: live == landed pin, bak == f6a8d919 (checked in shell wrapper)
"""
import importlib.util, io, json, sys, types
from argparse import Namespace
from contextlib import redirect_stdout

BASE = "/sessions/hopeful-youthful-galileo/mnt/OMPU_shared/tools"
PATHS = {"ORIG": f"{BASE}/preflight_membership_cure.py.bak_nestor_gen1007_preSSRFgate_f6a8d919",
         "NEW":  f"{BASE}/preflight_membership_cure.py"}

def load(tag, path):
    spec = importlib.util.spec_from_loader(f"pmc_{tag}", loader=None, origin=path)
    mod = types.ModuleType(f"pmc_{tag}")
    src = open(path).read()
    exec(compile(src, path, "exec"), mod.__dict__)
    return mod

def instrument(mod):
    calls = []
    def stub(url, timeout=20):
        calls.append(url)
        return {"ok": True, "status": 200, "content_type": "text/html",
                "elapsed_ms": 1, "bytes_read": 0, "body_prefix": ""}
    mod.fetch = stub
    return calls

def run_eval(mod, calls, **kw):
    calls.clear()
    ns = Namespace(experiment=kw.get("experiment","A"), treated=kw.get("treated",""),
                   control=kw.get("control"), new_slot=kw.get("new_slot"), out=None)
    payload = mod.evaluate(ns)
    return payload, list(calls)

def run_main(mod, calls, argv):
    calls.clear()
    old = sys.argv
    sys.argv = ["preflight_membership_cure.py"] + argv
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = mod.main()
    except SystemExit as e:
        rc = e.code
    finally:
        sys.argv = old
    return rc, list(calls)

results, fails = [], []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    if not cond: fails.append(name)

mods = {t: load(t, p) for t, p in PATHS.items()}
calls = {t: instrument(m) for t, m in mods.items()}
O, N = mods["ORIG"], mods["NEW"]
co, cn = calls["ORIG"], calls["NEW"]

def hosts(urls): return sorted({u.split("/")[2] for u in urls})

# C1 valid-A pair (survivor)
po, fo = run_eval(O, co, treated="mirageloom.org", control="huyuring.org")
pn, fn = run_eval(N, cn, treated="mirageloom.org", control="huyuring.org")
check("C1a status both BLOCKED", po["status"]==pn["status"]=="BLOCKED_NO_DEN_GO")
check("C1b both fetch 2 domains x3", hosts(fo)==hosts(fn)==["huyuring.org","mirageloom.org"] and len(fo)==len(fn)==6, f"{hosts(fo)} {hosts(fn)}")

# C2 invalid-A SSRF-to-localhost (flip)
po, fo = run_eval(O, co, treated="127.0.0.1")
pn, fn = run_eval(N, cn, treated="127.0.0.1")
check("C2a ORIG repro: INVALID yet fetched", po["status"]=="INVALID_REQUEST" and len(fo)==3, f"orig calls={len(fo)}")
check("C2b NEW: INVALID and ZERO fetch", pn["status"]=="INVALID_REQUEST" and len(fn)==0, f"new calls={len(fn)}")

# C3 host/path confusion (flip)
po, fo = run_eval(O, co, treated="attacker.example.com/x")
pn, fn = run_eval(N, cn, treated="attacker.example.com/x")
check("C3 ORIG fetched attacker / NEW zero", len(fo)>0 and len(fn)==0, f"{len(fo)}->{len(fn)}")

# C4 Namespace-level exp=C (flip)
po, fo = run_eval(O, co, experiment="C", treated="evil.internal")
pn, fn = run_eval(N, cn, experiment="C", treated="evil.internal")
check("C4 exp=C: ORIG fetched / NEW zero", len(fo)>0 and len(fn)==0, f"{len(fo)}->{len(fn)}")

# C5 B-CONTROL GAP (genuinely-new, flip incl. STATUS)
po, fo = run_eval(O, co, experiment="B", treated="aisauna.org", control="evil.internal", new_slot="slotx")
pn, fn = run_eval(N, cn, experiment="B", treated="aisauna.org", control="evil.internal", new_slot="slotx")
check("C5a ORIG: hostile fetch under VALID status", po["status"]=="BLOCKED_NO_DEN_GO" and "evil.internal" in hosts(fo), f"{po['status']} {hosts(fo)}")
check("C5b NEW: INVALID_REQUEST + zero fetch", pn["status"]=="INVALID_REQUEST" and len(fn)==0, f"{pn['status']} {len(fn)}")

# C6 valid-B pair (survivor / over-tighten guard)
po, fo = run_eval(O, co, experiment="B", treated="aisauna.org", control="genesiscodex.org", new_slot="slotx")
pn, fn = run_eval(N, cn, experiment="B", treated="aisauna.org", control="genesiscodex.org", new_slot="slotx")
check("C6 valid-B pair survives", po["status"]==pn["status"]=="BLOCKED_NO_DEN_GO" and hosts(fn)==["aisauna.org","genesiscodex.org"] and len(fn)==6, f"{pn['status']} {hosts(fn)}")

# C7 valid-B solo (survivor)
po, fo = run_eval(O, co, experiment="B", treated="paniccast.com", new_slot="slotx")
pn, fn = run_eval(N, cn, experiment="B", treated="paniccast.com", new_slot="slotx")
check("C7 valid-B solo survives", po["status"]==pn["status"]=="BLOCKED_NO_DEN_GO" and hosts(fn)==["paniccast.com"] and len(fn)==3)

# C9 B control==treated (flip, declared new validation)
po, fo = run_eval(O, co, experiment="B", treated="aisauna.org", control="aisauna.org", new_slot="slotx")
pn, fn = run_eval(N, cn, experiment="B", treated="aisauna.org", control="aisauna.org", new_slot="slotx")
check("C9 ORIG BLOCKED+double fetch / NEW INVALID+zero", po["status"]=="BLOCKED_NO_DEN_GO" and len(fo)==6 and pn["status"]=="INVALID_REQUEST" and len(fn)==0, f"{po['status']}/{len(fo)} -> {pn['status']}/{len(fn)}")

# C8 GO_SEEN sweep (both engines, all statuses observed so far are in results; re-assert on a fresh matrix)
go_seen = False
for m, c in ((O, co), (N, cn)):
    for kw in ({"treated":"mirageloom.org"}, {"treated":"127.0.0.1"},
               {"experiment":"B","treated":"aisauna.org","new_slot":"s"},
               {"experiment":"C","treated":"x"}):
        p, _ = run_eval(m, c, **kw)
        if any(t in p["status"] for t in ("GO","PROCEED","DEPLOY")) and p["status"]!="BLOCKED_NO_DEN_GO":
            go_seen = True
check("C8 no GO/PROCEED/DEPLOY status either engine", not go_seen)

# C11 rc matrix via real main()
rc_o_valid, f1 = run_main(O, co, ["--experiment","A","--treated","mirageloom.org"])
rc_n_valid, f2 = run_main(N, cn, ["--experiment","A","--treated","mirageloom.org"])
rc_o_inval, f3 = run_main(O, co, ["--experiment","A","--treated","127.0.0.1"])
rc_n_inval, f4 = run_main(N, cn, ["--experiment","A","--treated","127.0.0.1"])
rc_o_argp,  _  = run_main(O, co, ["--experiment","Z","--treated","x"])
rc_n_argp,  _  = run_main(N, cn, ["--experiment","Z","--treated","x"])
check("C11a valid rc0 both", rc_o_valid==0 and rc_n_valid==0)
check("C11b evaluate-invalid rc: ORIG 0 -> NEW 1", rc_o_inval==0 and rc_n_inval==1, f"{rc_o_inval}->{rc_n_inval}")
check("C11c argparse-invalid rc2 both", rc_o_argp==2 and rc_n_argp==2)
check("C11d main() fetch parity with evaluate()", len(f3)==3 and len(f4)==0)

# C12 JSON shape preserved on NEW INVALID_REQUEST
pn, _ = run_eval(N, cn, treated="127.0.0.1")
po, _ = run_eval(O, co, treated="127.0.0.1")
check("C12 keys identical, baseline==[]", set(pn.keys())==set(po.keys()) and pn["baseline"]==[])

print(f"\n=== probe gen-1007: {sum(1 for _,ok,_ in results if ok)}/{len(results)} GREEN ===")
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
sys.exit(1 if fails else 0)
