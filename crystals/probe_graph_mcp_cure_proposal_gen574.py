#!/usr/bin/env python3
"""
probe_graph_mcp_cure_proposal_gen574.py — Bolt gen-574

ONE battery driven through BOTH files (technique: gen-556 probe + gen-573 dual-battery):
  ORIGINAL = tools/graph_mcp_server.py            (md5 must be 65372595, untouched)
  PATCHED  = crystals/graph_mcp_server_PROPOSED_gen574.py (cure candidate)

ZERO LIVE TOUCH:
  - infograph_v0_1 stubbed in sys.modules BEFORE exec (inert import, no live DB)
  - OMPU_GRAPH_OUTBOX -> tempfile.mkdtemp() throwaway, per file
  - OMPU_INFOGRAPH_DIR -> throwaway subdir (sys.path.insert points nowhere live)
  - only t_propose() called; NEVER __main__/stdin loop; NEVER live graph_outbox

EXPECTED (named BEFORE run, per WATCH-5):
  C2 '..'         : ORIGINAL ESCAPED (finding reproduces) -> PATCHED INSIDE anon/  [THE FLIP]
  C5 '.'          : ORIGINAL writes into OUTBOX root (drain-invisible)
                    -> PATCHED anon/ (drain-VISIBLE)                               [named behavior change]
  C1 control, C3 multi-level, C4 absolute, C6 bad kind, C7 bad payload: NO regressions.
Exit 0 = all checks pass; exit 1 = any check fails.
"""
import sys, os, re, json, types, tempfile, importlib.util
from pathlib import Path

HERE = Path(__file__).resolve()
SHARED = HERE.parents[3]                      # crystals -> public -> nestor_repos -> OMPU_shared
ORIGINAL = SHARED / "tools" / "graph_mcp_server.py"
PATCHED = HERE.parent / "graph_mcp_server_PROPOSED_gen574.py"

FAILS = []
CHECKS = [0]
def check(name, cond, detail=""):
    CHECKS[0] += 1
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)

# ── Nestor tooling-rule: assert MY vectors before interpreting the engine ──
SAN = lambda a: re.sub(r"[^A-Za-z0-9_.-]", "_", str(a))[:60] or "anon"
assert SAN("..") == "..", "premise broken: '..' must survive sanitizer"
assert SAN("../../evil") == ".._.._evil", "premise broken: '/' must map to '_'"
assert SAN("/etc/passwd") == "_etc_passwd", "premise broken: absolute path must flatten"
assert SAN(".") == ".", "premise broken: '.' must survive sanitizer"
print("[vectors] premise asserts OK ('..' and '.' survive sanitizer; '/'->'_')")

def load(path, tag):
    outbox = Path(tempfile.mkdtemp(prefix=f"gm574_{tag}_")) / "graph_outbox"
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    os.environ["OMPU_INFOGRAPH_DIR"] = str(outbox.parent / "_memstub")
    sys.modules["infograph_v0_1"] = types.ModuleType("infograph_v0_1")
    spec = importlib.util.spec_from_file_location(f"gm_{tag}", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, outbox

def propose(mod, agent):
    return mod.t_propose({"agent": agent, "kind": "block", "payload": {"probe": "gen574"}})

def landing(res, outbox):
    p = Path(res["proposed"]).resolve()
    return p, p.is_relative_to(outbox.resolve())

for tag, path in (("ORIG", ORIGINAL), ("PATCH", PATCHED)):
    mod, outbox = load(path, tag)
    print(f"\n=== {tag}: {path.name} (OUTBOX={outbox}) ===")

    # C1 control
    p, inside = landing(propose(mod, "bolt"), outbox)
    check(f"{tag}-C1 control 'bolt' INSIDE bolt/", inside and p.parent.name == "bolt")

    # C2 THE FINDING / THE FLIP
    p, inside = landing(propose(mod, ".."), outbox)
    if tag == "ORIG":
        check("ORIG-C2 '..' ESCAPED one level (finding reproduces)",
              (not inside) and p.parent == outbox.resolve().parent, str(p))
    else:
        check("PATCH-C2 '..' CONTAINED in anon/ (cure holds)",
              inside and p.parent.name == "anon", str(p))

    # C3 multi-level (defended both)
    p, inside = landing(propose(mod, "../../evil"), outbox)
    check(f"{tag}-C3 '../../evil' INSIDE literal '.._.._evil'",
          inside and p.parent.name == ".._.._evil")

    # C4 absolute (defended both)
    p, inside = landing(propose(mod, "/etc/passwd"), outbox)
    check(f"{tag}-C4 '/etc/passwd' INSIDE '_etc_passwd'",
          inside and p.parent.name == "_etc_pass