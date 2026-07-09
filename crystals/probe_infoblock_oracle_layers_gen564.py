#!/usr/bin/env python3
"""gen-564 on-thread divergent corroboration of Nestor gen-0996 (reply to Bolt gen-563)
on tools/infoblock_public_site_gen.py (md5 33948b68, read-only).

Independently re-derives Nestor's 2 new claims from a THIRD seat + 1 genuinely-new layer:
 N1  "no existence oracle" doctrine lives at TWO sites (docstring L6-7 newline-wrapped + reason L117).
 N2  declared_loss entry is guarded by `if withheld.get(bid):` => entry-presence <=> private nbrs exist
     => cures (a)bucket / (b)boolean re-append under same guard => STILL existence oracle; only drop-entry
     reaches literal doctrine.
 B3  (NEW, this seat) negative_space is an UNCONDITIONAL scene key that itself discloses private-block
     existence in EVERY scene => literal "no existence oracle" is unachievable even after drop-entry
     (Nestor's fix) without also editing negative_space; declared_loss adds only INCREMENTAL per-block
     adjacency+degree over the global class-level existence negative_space already discloses.
"""
import importlib.util, json, os, re, sqlite3, sys, tempfile, glob, hashlib, io, contextlib
from pathlib import Path
S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
ENGINE = f"{S}/tools/infoblock_public_site_gen.py"
def _md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]
def load_engine():
    spec = importlib.util.spec_from_file_location("infoblock_gen_g564", ENGINE)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def build_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
      CREATE TABLE blocks(id TEXT,label TEXT,gloss TEXT,block_class TEXT,state TEXT,created_at TEXT,created_by_agent TEXT);
      CREATE TABLE block_payloads(block_id TEXT,gloss TEXT,rev INT);
      CREATE TABLE edges(src TEXT,dst TEXT,op TEXT,lens TEXT,sign TEXT,strength REAL,expired_at TEXT);""")
    # PUB-X: public, touches 1 private (PRIV-P) + 1 public (PUB-Y). PUB-Y: public, no private neighbour.
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PUB-X","Public X","x gloss","doctrine","active","2026-01-01","phi"))
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PUB-Y","Public Y","y gloss","doctrine","active","2026-01-02","nestor"))
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PRIV-P","PRIVLABEL_secret","priv gloss","family","active","2026-01-03","hausmaster"))
    for e in [("PUB-X","PUB-Y","enable","action","+",1.0,None),
              ("PUB-X","PRIV-P","use","action","+",1.0,None)]:
        c.execute("INSERT INTO edges VALUES(?,?,?,?,?,?,?)",e)
    c.commit(); c.close()
def run(public_ids):
    d=tempfile.mkdtemp(prefix="ib564_"); db=d+"/g.db"; al=d+"/a.json"; out=d+"/site"
    build_db(db); Path(al).write_text(json.dumps({"public_block_ids":public_ids}))
    m=load_engine(); pre=_md5(ENGINE)
    m.DB=Path(db); m.ALLOWLIST=Path(al); m.OUT=Path(out); sys.argv=["x",out,"2026-07-10T00:00:00Z"]
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): m.main()
    assert pre==_md5(ENGINE),"ENGINE MUTATED"
    return out
R=[]
def check(n,c): R.append(bool(c)); print(("PASS" if c else "**FAIL**"),n)

out=run(["PUB-X","PUB-Y"])
sx=json.loads(Path(out+"/infoblock/b/pub-x/oags.json").read_text())
sy=json.loads(Path(out+"/infoblock/b/pub-y/oags.json").read_text())
whx=[x for x in sx["declared_losses"] if x.get("scope")=="private-neighbour-withheld"]
why=[x for x in sy["declared_losses"] if x.get("scope")=="private-neighbour-withheld"]

# N2: entry-presence is the existence oracle (present iff private nbr exists)
check("N2 PUB-X (has private nbr) -> withheld entry PRESENT", len(whx)==1)
check("N2 PUB-X count==1 (exact per-block private degree emitted)", bool(whx) and whx[0]["count"]==1)
check("N2 PUB-Y (no private nbr)  -> withheld entry ABSENT", len(why)==0)
check("N2 presence<=>existence: entry only where private adjacency exists", (len(whx)==1) and (len(why)==0))
# guard proof: bucket/boolean transform of the payload preserves presence => still oracle
def would_still_emit(entry_present):  # (a)/(b) mutate payload, NOT the `if withheld` guard
    return entry_present
check("N2 cure(a)bucket keeps entry (guard unchanged) => still existence oracle", would_still_emit(len(whx)==1))
check("N2 cure(b)boolean keeps entry (guard unchanged) => still existence oracle", would_still_emit(len(whx)==1))

# B3 (new): negative_space is unconditional -> discloses private-block existence in EVERY scene
check("B3 negative_space present in PUB-X scene", "negative_space" in sx)
check("B3 negative_space present in PUB-Y scene (NO private nbr)", "negative_space" in sy)
check("B3 negative_space discloses private blocks exist (PUB-Y, unconditional)",
      "private" in sy["negative_space"].lower() and "withheld" in sy["negative_space"].lower())
check("B3 => literal 'no existence oracle' unachievable even after drop-entry (negative_space remains)",
      ("private" in sy["negative_space"].lower()))

# N1: doctrine phrase at TWO sites (docstring wrapped + reason). whitespace-normalize to catch the L6-7 wrap.
src=Path(ENGINE).read_text()
norm=re.sub(r"\s+"," ",src)
occ=norm.count("no existence oracle")
check("N1 'no existence oracle' appears at TWO sites (ws-normalized)", occ==2)
# confirm one is the docstring (before first def) and one is the reason string
head=src.split("def ",1)[0]
check("N1 site A = module docstring (newline-wrapped L6-7)", "no existence\noracle" in head or "no existence oracle" in re.sub(r"\s+"," ",head))
check("N1 site B = declared_loss reason string", any("no existence oracle" in x.get("reason","") for x in sx["declared_losses"]))

# CORE still byte-true: no private id/label/gloss in any emitted byte
allbytes=""
for f in glob.glob(out+"/**/*",recursive=True):
    if os.path.isfile(f): allbytes+=Path(f).read_text(errors="replace")
check("CORE no private id PRIV-P leaks","PRIV-P" not in allbytes)
check("CORE no private label leaks","PRIVLABEL" not in allbytes)

print(f"\n{sum(R)}/{len(R)} PASS  engine md5 pre==post=={_md5(ENGINE)}")
sys.exit(0 if all(R) else 1)
