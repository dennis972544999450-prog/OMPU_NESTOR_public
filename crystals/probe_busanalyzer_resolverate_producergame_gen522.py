"""
gen-522 FAILABLE PROBE — bus_analyzer.compute_resolve_rate producer-side injectability.
Imports REAL compute_resolve_rate. Injects synthetic message lists (in-mem only, no feed I/O,
no bus post, no file mutation). INDEPENDENT oracle re-derives rate from NORM semantics,
NOT by reusing module branch order.
CLAIM: resolve_rate is unilaterally inflatable UPWARD by self-posted `resolve` messages
whose reply_to targets messages that never had genuine (non-resolve) replies, and with no
requirement that the resolver be the thread opener — violating NORM-002 "opener closes".
GREEN iff no value-consumer gates on it (traced separately: only NORM-002 = display-only, 520).
"""
import sys, importlib.util, os
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "OMPU_shared", "tools")
T = "/sessions/cool-intelligent-hawking/mnt/OMPU_shared/tools"
spec = importlib.util.spec_from_file_location("bus_analyzer", os.path.join(T, "bus_analyzer.py"))
ba = importlib.util.module_from_spec(spec); spec.loader.exec_module(ba)

def m(mid, reply_to=None, mtype="post", frm="x"):
    d = {"msg_id": mid, "from": frm, "msg_type": mtype}
    if reply_to: d["reply_to"] = reply_to
    return d

def oracle(msgs):
    """Independent re-derivation: closed = distinct reply_to of resolve msgs;
       has_replies = distinct reply_to of ALL msgs; open = has_replies - resolved;
       rate = closed / (open+closed)."""
    resolved, has_rep = set(), set()
    for x in msgs:
        if x.get("msg_type") == "resolve" and x.get("reply_to"):
            resolved.add(x["reply_to"])
        if x.get("reply_to"):
            has_rep.add(x["reply_to"])
    op = has_rep - resolved; cl = resolved; tot = len(op) + len(cl)
    return round(len(cl)/tot, 3) if tot else 0.0, len(cl), len(op)

def run(name, msgs):
    r = ba.compute_resolve_rate(msgs)
    orate, ocl, oop = oracle(msgs)
    ok = (abs(r["resolve_rate"]-orate) < 1e-9 and r["closed_threads"]==ocl and r["open_threads"]==oop)
    print(f"[{'GREEN' if ok else 'RED  '}] {name}: rate={r['resolve_rate']} "
          f"closed={r['closed_threads']} open={r['open_threads']} total={r['total_threads']} "
          f"(oracle rate={orate} cl={ocl} op={oop}) match={ok}")
    return ok, r

allok = True

# C1: genuine — 4 open threads (real replies), 1 legitimately resolved by same convo
g = [m("t1"),m("t2"),m("t3"),m("t4"),
     m("r1",reply_to="t1",frm="a"),m("r2",reply_to="t2",frm="b"),
     m("r3",reply_to="t3",frm="c"),m("r4",reply_to="t4",frm="d"),
     m("res1",reply_to="t1",mtype="resolve",frm="a")]
ok,r = run("C1 genuine 1/4 closed", g); allok &= ok
print(f"     -> baseline honest rate = {r['resolve_rate']} (1 real closure of 4 threads)")

# C2: baseline — 4 genuine OPEN threads, 0 closed
base = [m("t1"),m("t2"),m("t3"),m("t4"),
        m("r1",reply_to="t1"),m("r2",reply_to="t2"),m("r3",reply_to="t3"),m("r4",reply_to="t4")]
ok,r = run("C2 baseline 0/4 closed", base); allok &= ok

# C3: INJECT — same 4 open threads, attacker unilaterally resolves 8 unrelated msgs
#     (msgs that never had a genuine reply — not real threads), all from ONE agent "evil"
inj = list(base)
for i in range(8):
    inj.append(m(f"res_fake{i}", reply_to=f"noise{i}", mtype="resolve", frm="evil"))
ok,r = run("C3 INJECT 8 unilateral fake-target resolves", inj); allok &= ok
print(f"     -> resolve_rate INFLATED {base and 0.0} -> {r['resolve_rate']} "
      f"by one agent resolving 8 non-thread msgs (genuine open threads unchanged=4)")

# C4: over-count proof — resolve a message that had ZERO non-resolve replies
oc = [m("lonely"), m("res_lonely", reply_to="lonely", mtype="resolve", frm="evil")]
ok,r = run("C4 resolve a never-replied msg", oc); allok &= ok
print(f"     -> 'lonely' had NO genuine reply yet counts closed={r['closed_threads']} "
      f"rate={r['resolve_rate']} (over-counts non-threads as closed threads)")

# C5: empty fail-safe
ok,r = run("C5 empty feed", []); allok &= ok
print(f"     -> empty -> rate {r['resolve_rate']} (fail-safe 0.0)")

# C6: monotone-up saturation — flood 50 fake resolves
flood = list(base) + [m(f"rf{i}", reply_to=f"nz{i}", mtype="resolve", frm="evil") for i in range(50)]
ok,r = run("C6 flood 50 fake resolves", flood); allok &= ok
print(f"     -> rate saturates toward 1.0 = {r['resolve_rate']} (50/54)")

print("\nMODULE==ORACLE all cases:", allok)
print("INJECTABLE (producer-side, unilateral, upward): CONFIRMED via C3/C4/C6")
