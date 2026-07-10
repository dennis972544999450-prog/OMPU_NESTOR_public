#!/usr/bin/env python3
"""
probe_graph_mcp_outbox_escape_cure_proposal_gen574.py — Bolt gen-574

Double battery over BOTH files (ORIGINAL 65372595 vs PROPOSED gen-574), driving
t_propose directly. Technique from gen-556 probe: stub infograph_v0_1 (inert import,
no live DB), redirect OMPU_GRAPH_OUTBOX -> tempfile.mkdtemp() throwaway PER LOAD.
NEVER touches live graph_outbox / live graph DB / network / __main__ / stdin-loop.

Expected (the whole point of a cure-proposal):
  ORIGINAL: H1 agent='..' ESCAPES to OUTBOX.parent  -> FINDING reproduced
  PROPOSED: H1 agent='..' collapses to 'anon', file lands INSIDE OUTBOX -> FIXED
  Both: H4 control 'bolt' INSIDE; H2 '../../evil' INSIDE (literal); H3 '/etc/passwd'
        INSIDE; H5 '.' -> in ORIGINAL harmless-inside(OUTBOX itself, escapes NOTHING
        but writes at box root), in PROPOSED collapses to 'anon' subdir.
  => no regression on the defended/control cases; only the escaping case flips.
"""
import sys, os, json, tempfile, importlib.util
from pathlib import Path

CRYST = Path(__file__).resolve().parent
ORIGINAL = CRYST.parent.parent / "tools" / "graph_mcp_server.py"   # public/ -> repo root? resolve below
# graph_mcp lives at OMPU_shared/tools/graph_mcp_server.py; this probe lives at
# OMPU_shared/nestor_repos/public/crystals/. Walk up to OMPU_shared.
def find_shared(start):
    p = start
    for _ in range(8):
        if (p / "tools" / "graph_mcp_server.py").exists() and (p / "bus").exists():
            return p
        p = p.parent
    raise RuntimeError("OMPU_shared root not found")

SHARED = find_shared(CRYST)
ORIGINAL = SHARED / "tools" / "graph_mcp_server.py"
PROPOSED = CRYST / "graph_mcp_server_PROPOSED_gen574.py"

# ── stub the engine so importing the server never touches the live graph DB ──
import types
stub = types.ModuleType("infograph_v0_1")
for name in ("search_blocks","search_edges","field","neighbors","scars_near",
             "scope","recent_blocks","active_questions","graph_news"):
    setattr(stub, name, lambda *a, **k: {"stub": True})
sys.modules["infograph_v0_1"] = stub

def load_server(path, outbox):
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    os.environ["OMPU_INFOGRAPH_DIR"] = str(outbox)  # MEM_DIR; sys.path.insert only, stub already present
    spec = importlib.util.spec_from_file_location(f"gms_{outbox.name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

CASES = [
    ("H4 control 'bolt'", "bolt",        "INSIDE"),
    ("H1 escape '..'",    "..",          "ESCAPE"),   # the finding
    ("H2 '../../evil'",   "../../evil",  "INSIDE"),
    ("H3 '/etc/passwd'",  "/etc/passwd", "INSIDE"),
    ("H5 single '.'",     ".",           "INSIDE"),
]

def run(path, label):
    outbox = Path(tempfile.mkdtemp(prefix=f"gms_{label}_"))
    mod = load_server(path, outbox)
    OUTBOX = mod.OUTBOX.resolve()
    results = {}
    for name, agent, _exp in CASES:
        r = mod.t_propose({"agent": agent, "kind": "block", "payload": {"x": 1}})
        written = Path(r["proposed"]).resolve()
        escaped = not written.is_relative_to(OUTBOX)
        results[name] = (agent, written, escaped, written.exists())
    return OUTBOX, results

def main():
    print("=" * 70)
    passed = failed = 0
    orig_ob, orig = run(ORIGINAL, "ORIG")
    prop_ob, prop = run(PROPOSED, "PROP")

    # --- assertions ---
    checks = []
    # 1. ORIGINAL reproduces the finding: '..' escapes
    checks.append(("ORIG H1 '..' ESCAPES (finding reproduced)", orig["H1 escape '..'"][2] is True))
    # 2. PROPOSED fixes it: '..' no longer escapes
    checks.append(("PROP H1 '..' contained (no escape)", prop["H1 escape '..'"][2] is False))
    #    and lands inside the box under 'anon'
    checks.append(("PROP H1 '..' collapsed to anon subdir",
                   (prop_ob / "anon") in prop["H1 escape '..'"][1].parents))
    # 3. No regression: control + defended cases never escape in EITHER build
    for name in ("H4 control 'bolt'", "H2 '../../evil'", "H3 '/etc/passwd'", "H5 single '.'"):
        checks.append((f"ORIG {name} contained", orig[name][2] is False))
        checks.append((f"PROP {name} contained", prop[name][2] is False))
    # 4. control 'bolt' lands in graph_outbox/bolt in both
    checks.append(("ORIG H4 bolt in graph_outbox/bolt", (orig_ob / "bolt") in orig["H4 control 'bolt'"][1].parents))
    checks.append(("PROP H4 bolt in graph_outbox/bolt", (prop_ob / "bolt") in prop["H4 control 'bolt'"][1].parents))
    # 5. every proposal file actually written (behavior preserved)
    checks.append(("ORIG all files written", all(v[3] for v in orig.values())))
    checks.append(("PROP all files written", all(v[3] for v in prop.values())))

    for desc, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
        passed += ok; failed += (not ok)

    print("-" * 70)
    print(f"  ORIG '..' wrote -> {orig[CASES[1][0]][1]}  (escaped={orig[CASES[1][0]][2]})")
    print(f"  PROP '..' wrote -> {prop[CASES[1][0]][1]}  (escaped={prop[CASES[1][0]][2]})")
    print("=" * 70)
    print(f"  {passed}/{passed+failed} PASS")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
