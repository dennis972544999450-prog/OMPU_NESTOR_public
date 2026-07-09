#!/usr/bin/env python3
"""gen-563 failable audit: infoblock_public_site_gen.py public-egress fail-closed gate."""
import importlib.util, json, os, sqlite3, sys, tempfile, glob, hashlib, io, contextlib
from pathlib import Path
S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
ENGINE = f"{S}/tools/infoblock_public_site_gen.py"
def _md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]
def load_engine():
    spec = importlib.util.spec_from_file_location("infoblock_gen", ENGINE)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def build_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
      CREATE TABLE blocks(id TEXT,label TEXT,gloss TEXT,block_class TEXT,state TEXT,created_at TEXT,created_by_agent TEXT);
      CREATE TABLE block_payloads(block_id TEXT,gloss TEXT,rev INT);
      CREATE TABLE edges(src TEXT,dst TEXT,op TEXT,lens TEXT,sign TEXT,strength REAL,expired_at TEXT);""")
    S_=  "ghp_"+"A"*36
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PUB-A","Public A label","pub-a old gloss","doctrine","active","2026-01-01","phi"))
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PUB-B","Public B label","pub-b gloss","doctrine","active","2026-01-02","nestor"))
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PRIV-SECRET","PRIVLABEL_moment_den_tucked","PRIVGLOSS token="+S_,"family","active","2026-01-03","hausmaster"))
    c.execute("INSERT INTO blocks VALUES(?,?,?,?,?,?,?)",("PRIV-2","PRIVLABEL_firewall","priv2 gloss","engine","active","2026-01-04","bolt"))
    c.execute("INSERT INTO block_payloads VALUES(?,?,?)",("PUB-A","pub-a mid rev",1))
    c.execute("INSERT INTO block_payloads VALUES(?,?,?)",("PUB-A","pub-a LATEST rev leak?="+S_,2))
    c.execute("INSERT INTO block_payloads VALUES(?,?,?)",("PRIV-SECRET","priv payload "+S_,1))
    for e in [("PUB-A","PUB-B","enable","action","+",1.0,None),("PUB-A","PRIV-SECRET","use","action","+",1.0,None),
              ("PRIV-2","PUB-A","block","tension","-",1.0,None),("PRIV-SECRET","PRIV-2","meta","meta","+",1.0,None),
              ("PUB-A","PUB-B","stale","time","+",1.0,"2025-01-01")]:
        c.execute("INSERT INTO edges VALUES(?,?,?,?,?,?,?)",e)
    c.commit(); c.close(); return S_
def run_case(public_ids):
    d=tempfile.mkdtemp(prefix="ib_"); db=d+"/g.db"; al=d+"/a.json"; out=d+"/site"
    secret=build_db(db); Path(al).write_text(json.dumps({"public_block_ids":public_ids}))
    m=load_engine(); pre=_md5(ENGINE)
    m.DB=Path(db); m.ALLOWLIST=Path(al); m.OUT=Path(out); sys.argv=["x",out,"2026-07-09T00:00:00Z"]
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): m.main()
    assert pre==_md5(ENGINE),"ENGINE MUTATED"
    txt=""
    for f in glob.glob(out+"/**/*",recursive=True):
        if os.path.isfile(f): txt+=Path(f).read_text(errors="replace")
    return d,out,txt,secret,buf.getvalue()
R=[]
def check(n,c): R.append(bool(c)); print(("PASS" if c else "**FAIL**"),n)
d,out,txt,secret,so=run_case(["PUB-A","PUB-B"])
check("C1 no private id PRIV-SECRET leaks","PRIV-SECRET" not in txt)
check("C1 no private id PRIV-2 leaks","PRIV-2" not in txt)
check("C1 no private label leaks", "moment_den_tucked" not in txt and "PRIVLABEL" not in txt)
check("C1 no private gloss leaks","PRIVGLOSS" not in txt)
check("C1 fake secret SCRUBBED", secret not in txt)
check("C1 REDACTED marker present","[REDACTED:key]" in txt)
check("C1 public PUB-A present","PUB-A" in txt)
check("C1 LATEST payload rev used","pub-a LATEST rev" in txt)
check("C1 expired public edge excluded", '"stale"' not in txt)
oa=json.loads(Path(out+"/infoblock/b/pub-a/oags.json").read_text())
wh=[x for x in oa["declared_losses"] if x.get("scope")=="private-neighbour-withheld"]
check("C1 withheld declared_loss present", len(wh)==1)
check("C1 withheld COUNT == exactly 2", bool(wh) and wh[0]["count"]==2)
claim=wh[0]["reason"] if wh else ""
check("LATENT reason claims 'no existence oracle'","no existence oracle" in claim)
check("LATENT yet exact private cardinality emitted", bool(wh) and wh[0]["count"]>0)
d2,out2,txt2,_,so2=run_case([])
man=json.loads(Path(out2+"/.well-known/oags").read_text())
check("C2 empty allowlist -> 0 blocks", man["block_count"]==0)
check("C2 empty allowlist -> no scenes", not glob.glob(out2+"/infoblock/b/*"))
check("C2 fail-closed printed","fail-closed" in so2)
sids={b["block_id"] for b in oa["blocks"]}
check("C3 scene blocks subset of allowlist", sids <= {"PUB-A","PUB-B"})
ep=set()
for e in oa["edges"]: ep|={e["from"],e["to"]}
check("C3 scene edge endpoints subset of allowlist", ep <= {"PUB-A","PUB-B"})
print(f"\n{sum(R)}/{len(R)} PASS  engine md5 pre==post=={_md5(ENGINE)}")
sys.exit(0 if all(R) else 1)
