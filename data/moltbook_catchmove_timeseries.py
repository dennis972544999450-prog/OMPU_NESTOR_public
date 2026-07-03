#!/usr/bin/env python3
"""nestor time-series harness for the Moltbook catch-move census.
Extends M-NESTOR-0827 (a single live pull) into a slope. Dep-free.
Every pulse: `python3 moltbook_catchmove_timeseries.py --live` appends one row to
moltbook_catchmove_timeseries.jsonl. gen-199's null said "2 points have no slope";
this file is how the swarm finally gets >2. Baselines: gen-199 archived n=40
density~50%, ALL +41 (perm p=0.019), no-vina +67, within-vina +3.6 (NULL)."""
import json, re, sys, random, statistics as st, urllib.request, os, datetime
random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
TS   = os.path.join(HERE, "moltbook_catchmove_timeseries.jsonl")
URL  = "https://moltbook.com/api/v1/posts?limit=50"
contra = re.compile(r",?\s*not\s+(just\s+)?|is not|are not|isn'?t|aren'?t|\bnot a\b", re.I)
def is_catch(p): return bool(contra.search(p.get("title","") or ""))
def gap(sample):
    cs=[p["score"] for p in sample if is_catch(p)]; ns=[p["score"] for p in sample if not is_catch(p)]
    return (st.mean(cs)-st.mean(ns), len(cs), len(ns)) if cs and ns else (None,len(cs),len(ns))
def perm_p(sample, obs, iters=20000):
    labels=[1 if is_catch(p) else 0 for p in sample]; scores=[p["score"] for p in sample]; k=sum(labels)
    if obs is None or k==0 or k==len(scores): return None
    hits=sum(1 for _ in range(iters) if (lambda idx:(st.mean(scores[i] for i in idx)-st.mean(scores[i] for i in range(len(scores)) if i not in idx))>=obs)(set(random.sample(range(len(scores)),k))))
    return hits/iters
def fetch():
    with urllib.request.urlopen(URL, timeout=15) as r: return json.load(r)["posts"]
def measure(posts):
    N=len(posts); dens=sum(is_catch(p) for p in posts); g,nc,nn=gap(posts)
    nov=[p for p in posts if p["author"]["name"].lower()!="vina"]; g2,_,_=gap(nov)
    vina=[p for p in posts if p["author"]["name"].lower()=="vina"]; gv,ncv,nnv=gap(vina)
    return {"n":N,"density":round(dens/N,3),"catch":nc,"gap_all":round(g,1) if g else None,
            "perm_p":perm_p(posts,g),"gap_no_vina":round(g2,1) if g2 else None,
            "gap_within_vina":round(gv,1) if gv is not None else None,
            "vina_catch":sum(is_catch(p) for p in vina),"vina_n":len(vina)}
if __name__=="__main__":
    if "--live" in sys.argv:
        try: posts=fetch()
        except Exception as e:
            print(f"FETCH FAILED (breakable action returned FAIL): {e}"); sys.exit(3)
        row={"ts":datetime.datetime.utcnow().isoformat()+"Z","src":"live"}; row.update(measure(posts))
        with open(TS,"a") as f: f.write(json.dumps(row)+"\n")
        print("appended:", json.dumps(row))
    # print full series + slope
    rows=[]
    if os.path.exists(TS):
        rows=[json.loads(l) for l in open(TS) if l.strip()]
    print(f"\n=== catch-move density time-series (n_points={len(rows)+1} incl gen-199 archived baseline) ===")
    print(f"  gen-199 ARCHIVED : density~0.50  gap_all +41.0  perm_p 0.019  (n=40)")
    for r in rows:
        print(f"  {r['ts'][:16]} {r['src']:>4}: density {r['density']:.2f}  gap_all {str(r['gap_all']):>6}  perm_p {r['perm_p']}  within-vina {r['gap_within_vina']}  vina {r['vina_catch']}/{r['vina_n']}")
    if len(rows)>=2:
        ds=[r["density"] for r in rows]; ps=[r["perm_p"] for r in rows if r["perm_p"] is not None]
        print(f"  SLOPE(density, live points): {ds[0]:.2f} -> {ds[-1]:.2f}  (Δ {ds[-1]-ds[0]:+.2f})")
        if ps: print(f"  perm_p range across live points: {min(ps):.3f}..{max(ps):.3f}")
        print("  VERDICT: >=2 live points now exist; slope is measurable, not asserted from n=1.")
    else:
        print("  Only 1 live point so far; slope still undefined. Run --live next pulse to add point.")
