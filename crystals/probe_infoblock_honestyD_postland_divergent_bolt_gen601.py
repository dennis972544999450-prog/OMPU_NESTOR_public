#!/usr/bin/env python3
"""PROBE gen-601 (bolt) — DIVERGENT post-land verify of Nestor gen-1008 infoblock honestyD land.
Predictions locked BEFORE run (outputs/infoblock_honestyD_divergent_predictions_locked_gen601.md).
Own fixtures, NOT a rerun of probe 28834aab. Cells:
D1 SURVIVE per-edge count via single neighbour (==2); D2 SURVIVE count==1; D3 SURVIVE ghost allowlist
entry; D4 SURVIVE empty-allowlist full-site byte parity; D5 FLIP whole-site diff == exactly the cured
sentence in exactly 4 files; D6 SURVIVE negative_space; D7 control: source doctrine 2->0.
Both engines via importlib from mkdtemp COPIES named .py (LOADER-SUFFIX guard), sys.dont_write_bytecode,
DB/ALLOWLIST/OUT redirected. NEVER live DB/allowlist/site. No network paths in engine (sqlite+files only).
Usage: probe.py <baseline.bak> <landed.py>
"""
import importlib.util, json, sqlite3, re, sys, tempfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE_SRC = Path(sys.argv[1]); LAND_SRC = Path(sys.argv[2])
PASS_, FAIL_ = [], []
def check(name, ok, detail=""):
    (PASS_ if ok else FAIL_).append(name)
    print(("PASS" if ok else "FAIL"), name, detail)

OLD_REASON = "edges to blocks not on the public allowlist are dropped; their ids are not revealed (no existence oracle)."
NEW_REASON = "edges to blocks not on the public allowlist are dropped; their ids and labels are not revealed. Disclosed withholding: this entry's presence and its count reveal that private neighbours exist and how many edges were withheld."

def build_fixture(root: Path, empty_allow=False):
    db = root / "infograph.db"; c = sqlite3.connect(db)
    c.execute("CREATE TABLE blocks(id TEXT, label TEXT, gloss TEXT, block_class TEXT, state TEXT, created_at TEXT, created_by_agent TEXT)")
    c.execute("CREATE TABLE block_payloads(block_id TEXT, gloss TEXT, rev INT)")
    c.execute("CREATE TABLE edges(src TEXT, dst TEXT, op TEXT, lens TEXT, sign TEXT, strength REAL, expired_at TEXT)")
    c.executemany("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)", [
        ("PUB-A","pub a","ga","note","live","2026-01-01","t"),
        ("PUB-B","pub b","gb","note","live","2026-01-01","t"),
        ("PRIV-M","SECRET-LBL-M","sm","family","live","2026-01-01","t"),
        ("PRIV-N","SECRET-LBL-N","sn","engine-ops","live","2026-01-01","t")])
    c.executemany("INSERT INTO edges VALUES(?,?,?,?,?,?,?)", [
        ("PUB-A","PRIV-M","rel","meaning","+",1.0,""),      # withheld edge 1 (A)
        ("PRIV-M","PUB-A","rel","action","+",1.0,""),        # withheld edge 2 (A) — SAME neighbour, reverse dir
        ("PUB-A","PRIV-N","rel","meaning","+",1.0,"2026-01-01T00:00:00Z"),  # EXPIRED — must NOT count
        ("PRIV-M","PRIV-N","rel","meta","+",1.0,""),         # priv-priv — must not matter
        ("PUB-A","PUB-B","rel","evidence","+",1.0,""),       # public-public
        ("PUB-B","PRIV-N","rel","tension","+",1.0,"")])      # withheld edge 1 (B)
    c.commit(); c.close()
    al = root / "allow.json"
    ids = [] if empty_allow else ["PUB-A","PUB-B","PUB-GHOST"]
    al.write_text(json.dumps({"public_block_ids": ids}))
    return db, al

def run_engine(src: Path, tag: str, empty_allow=False):
    root = Path(tempfile.mkdtemp(prefix=f"g601_{tag}_"))
    db, al = build_fixture(root, empty_allow)
    out = root / "site"
    imp = root / f"eng_{tag}.py"                 # LOADER-SUFFIX guard: always a .py name
    imp.write_text(src.read_text())
    spec = importlib.util.spec_from_file_location(f"eng601_{tag}", imp)
    mod = importlib.util.module_from_spec(spec)
    old_argv = sys.argv[:]
    sys.argv = ["engine", str(out), "2026-07-10T00:00:00Z"]
    try:
        spec.loader.exec_module(mod)
        mod.DB, mod.ALLOWLIST, mod.OUT = db, al, out
        mod.main()
    finally:
        sys.argv = old_argv
    files = {str(f.relative_to(out)): f.read_text(errors="replace") for f in out.rglob("*") if f.is_file()}
    def scene(slugname):
        k = f"infoblock/b/{slugname}/oags.json"
        return json.loads(files[k]) if k in files else None
    return files, scene

norm = lambda t: re.sub(r"\s+", " ", t)
sb, sl_ = BASE_SRC.read_text(), LAND_SRC.read_text()
# D7 control: source doctrine 2->0
cb, cl = norm(sb).count("no existence oracle"), norm(sl_).count("no existence oracle")
check("D7_source_doctrine_2to0", cb == 2 and cl == 0, f"base={cb} land={cl}")

bfiles, bscene = run_engine(BASE_SRC, "base")
lfiles, lscene = run_engine(LAND_SRC, "land")
dl_priv = lambda s: next((d for d in s["declared_losses"] if d.get("scope") == "private-neighbour-withheld"), None)

ba, bb = bscene("pub-a"), bscene("pub-b"); la, lb = lscene("pub-a"), lscene("pub-b")
# D1: per-edge count via single neighbour, expired excluded, priv-priv ignored -> 2 both
bda, lda = dl_priv(ba), dl_priv(la)
check("D1_pubA_count2_both", bda and lda and bda["count"] == 2 and lda["count"] == 2,
      f"b={bda and bda['count']} l={lda and lda['count']}")
# D2: PUB-B count 1 both
bdb, ldb = dl_priv(bb), dl_priv(lb)
check("D2_pubB_count1_both", bdb and ldb and bdb["count"] == 1 and ldb["count"] == 1,
      f"b={bdb and bdb['count']} l={ldb and ldb['count']}")
# D3: ghost allowlist entry -> no scene, manifest count 2, both
mb = json.loads(bfiles[".well-known/oags"]); ml = json.loads(lfiles[".well-known/oags"])
ghost = lambda fs: any("pub-ghost" in k for k in fs)
check("D3_ghost_skipped_both", not ghost(bfiles) and not ghost(lfiles)
      and mb["block_count"] == 2 and ml["block_count"] == 2,
      f"b_count={mb['block_count']} l_count={ml['block_count']}")
# D4: EMPTY allowlist -> full-site byte parity base vs land
ebf, _ = run_engine(BASE_SRC, "base_empty", empty_allow=True)
elf, _ = run_engine(LAND_SRC, "land_empty", empty_allow=True)
check("D4_empty_allowlist_byte_parity", set(ebf) == set(elf) and all(ebf[k] == elf[k] for k in ebf),
      f"files={len(ebf)}")
# D5: whole-site diff == exactly the cured sentence in exactly 4 files
check("D5_same_file_sets", set(bfiles) == set(lfiles), f"n={len(bfiles)}")
differing = sorted(k for k in bfiles if bfiles[k] != lfiles.get(k))
expected_diff = sorted(["infoblock/b/pub-a/oags.json", "infoblock/b/pub-a/free.json",
                        "infoblock/b/pub-b/oags.json", "infoblock/b/pub-b/free.json"])
check("D5_exactly_4_files_differ", differing == expected_diff, f"differing={differing}")
mod_ok = all(lfiles[k].replace(NEW_REASON, OLD_REASON) == bfiles[k] for k in differing)
check("D5_diff_is_exactly_cured_sentence", mod_ok)
# D6: negative_space byte-identical across engines on MY fixture
check("D6_negative_space_stable", ba["negative_space"] == la["negative_space"]
      and bb["negative_space"] == lb["negative_space"])
# sanity: no private leak in either full site (corroborates C3 on new fixture)
leak = lambda fs: any(("PRIV-M" in t) or ("PRIV-N" in t) or ("SECRET-LBL" in t) for t in fs.values())
check("D8_no_priv_leak_both", not leak(bfiles) and not leak(lfiles))

print(f"\nRESULT: {len(PASS_)} PASS / {len(FAIL_)} FAIL")
sys.exit(1 if FAIL_ else 0)
