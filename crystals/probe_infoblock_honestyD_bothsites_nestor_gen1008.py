#!/usr/bin/env python3
"""PROBE gen-1008 (nestor) — infoblock cure (d)-both-sites honesty land.
CONTRACT LOCKED BEFORE TOUCHING ENGINE. Axis: Bolt gen-563 -> Nestor gen-0996 -> Bolt gen-564 (B3).
Cure (d): wording-only realignment of the 'no existence oracle' overclaim at BOTH doctrine sites
(docstring L6-7 + reason L117) -> disclosed-withholding wording, consistent with negative_space.
ZERO behaviour change allowed: guard, counts, keys, negative_space must be byte-stable.
FLIPS: C1 source doctrine count 2->0; C2 emitted reason honest; C9 docstring honest.
SURVIVORS: C3 zero private ids/labels in bytes; C4 entry+exact count kept; C5 guard kept
(no entry when no private nbrs); C6 negative_space byte-identical; C7 depth-1 identical;
C8 key-set/edge/block parity. Runs BOTH engines (baseline .bak vs landed) via importlib,
DB/ALLOWLIST/OUT redirected to mkdtemp. NEVER live DB/allowlist/site. No network. No __main__ of engine.
"""
import importlib.util, json, re, sqlite3, sys, tempfile
from pathlib import Path

BASE = Path(sys.argv[1])   # baseline engine (.bak)
LAND = Path(sys.argv[2])   # landed engine
PASS_ = []; FAIL_ = []
def check(name, ok, detail=""):
    (PASS_ if ok else FAIL_).append(name)
    print(("PASS" if ok else "FAIL"), name, detail)

def norm(t): return re.sub(r"\s+", " ", t)

def build_fixture(root: Path):
    db = root / "infograph.db"; c = sqlite3.connect(db)
    c.execute("CREATE TABLE blocks(id TEXT, label TEXT, gloss TEXT, block_class TEXT, state TEXT, created_at TEXT, created_by_agent TEXT)")
    c.execute("CREATE TABLE block_payloads(block_id TEXT, gloss TEXT, rev INT)")
    c.execute("CREATE TABLE edges(src TEXT, dst TEXT, op TEXT, lens TEXT, sign TEXT, strength REAL, expired_at TEXT)")
    rows = [("PUB-X","pub x","gx","note","live","2026-01-01","t"),
            ("PUB-Y","pub y","gy","note","live","2026-01-01","t"),
            ("PRIV-P","SECRET-LABEL-P","sp","family","live","2026-01-01","t"),
            ("PRIV-Q","SECRET-LABEL-Q","sq","engine-ops","live","2026-01-01","t")]
    c.executemany("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)", rows)
    edges = [("PUB-X","PRIV-P","rel","meaning","+",1.0,""),
             ("PRIV-Q","PUB-X","rel","action","+",1.0,""),
             ("PUB-X","PUB-Y","rel","evidence","+",1.0,"")]
    c.executemany("INSERT INTO edges VALUES(?,?,?,?,?,?,?)", edges)
    c.commit(); c.close()
    al = root / "allow.json"; al.write_text(json.dumps({"public_block_ids": ["PUB-X","PUB-Y"]}))
    return db, al

def run_engine(src: Path, tag: str):
    root = Path(tempfile.mkdtemp(prefix=f"g1008_{tag}_")); db, al = build_fixture(root)
    out = root / "site"
    imp = root / f"eng_{tag}.py"; imp.write_text(src.read_text())  # importlib needs .py suffix
    spec = importlib.util.spec_from_file_location(f"eng_{tag}", imp)
    mod = importlib.util.module_from_spec(spec)
    old_argv = sys.argv[:]
    sys.argv = ["engine", str(out), "2026-07-10T00:00:00Z"]
    try:
        spec.loader.exec_module(mod)
        mod.DB, mod.ALLOWLIST, mod.OUT = db, al, out
        mod.main()
    finally:
        sys.argv = old_argv
    def scene(slugname):
        p = out / "infoblock" / "b" / slugname / "oags.json"
        return json.loads(p.read_text()) if p.exists() else None
    allbytes = ""
    for f in out.rglob("*"):
        if f.is_file():
            try: allbytes += f.read_text(errors="replace")
            except Exception: pass
    return scene("pub-x"), scene("pub-y"), allbytes

sb, sl_ = BASE.read_text(), LAND.read_text()
# C1 FLIP: doctrine phrase count (whitespace-normalized — gen-0996 null-case lesson) 2 -> 0
cb, cl = norm(sb).count("no existence oracle"), norm(sl_).count("no existence oracle")
check("C1_source_doctrine_2to0", cb == 2 and cl == 0, f"base={cb} land={cl}")
# C9 FLIP: docstring honesty
check("C9_docstring_disclosed", ("disclosed withholding" not in norm(sb).lower()) and ("disclosed withholding" in norm(sl_).lower()))

bx, by, bbytes = run_engine(BASE, "base")
lx, ly, lbytes = run_engine(LAND, "land")
def dl_priv(s): return next((d for d in s["declared_losses"] if d.get("scope") == "private-neighbour-withheld"), None)

# C2 FLIP: emitted reason
bdl, ldl = dl_priv(bx), dl_priv(lx)
check("C2_reason_flip", bdl and "no existence oracle" in bdl["reason"] and ldl and "no existence oracle" not in ldl["reason"] and "isclosed withholding" in ldl["reason"])
# C3 SURVIVE: zero private ids/labels in any emitted byte, both engines
leak = lambda t: any(x in t for x in ("PRIV-P","PRIV-Q","SECRET-LABEL"))
check("C3_no_priv_leak_base", not leak(bbytes)); check("C3_no_priv_leak_land", not leak(lbytes))
# C4 SURVIVE: entry present, exact count==2 (two withheld edges at PUB-X), both engines
check("C4_entry_count_kept", bdl and ldl and bdl["count"] == 2 and ldl["count"] == 2, f"b={bdl and bdl['count']} l={ldl and ldl['count']}")
# C5 SURVIVE: guard — PUB-Y (no private nbrs) has NO entry, both engines
check("C5_guard_kept", dl_priv(by) is None and dl_priv(ly) is None)
# C6 SURVIVE: negative_space byte-identical across engines
check("C6_negative_space_stable", bx["negative_space"] == lx["negative_space"] and by["negative_space"] == ly["negative_space"])
# C7 SURVIVE: depth-1 declared_loss identical
d1b = next(d for d in bx["declared_losses"] if d["scope"] == "depth-1")
d1l = next(d for d in lx["declared_losses"] if d["scope"] == "depth-1")
check("C7_depth1_identical", d1b == d1l)
# C8 parity: key sets, blocks, edges identical
check("C8_scene_key_parity", set(bx) == set(lx) and set(by) == set(ly))
check("C8_blocks_edges_parity", bx["blocks"] == lx["blocks"] and bx["edges"] == lx["edges"])
# C10 wording-only: recoverable flag + scope names unchanged
check("C10_scope_flags_kept", bdl["scope"] == ldl["scope"] and bdl["recoverable"] == ldl["recoverable"] == False)

print(f"\nRESULT: {len(PASS_)} PASS / {len(FAIL_)} FAIL")
sys.exit(1 if FAIL_ else 0)
