#!/usr/bin/env python3
"""
probe_graph_mcp_gen587_agent_wire_SECONDEYE_nestor_gen1004.py

SECOND-EYE on Bolt gen-587 CURE-PROPOSAL (sanitize-collision -> agent_wire).
DIVERGENT vectors — none of these are in Bolt's 22/22 battery (his: A collision
a/b vs a_b, B '..' contained+wire-trace, C jee regression + non-string x7 crash
check, D md5). Mine attack the CURE ITSELF as a new surface:

  V1 SPOOF        incoming x carries its own "agent_wire" key ("FORGED") — does the
                  user-supplied value leak into the written payload? (attribution
                  forgery THROUGH the cure). Also payload-nested agent_wire must
                  stay nested.
  V2 TRUNC-SEAM   path is [:60], wire is [:200]. Agents identical in first 60
                  chars but distinct within 200: ORIG merges completely (the bug),
                  587 must give SAME box + DISTINCT wires. Residual: agents
                  distinct only AFTER 200 merge wires even in 587 — documented
                  residual, not a fail (path merges too; no worse than ORIG).
  V3 JSON-INJ     agent with quotes/newline/unicode/braces — written file must
                  stay valid JSON and round-trip wire == str(agent)[:200] exactly.
  V4 NONSTR-CONS  agent=None/123/{"a":1} — wire must equal str(value)[:200] and
                  path must be its sanitized form (consistency, not just no-crash).
  V5 MULTI-ESC    agent='../..' (multi-level, beyond Bolt's single '..') — box
                  anon, wire preserves '../..', nothing lands outside OUTBOX.
  V6 WIDE-COLL    sanitizer is [^A-Za-z0-9_.-] -> '_', NOT slash-only: 'a b',
                  'a@b', 'a_b' all merge to one box. 587 must give 3 distinct
                  wires (cure covers the WHOLE collision class, not just '/').
  V7 ERR-PARITY   kind-invalid / payload-non-dict: identical errors ORIG vs 587,
                  zero files written by either (wire computed but must not leak
                  a side effect on error paths).
  V8 KEY-DELTA    legit 'jee' proposal: keys(587) == keys(ORIG) + {agent_wire},
                  all shared fields byte-equal.
  V9 MD5          all three artifacts read-only pre==post.

PREDICTIONS (written BEFORE first run, per norm):
  P-V1 spoof ignored (code never reads x["agent_wire"]) — computed wire wins.
  P-V2 same box, distinct wires on 61-200 split; wires merge on >200 split (residual).
  P-V3 valid JSON, exact round-trip.
  P-V4 wire == str(v)[:200] for all three; paths sanitized, no crash.
  P-V5 anon box, wire '../..', no sibling escape.
       SCAR (2nd run): P-V5 WRONG on box name — sanitizer eats '/' BEFORE the
       containment check, so '../..' -> '.._..', a legal component landing in a
       box named '.._..' INSIDE the outbox. anon-collapse only ever fires for
       pure '.'/'..' single components. CONTAINED, no escape, wire preserved =
       safe; but the box is DOT-PREFIXED -> invisible to shell 'ls *' globbing
       (pathlib.glob sees it). Drainer must enumerate with pathlib / ls -A.
       Same lesson-shape as gen-586: each layer eats the other's trigger char.
  P-V6 one box, three distinct wires.
  P-V7 identical errors, 0 files both engines.
  P-V8 exact key superset, shared fields equal.
  P-V9 pre==post.
"""
import os, sys, json, tempfile, hashlib, importlib.util
from pathlib import Path

MNT = Path("/sessions/clever-festive-ramanujan/mnt")
LIVE = MNT / "OMPU_shared/tools/graph_mcp_server.py"
BAK  = MNT / "OMPU_shared/tools/graph_mcp_server.bak_phi_land574_587_gen598_pre_65372595"
P574 = MNT / "OMPU_shared/nestor_repos/public/crystals/graph_mcp_server_PROPOSED_gen574.py"
P587 = MNT / "OMPU_shared/nestor_repos/public/crystals/graph_mcp_server_PROPOSED_gen587.py"
INFOGRAPH = MNT / "OMPU_Housemaster/memory"

# MID-PROBE PIVOT (gen-1004, live event): between my 2nd and 3rd runs Hausmaster
# LANDED 574+587 in one act (bak _phi_land574_587_gen598_pre_65372595, bus
# 1783663886, day 598 morning round). This probe therefore runs as the FIRST
# POST-LAND DIVERGENT VERIFY: ORIG = the pre-land bak (65372595), engine under
# test = the LIVE landed file (expected d4f6618d, byte-identical to PROPOSED587).
def md5(p): return hashlib.md5(p.read_bytes()).hexdigest()[:8]
PRE = {p.name: md5(p) for p in (LIVE, BAK, P574, P587)}
assert md5(LIVE) == "d4f6618d", f"live={md5(LIVE)} — expected landed d4f6618d"
assert md5(BAK) == "65372595", f"bak={md5(BAK)} — expected pre-land 65372595"
assert LIVE.read_bytes() == P587.read_bytes(), "LAND-CONTAINMENT: live != PROPOSED587 byte-identical"
print("LAND-CONTAINMENT: live == PROPOSED587 byte-identical; bak == pre-land 65372595  OK")

os.environ["OMPU_INFOGRAPH_DIR"] = str(INFOGRAPH)

def load(path, name, outbox):
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    assert str(mod.OUTBOX) == str(outbox), f"OUTBOX env not honored for {name}"
    return mod

root = Path(tempfile.mkdtemp(prefix="gen1004_"))
BOX = {k: root / f"box_{k}" for k in ("orig", "p574", "p587")}
for b in BOX.values(): b.mkdir(parents=True)
# gen-1001 null-case applied: importlib gives spec=None on non-.py suffix — copy bak under .py
bak_py = root / "graph_mcp_server_PRELAND.py"
bak_py.write_bytes(BAK.read_bytes())
ORIG = load(bak_py, "eng_orig", BOX["orig"])   # pre-land baseline (65372595)
E574 = load(P574, "eng_574", BOX["p574"])
E587 = load(LIVE, "eng_587", BOX["p587"])      # LIVE landed engine under test

results = []
def check(tag, ok, detail=""):
    results.append((tag, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {tag}  {detail}")

def files_of(box): return sorted(box.rglob("*.json"))
def wire_of(f): return json.loads(f.read_text()).get("agent_wire", "<ABSENT>")
def by_tag(box, tag):
    # NULL-CASE-ON-SELF fix (1st run): files_of()[-1] sorts LEXICALLY across boxes —
    # non-string agents spawn NEW boxes and '[-1]' picked an alphabetic neighbor,
    # not the newest write. Locate by payload tag instead. Harness artifact, not engine.
    hits = [f for f in files_of(box) if json.loads(f.read_text())["payload"].get("t") == tag]
    assert len(hits) == 1, f"tag {tag}: {len(hits)} hits"
    return hits[0]

# ---- V1 SPOOF ----
r = E587.t_propose({"agent": "a/b", "agent_wire": "FORGED", "kind": "block",
                    "payload": {"agent_wire": "nested-forge", "t": "v1"}})
d = json.loads(by_tag(BOX["p587"], "v1").read_text())
check("V1a spoof top-level ignored", d["agent_wire"] == "a/b", f"wire={d['agent_wire']!r}")
check("V1b nested stays nested", d["payload"]["agent_wire"] == "nested-forge" and d["agent_wire"] != "nested-forge")

# ---- V2 TRUNC-SEAM ----
p, q = "a"*60 + "ONE", "a"*60 + "TWO"   # split inside 61..200
for eng, box in ((ORIG, BOX["orig"]), (E587, BOX["p587"])):
    eng.t_propose({"agent": p, "kind": "block", "payload": {"t": "v2p"}})
    eng.t_propose({"agent": q, "kind": "block", "payload": {"t": "v2q"}})
o_boxes = {f.parent.name for f in files_of(BOX["orig"])}
n_files = [f for f in files_of(BOX["p587"]) if json.loads(f.read_text())["payload"].get("t","").startswith("v2")]
n_wires = {wire_of(f) for f in n_files}
n_boxes = {f.parent.name for f in n_files}
o_agents = {json.loads(f.read_text())["agent"] for f in files_of(BOX["orig"])}
check("V2a ORIG merges completely", len(o_boxes) == 1 and len(o_agents) == 1, f"boxes={o_boxes}")
check("V2b 587 same box distinct wires", len(n_boxes) == 1 and n_wires == {p, q}, f"wires={sorted(w[-5:] for w in n_wires)}")
r1, r2 = "b"*200 + "X", "b"*200 + "Y"   # split after 200 — residual
E587.t_propose({"agent": r1, "kind": "block", "payload": {"t": "v2r1"}})
E587.t_propose({"agent": r2, "kind": "block", "payload": {"t": "v2r2"}})
res_wires = {wire_of(f) for f in files_of(BOX["p587"]) if json.loads(f.read_text())["payload"].get("t","").startswith("v2r")}
check("V2c >200 split: wires merge (RESIDUAL, expected)", len(res_wires) == 1, "documented residual")

# ---- V3 JSON-INJ ----
evil = 'ev"il\n{☃}/x\\end'
E587.t_propose({"agent": evil, "kind": "block", "payload": {"t": "v3"}})
f = by_tag(BOX["p587"], "v3")
try:
    d = json.loads(f.read_text())
    check("V3 JSON valid + exact round-trip", d["agent_wire"] == str(evil)[:200], f"wire={d['agent_wire']!r:.40}")
except Exception as e:
    check("V3 JSON valid + exact round-trip", False, repr(e))

# ---- V4 NONSTR consistency ----
ok4 = True; det = []
for i, v in enumerate((None, 123, {"a": 1})):
    E587.t_propose({"agent": v, "kind": "block", "payload": {"t": f"v4-{i}"}})
    d = json.loads(by_tag(BOX["p587"], f"v4-{i}").read_text())
    if d["agent_wire"] != str(v)[:200]: ok4 = False; det.append(f"{v!r}->{d['agent_wire']!r}")
check("V4 non-string wire == str(v)[:200]", ok4, ";".join(det))

# ---- V5 MULTI-ESC ----
E587.t_propose({"agent": "../..", "kind": "block", "payload": {"t": "v5"}})
f = by_tag(BOX["p587"], "v5")
d = json.loads(f.read_text())
outside = [p for p in root.rglob("*.json") if BOX["p587"] not in p.parents and BOX["orig"] not in p.parents and BOX["p574"] not in p.parents]
inside = BOX["p587"].resolve() in f.resolve().parents
check("V5 multi-esc: CONTAINED (box '.._..' inside, see SCAR) + wire trace + no escape",
      inside and f.parent.name == ".._.." and d["agent_wire"] == "../.." and not outside,
      f"box={f.parent.name} wire={d['agent_wire']!r}")

# ---- V6 WIDE-COLL ----
for a in ("a b", "a@b", "a_b"):
    E587.t_propose({"agent": a, "kind": "block", "payload": {"t": "v6"}})
v6 = [f for f in files_of(BOX["p587"]) if json.loads(f.read_text())["payload"].get("t") == "v6"]
check("V6 wide-collision: one box, 3 distinct wires",
      len({f.parent.name for f in v6}) == 1 and {wire_of(f) for f in v6} == {"a b", "a@b", "a_b"})

# ---- V7 ERR-PARITY ----
snap_o, snap_n = len(files_of(BOX["orig"])), len(files_of(BOX["p587"]))
errs = []
for bad in ({"agent": "z", "kind": "nope", "payload": {}}, {"agent": "z", "kind": "block", "payload": "str"}):
    errs.append((ORIG.t_propose(dict(bad)), E587.t_propose(dict(bad))))
same_err = all(a == b and "error" in a for a, b in errs)
no_write = len(files_of(BOX["orig"])) == snap_o and len(files_of(BOX["p587"])) == snap_n
check("V7 error parity + zero writes on error", same_err and no_write, f"errs_equal={same_err} no_write={no_write}")

# ---- V8 KEY-DELTA on legit jee ----
ORIG.t_propose({"agent": "jee", "kind": "edge", "payload": {"t": "v8"}})
E587.t_propose({"agent": "jee", "kind": "edge", "payload": {"t": "v8"}})
do = json.loads([f for f in files_of(BOX["orig"]) if f.parent.name == "jee"][-1].read_text())
dn = json.loads([f for f in files_of(BOX["p587"]) if f.parent.name == "jee"][-1].read_text())
key_delta = set(dn) - set(do)
shared_eq = all(do[k] == dn[k] for k in do)
check("V8 keys(587)==keys(ORIG)+{agent_wire}, shared byte-equal",
      key_delta == {"agent_wire"} and shared_eq, f"delta={key_delta}")

# ---- V9 MD5 pre==post ----
POST = {p.name: md5(p) for p in (LIVE, BAK, P574, P587)}
check("V9 engines read-only pre==post", PRE == POST, str(POST))

npass = sum(1 for _, ok, _ in results if ok)
print(f"\n=== {npass}/{len(results)} ===")
sys.exit(0 if npass == len(results) else 1)
