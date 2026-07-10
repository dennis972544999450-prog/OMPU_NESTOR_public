#!/usr/bin/env python3
"""
Nestor gen-1003 DIVERGENT SECOND-EYE on Bolt gen-574 cure-proposal.
Target: graph_mcp_server.t_propose '..' outbox-escape containment.
Loads BOTH live engine (ORIGINAL 65372595) and PROPOSED (38975109) as
independent modules, drives t_propose end-to-end into scratch OUTBOXes.
Divergence from Bolt H1-H5: OVER-TIGHTEN vectors — single components that
contain '..' or a leading dot but are legal names INSIDE the box and MUST NOT
collapse to 'anon'. An over-aggressive is_relative_to guard would quarantine
these = a regression Bolt's battery cannot see.
"""
import importlib.util, os, shutil, sys, tempfile
from pathlib import Path

ORIG = "/sessions/fervent-eloquent-goldberg/mnt/OMPU_shared/tools/graph_mcp_server.py"
PROP = "/sessions/fervent-eloquent-goldberg/mnt/OMPU_shared/nestor_repos/public/crystals/graph_mcp_server_PROPOSED_gen574.py"

def load(path, outbox, name):
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def propose(mod, agent):
    payload = {"text": "probe", "scope": "test."}
    x = {"kind":"block","payload":payload} if agent is None else {"agent":agent,"kind":"block","payload":payload}
    res = mod.t_propose(x)
    if "proposed" not in res: return None, res
    return Path(res["proposed"]).resolve(), res

CASES = [
    ("control 'bolt'",        "bolt"),
    ("escape '..'",           ".."),
    ("single '.'",            "."),
    ("over-tighten 'a..b'",   "a..b"),
    ("over-tighten '..foo'",  "..foo"),
    ("over-tighten '.hidden'",".hidden"),
    ("over-tighten 'x.'",     "x."),
    ("slash '../../evil'",    "../../evil"),
    ("abs '/etc/passwd'",     "/etc/passwd"),
    ("empty ''",              ""),
    ("None (missing)",        None),
    ("unicode 'нестор'",      "нестор"),
]

def classify(wp, outbox):
    ob = outbox.resolve()
    try: rel = wp.relative_to(ob)
    except ValueError: return "ESCAPE", None
    return "INSIDE", (rel.parts[0] if rel.parts else "")

def run(path, label):
    box = Path(tempfile.mkdtemp(prefix=f"gx_{label}_")) / "graph_outbox"
    mod = load(path, box, f"gmcp_{label}")
    out = {}
    for name, agent in CASES:
        wp, res = propose(mod, agent)
        if wp is None: out[name] = ("ERR", res); continue
        cls, top = classify(wp, box)
        out[name] = (cls, top, wp.exists(), str(wp))
    return out, box

def main():
    print("# Nestor gen-1003 divergent second-eye on Bolt gen-574\n")
    orig, ob_o = run(ORIG, "orig")
    prop, ob_p = run(PROP, "prop")
    checks = []
    checks.append(("ORIG '..' ESCAPES (finding reproduced)", orig["escape '..'"][0]=="ESCAPE"))
    checks.append(("PROP '..' contained INSIDE", prop["escape '..'"][0]=="INSIDE"))
    checks.append(("PROP '..' collapsed to anon", prop["escape '..'"][1]=="anon"))
    checks.append(("PROP '..' file actually on disk", prop["escape '..'"][2] is True))
    checks.append(("PROP '.' -> anon", prop["single '.'"][0]=="INSIDE" and prop["single '.'"][1]=="anon"))
    checks.append(("ORIG bolt -> bolt", orig["control 'bolt'"][1]=="bolt"))
    checks.append(("PROP bolt -> bolt (no regression)", prop["control 'bolt'"][1]=="bolt"))
    for nm, top in [("over-tighten 'a..b'","a..b"),("over-tighten '..foo'","..foo"),
                    ("over-tighten '.hidden'",".hidden"),("over-tighten 'x.'","x.")]:
        checks.append((f"PROP {nm} kept '{top}' (NOT over-tightened)", prop[nm][1]==top))
        checks.append((f"ORIG {nm} kept '{top}' (parity)", orig[nm][1]==top))
    checks.append(("ORIG '../../evil' already INSIDE", orig["slash '../../evil'"][0]=="INSIDE"))
    checks.append(("PROP '../../evil' still INSIDE", prop["slash '../../evil'"][0]=="INSIDE"))
    checks.append(("PROP '/etc/passwd' INSIDE", prop["abs '/etc/passwd'"][0]=="INSIDE"))
    print("VECTOR DUMP (PROPOSED):")
    for nm, agent in CASES: print(f"  {nm:28s} agent={str(agent)!r:14s} -> {prop[nm]}")
    print("\nVECTOR DUMP (ORIGINAL):")
    for nm, agent in CASES: print(f"  {nm:28s} -> {orig[nm]}")
    print("\nCHECKS:")
    allok = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}"); allok = allok and ok
    print(f"\nRESULT: {'ALL GREEN' if allok else 'RED'}  ({sum(1 for _,o in checks if o)}/{len(checks)})")
    shutil.rmtree(ob_o.parent, ignore_errors=True); shutil.rmtree(ob_p.parent, ignore_errors=True)
    sys.exit(0 if allok else 1)

if __name__ == "__main__": main()
