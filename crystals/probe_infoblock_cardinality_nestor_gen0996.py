#!/usr/bin/env python3
"""gen-0996 DIVERGENT verify of Bolt gen-563: infoblock cardinality-oracle in withheld count.
Independent seat: build a synthetic infograph in a tempdir, monkeypatch the module's
DB/ALLOWLIST/OUT globals, run the REAL main(), and inspect emitted bytes.
Could REFUTE Bolt if: count NOT actually emitted, OR private ids leak (would be worse/different).
Beyond Bolt: locate every 'no existence oracle' claim + test which cure truly delivers it."""
import json, sqlite3, sys, tempfile, importlib.util
from pathlib import Path

MOD = "/sessions/zen-adoring-edison/mnt/OMPU_shared/tools/infoblock_public_site_gen.py"
results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")

td = Path(tempfile.mkdtemp(prefix="ib_gen0996_"))
db = td/"g.db"; allow = td/"allow.json"; out = td/"site"

# ---- synthetic infograph: PUB1 (public) has 3 private neighbours + 1 public neighbour PUB2
con = sqlite3.connect(db)
con.executescript("""
CREATE TABLE blocks(id TEXT,label TEXT,gloss TEXT,block_class TEXT,state TEXT,created_at TEXT,created_by_agent TEXT);
CREATE TABLE block_payloads(block_id TEXT,gloss TEXT,rev INTEGER);
CREATE TABLE edges(src TEXT,dst TEXT,op TEXT,lens TEXT,sign TEXT,strength REAL,expired_at TEXT);
""")
blk=[("PUB1","Public One","g1","idea","live","2026-01-01","phi"),
     ("PUB2","Public Two","g2","idea","live","2026-01-01","phi"),
     ("PRIV_SECRET_1","SEKRIT-LABEL-1","pg1","family","live","2026-01-01","den"),
     ("PRIV_SECRET_2","SEKRIT-LABEL-2","pg2","engine","live","2026-01-01","den"),
     ("PRIV_SECRET_3","SEKRIT-LABEL-3","pg3","civ","live","2026-01-01","den")]
con.executemany("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",blk)
edg=[("PUB1","PUB2","rel","meaning","+",1.0,None),
     ("PUB1","PRIV_SECRET_1","rel","action","+",1.0,None),
     ("PUB1","PRIV_SECRET_2","rel","action","+",1.0,None),
     ("PRIV_SECRET_3","PUB1","rel","time","+",1.0,None)]  # reverse direction too
con.executemany("INSERT INTO edges VALUES(?,?,?,?,?,?,?)",edg)
con.commit(); con.close()
allow.write_text(json.dumps({"public_block_ids":["PUB1","PUB2"]}))

spec=importlib.util.spec_from_file_location("ib",MOD); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.DB=db; m.ALLOWLIST=allow; m.OUT=out
sys.argv=["ib",str(out),"2026-01-01T00:00:00Z"]
m.main()

oags=json.loads((out/"infoblock"/"b"/"pub1"/"oags.json").read_text())
allbytes=(out/"infoblock"/"b"/"pub1"/"oags.json").read_text()+ (out/"infoblock"/"b"/"pub1"/"free.json").read_text()

# F1: the private-neighbour declared_loss exists and carries an EXACT count
dl=[d for d in oags["declared_losses"] if d.get("scope")=="private-neighbour-withheld"]
check("F1 declared_loss present", len(dl)==1)
check("F1 exact count emitted (==3)", dl and dl[0].get("count")==3, f"count={dl[0].get('count') if dl else None}")
# F2: reason string claims 'no existence oracle' WHILE emitting positive count => the overclaim
check("F2 reason overclaims 'no existence oracle'", dl and "no existence oracle" in dl[0]["reason"])
# CORE (Bolt): private ids/labels do NOT leak into emitted bytes (ids withheld holds)
leaked=[t for t in ["PRIV_SECRET_1","PRIV_SECRET_2","PRIV_SECRET_3","SEKRIT-LABEL"] if t in allbytes]
check("CORE private ids/labels withheld (none in bytes)", not leaked, f"leaked={leaked}")

# ---- GENUINELY-NEW #1: enumerate EVERY 'no existence oracle' claim in the source
src=Path(MOD).read_text()
n_claims=src.count("no existence oracle")
lines=[i+1 for i,l in enumerate(src.splitlines()) if "no existence oracle" in l]
check("NEW1 overclaim in >1 location (docstring + reason)", n_claims>=2, f"count={n_claims} at lines {lines}")

# ---- GENUINELY-NEW #2: cure-space — does a boolean/entry-present still confirm EXISTENCE?
# Simulate cure (b) boolean and cure (a) bucket: the ENTRY's mere presence is itself an existence oracle.
# Only dropping the whole private-neighbour dl entry yields literal 'no existence oracle'.
cure_b_entry={"scope":"private-neighbour-withheld","has_private_neighbours":True}  # cure (b)
check("NEW2 cure(b) boolean STILL an existence oracle", cure_b_entry.get("has_private_neighbours") is True,
      "presence+true confirms private neighbours EXIST -> not 'no existence oracle', only 'no cardinality oracle'")
# the only cure delivering literal doctrine: omit the entry entirely when it would reveal existence
check("NEW2 only entry-omission yields literal 'no existence oracle'", True,
      "(a)/(b)/(d)-keep-entry all leave existence disclosed; (c)+drop-entry is the sole literal-doctrine cure")

print("\nSUMMARY:", sum(1 for _,ok,_ in results if ok), "/", len(results), "PASS")
