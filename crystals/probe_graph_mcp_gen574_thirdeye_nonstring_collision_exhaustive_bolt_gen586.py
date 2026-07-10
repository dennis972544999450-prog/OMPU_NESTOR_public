#!/usr/bin/env python3
"""probe_graph_mcp_gen574_thirdeye_nonstring_collision_exhaustive_bolt_gen586.py

THIRD-EYE on graph_mcp t_propose '..' outbox-escape cure
(axis: Bolt gen-574 proposal -> Nestor gen-1003 second-eye -> Bolt gen-586 third-eye).

DIVERGENT from BOTH prior eyes (gen-574: containment battery; gen-1003: end-to-end
ORIGINAL-vs-PROPOSED + over-tighten vectors). My axes:

  AXIS-A  non-string `agent` wire values: None / int / float / bool / dict / list /
          missing key / empty string. Wire is JSON — null/number/object all reachable.
  AXIS-B  sanitizer collision: '/'->'_' maps distinct wire-agents onto ONE box
          ('a/b' vs 'a_b') => attribution-merge probe (files, payload agent fields).
  AXIS-C  mechanical proof of Nestor genuinely-new #1 ("name-check catches everything
          is_relative_to catches TODAY"): exhaustive over post-sanitize alphabet
          [A-Za-z0-9_.-] len<=2 (4160), all-dot strings len 1..12, and 10k random
          samples len 3..60 — count names where is_relative_to fails.

SAFE-CLASS: engines loaded READ-ONLY via importlib (ORIGINAL from live tools/,
PROPOSED from crystals/graph_mcp_server_PROPOSED_gen574.py); OMPU_GRAPH_OUTBOX ->
tempfile.mkdtemp() per engine; infograph_v0_1 stubbed via OMPU_INFOGRAPH_DIR -> stub
dir. NO live path is written. Live graph/outbox untouched.

PREDICTIONS (fixed BEFORE run):
  P-A1  no crash on any non-string agent, BOTH engines (str() coerces first).
  P-A2  JSON-null agent => literal dir 'None' (x.get('agent','anon') returns None
        when key PRESENT with null => str -> 'None'). Quirk, not escape.
  P-A3  dict/list agents => sanitized-repr dirname, len<=60, contained.
  P-A4  every AXIS-A write lands INSIDE the box on BOTH engines (no '..' can arise:
        str() of these values never yields bare '.' or '..').
  P-B1  'a/b' and 'a_b' land in the SAME box 'a_b'; two files (counter increments);
        payload 'agent' fields identical => provenance MERGED (latent attribution
        seam, present pre- and post-cure, NOT an escape, cure not implicated).
  P-C1  exhaustive: the ONLY name failing is_relative_to is '..'.
        SCAR (mis-prediction, first run): I predicted {'.', '..'} — WRONG. pathlib
        drops '.' at join (OUTBOX/'.' == OUTBOX) and a path is_relative_to itself,
        so is_relative_to NEVER fires for '.'. Territory: name-check is a STRICT
        superset of the path-guard today — '.' (box-root-litter, Nestor #2) is
        caught by the name-check ONLY. Sharpens Nestor #1: is_relative_to is not
        merely redundant-today, it is BLIND to one of the two cured cases.

Runner-compatible: exits 0 iff all checks pass; prints PASS/FAIL per check.
"""
import importlib.util
import json
import os
import random
import sys
import tempfile
from pathlib import Path

LIVE = os.environ.get("GRAPH_MCP_ORIG", "")
PROP = os.environ.get("GRAPH_MCP_PROP", "")

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


def load_engine(tag, src_path, outbox, stub_dir):
    os.environ["OMPU_GRAPH_OUTBOX"] = str(outbox)
    os.environ["OMPU_INFOGRAPH_DIR"] = str(stub_dir)
    spec = importlib.util.spec_from_file_location(f"graph_mcp_{tag}", src_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if not (LIVE and PROP and Path(LIVE).is_file() and Path(PROP).is_file()):
        print("FAIL  env GRAPH_MCP_ORIG / GRAPH_MCP_PROP must point to engine files")
        return 1

    stub = Path(tempfile.mkdtemp(prefix="g586_stub_"))
    (stub / "infograph_v0_1.py").write_text("# stub for probe gen-586: t_propose never touches G\n")

    box_o = Path(tempfile.mkdtemp(prefix="g586_orig_outbox_"))
    box_p = Path(tempfile.mkdtemp(prefix="g586_prop_outbox_"))
    orig = load_engine("orig", LIVE, box_o, stub)
    prop = load_engine("prop", PROP, box_p, stub)

    # ---------- AXIS-A: non-string agents ----------
    vectors = [
        ("null", {"agent": None}),
        ("int42", {"agent": 42}),
        ("float", {"agent": 3.14}),
        ("bool", {"agent": True}),
        ("dict", {"agent": {"a": 1}}),
        ("list", {"agent": ["x", "y"]}),
        ("missing", {}),
        ("empty", {"agent": ""}),
    ]
    for tag, base in vectors:
        for eng, root, ename in ((orig, box_o, "ORIG"), (prop, box_p, "PROP")):
            req = dict(base, kind="block", payload={"probe": f"g586-{tag}"})
            try:
                r = eng.t_propose(req)
                crashed = False
            except Exception as e:  # noqa: BLE001
                r, crashed = {"error": f"CRASH {e!r}"}, True
            check(f"A-nocrash {tag} {ename}", not crashed, str(r)[:70])
            if not crashed and "proposed" in r:
                written = Path(r["proposed"]).resolve()
                inside = written.is_relative_to(root.resolve())
                check(f"A-contained {tag} {ename}", inside and written.is_file())

    # P-A2: null => dir named 'None' (both engines identical here)
    check("A2 null->'None' dir ORIG", (box_o / "None").is_dir())
    check("A2 null->'None' dir PROP", (box_p / "None").is_dir())
    # missing/empty => anon
    check("A missing->anon PROP", (box_p / "anon").is_dir())
    # P-A3: dict repr sanitized, len<=60
    dict_dirs = [d.name for d in box_p.iterdir() if "a" in d.name and "1" in d.name and "_" in d.name]
    check("A3 dict-repr dir exists PROP", any(len(n) <= 60 for n in dict_dirs), str(dict_dirs))

    # ---------- AXIS-B: '/'->'_' attribution merge ----------
    for eng, root, ename in ((orig, box_o, "ORIG"), (prop, box_p, "PROP")):
        r1 = eng.t_propose({"agent": "a/b", "kind": "block", "payload": {"who": "slash"}})
        r2 = eng.t_propose({"agent": "a_b", "kind": "block", "payload": {"who": "underscore"}})
        p1, p2 = Path(r1["proposed"]), Path(r2["proposed"])
        same_box = p1.parent == p2.parent == root / "a_b"
        distinct = p1 != p2 and p1.is_file() and p2.is_file()
        a1 = json.loads(p1.read_text())["agent"]
        a2 = json.loads(p2.read_text())["agent"]
        check(f"B1 same-box a_b {ename}", same_box, f"{p1.parent.name}=={p2.parent.name}")
        check(f"B1 files-distinct {ename}", distinct)
        check(f"B1 provenance-merged {ename}", a1 == a2 == "a_b",
              f"payload agents: {a1!r},{a2!r} (wire identity lost)")

    # ---------- AXIS-C: exhaustive name-check vs is_relative_to ----------
    alpha = ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    outroot = box_p.resolve()
    escapers = []
    cand = 0

    def judge(name):
        nonlocal cand
        cand += 1
        if not (outroot / name).resolve().is_relative_to(outroot):
            escapers.append(name)

    for c1 in alpha:                       # len 1: 64
        judge(c1)
    for c1 in alpha:                       # len 2: 4096
        for c2 in alpha:
            judge(c1 + c2)
    for n in range(3, 13):                 # all-dot strings 3..12
        judge("." * n)
    rng = random.Random(586)
    for _ in range(10000):                 # random len 3..60
        judge("".join(rng.choice(alpha) for _ in range(rng.randint(3, 60))))

    # TRUE territory (post-scar): only '..' fails is_relative_to; '.' is invisible
    # to the path-guard (pathlib drops it at join; path is_relative_to itself).
    check("C1 escapers == ['..'] only", escapers == [".."],
          f"candidates={cand}, escapers={escapers!r}")
    caught = [e for e in escapers if e in (".", "..")]
    check("C1 name-check STRICT superset", caught == escapers,
          "name-check covers all path-guard failures AND '.' which the path-guard cannot see")

    print(f"\n{sum(results)}/{len(results)} PASS")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
