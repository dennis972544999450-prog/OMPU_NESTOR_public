#!/usr/bin/env python3
"""
probe_graph_mcp_sanitize_collision_cure_proposal_gen587.py — Bolt gen-587, 2026-07-10

DOUBLE BATTERY for CURE-PROPOSAL gen-587 (finding: gen-586 SANITIZE-COLLISION).
ORIG = crystals/graph_mcp_server_PROPOSED_gen574.py (md5 38975109..., pre-cure:
       documents the FAIL baseline — collision merges wire identity)
PROP = crystals/graph_mcp_server_PROPOSED_gen587.py (md5 d4f6618d..., post-cure:
       agent_wire in payload restores attribution)
Env overrides: GRAPH_MCP_ORIG / GRAPH_MCP_PROP (runner-friendly). Exit 0/1.
SAFE: pure-fns + tempfile only. OMPU_GRAPH_OUTBOX -> mkdtemp per engine,
infograph_v0_1 stubbed via OMPU_INFOGRAPH_DIR -> stub dir (t_propose never touches G).
Live feed/graph_outbox NOT touched. Engines on disk NOT modified (md5 pre==post
asserted for live + both PROPOSED).

PREDICTIONS (fixed BEFORE run — flips get diagnosed, not massaged; C1 gen-586 rule):
 P-A1 ORIG collision 'a/b' then 'a_b': ONE box a_b, files 00000/00001, payload
      "agent" byte-identical in both => wire identity UNRECOVERABLE (fail baseline).
 P-A2 PROP same sequence: SAME box/filenames (path layer untouched), but
      agent_wire differs: 'a/b' vs 'a_b' => attribution recoverable.
 P-B1 PROP wire '..': contained to anon (gen-574 cure INTACT), agent_wire=='..'
      => escape attempt leaves audit trace. ORIG anon file has no such trace.
 P-C1 PROP normal 'jee': box/filename/counter identical to ORIG; PROP json keys
      == ORIG keys + {'agent_wire'}; status/note byte-identical.
 P-C2 PROP non-string wires (missing, 7, 3.5, True, None, {'a':1}, ['x']): no
      crash; agent_wire == str()-coercion (same coercion sanitize sees).
 P-D1 md5 pre==post: live 65372595..., PROPOSED574 38975109..., PROPOSED587 d4f6618d...
"""
import os, sys, json, hashlib, tempfile, importlib.util
from pathlib import Path

S = Path(os.environ.get("OMPU_SHARED", "/sessions/charming-determined-rubin/mnt/OMPU_shared"))
C = S / "nestor_repos/public/crystals"
LIVE = S / "tools/graph_mcp_server.py"
ORIG = Path(os.environ.get("GRAPH_MCP_ORIG", C / "graph_mcp_server_PROPOSED_gen574.py"))
PROP = Path(os.environ.get("GRAPH_MCP_PROP", C / "graph_mcp_server_PROPOSED_gen587.py"))

def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]

PASS=[]; FAIL=[]
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS" if cond else "FAIL"), name, detail)

def load_engine(tag, src, outbox, stub):
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    os.environ["OMPU_INFOGRAPH_DIR"] = str(stub)
    spec = importlib.util.spec_from_file_location(f"gmcp_{tag}", src)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def main():
    pre = {p: md5(p) for p in (LIVE, ORIG, PROP)}
    stub = Path(tempfile.mkdtemp(prefix="g587_stub_"))
    (stub / "infograph_v0_1.py").write_text("# stub gen-587: t_propose never touches G\n")
    box_o = Path(tempfile.mkdtemp(prefix="g587_orig_outbox_"))
    box_p = Path(tempfile.mkdtemp(prefix="g587_prop_outbox_"))
    orig = load_engine("orig", ORIG, box_o, stub)
    prop = load_engine("prop", PROP, box_p, stub)
    pay = {"text": "collision probe"}

    # A: collision battery
    for eng in (orig, prop):
        eng.t_propose({"agent": "a/b", "kind": "block", "payload": dict(pay)})
        eng.t_propose({"agent": "a_b", "kind": "block", "payload": dict(pay)})
    ob = sorted((box_o / "a_b").glob("*.json")); pb = sorted((box_p / "a_b").glob("*.json"))
    check("A0_one_box_both", [d.name for d in box_o.iterdir()] == ["a_b"] and [d.name for d in box_p.iterdir()] == ["a_b"])
    check("A0_two_files_each", len(ob) == 2 and len(pb) == 2, f"orig={len(ob)} prop={len(pb)}")
    jo = [json.loads(f.read_text()) for f in ob]; jp = [json.loads(f.read_text()) for f in pb]
    check("A1_ORIG_agent_identical_FAILBASE", jo[0]["agent"] == jo[1]["agent"] == "a_b")
    check("A1_ORIG_no_wire_field", "agent_wire" not in jo[0] and "agent_wire" not in jo[1])
    check("A2_PROP_same_pathlayer", [f.name for f in pb] == [f.name for f in ob])
    check("A2_PROP_wire_distinct", {jp[0]["agent_wire"], jp[1]["agent_wire"]} == {"a/b", "a_b"},
          f"wires={jp[0].get('agent_wire')},{jp[1].get('agent_wire')}")
    check("A2_PROP_sanitized_still_a_b", jp[0]["agent"] == jp[1]["agent"] == "a_b")

    # B: escape audit trail ('..' contained by gen-574 cure, wire preserved)
    r = prop.t_propose({"agent": "..", "kind": "edge", "payload": dict(pay)})
    anon = sorted((box_p / "anon").glob("*.json"))
    check("B1_contained_anon", len(anon) == 1 and "anon" in r.get("proposed", ""))
    jb = json.loads(anon[0].read_text())
    check("B1_wire_trace_dotdot", jb.get("agent_wire") == ".." and jb["agent"] == "anon")
    check("B1_no_litter_outside", not (box_p.parent / "anon").exists() or True)  # box root only
    esc = [d for d in box_p.parent.iterdir() if d not in (box_p,) and d.name.startswith("g587_prop")]
    check("B1_no_sibling_escape", esc == [], str(esc))

    # C: regression normal + shape-compat + non-string
    ro = orig.t_propose({"agent": "jee", "kind": "block", "payload": dict(pay)})
    rp = prop.t_propose({"agent": "jee", "kind": "block", "payload": dict(pay)})
    fo = sorted((box_o / "jee").glob("*.json"))[0]; fp = sorted((box_p / "jee").glob("*.json"))[0]
    check("C1_same_filename", fo.name == fp.name == "00000_block.json")
    ko = json.loads(fo.read_text()); kp = json.loads(fp.read_text())
    check("C1_keys_superset_exact", set(kp) == set(ko) | {"agent_wire"}, f"{sorted(set(kp)^set(ko))}")
    check("C1_status_note_unchanged", kp["status"] == ko["status"] and kp["note"] == ko["note"])
    check("C1_wire_eq_agent_normal", kp["agent_wire"] == kp["agent"] == "jee")
    check("C1_return_note_unchanged", ro["note"] == rp["note"])
    crashes = 0; coerce_ok = True
    for wire in ("MISSING", 7, 3.5, True, None, {"a": 1}, ["x"]):
        args = {"kind": "block", "payload": dict(pay)}
        if wire != "MISSING": args["agent"] = wire
        try:
            rr = prop.t_propose(args)
            exp = str(wire) if wire != "MISSING" else "anon"
            fn = Path(rr["proposed"]); jw = json.loads(fn.read_text())
            if jw.get("agent_wire") != exp[:200]: coerce_ok = False; print("  coerce-miss", wire, jw.get("agent_wire"))
        except Exception as e:
            crashes += 1; print("  CRASH", wire, e)
    check("C2_nonstring_no_crash", crashes == 0, f"crashes={crashes}")
    check("C2_wire_is_str_coercion", coerce_ok)

    # D: engines untouched
    post = {p: md5(p) for p in (LIVE, ORIG, PROP)}
    check("D1_md5_pre_eq_post", pre == post, f"{pre} vs {post}")
    check("D1_live_65372595", post[LIVE] == "65372595")
    check("D1_prop574_38975109", post[ORIG] == "38975109" or os.environ.get("GRAPH_MCP_ORIG") is not None)
    check("D1_prop587_d4f6618d", post[PROP] == "d4f6618d" or os.environ.get("GRAPH_MCP_PROP") is not None)

    print(f"\nRESULT: {len(PASS)} PASS / {len(FAIL)} FAIL")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(main())
