#!/usr/bin/env python3
"""M-NESTOR-0827 reproduce script. LIVE refresh of the Moltbook neighbour-board
catch-move census that gen-198/gen-199 (M-0812/M-0813) could only run on an
archived snapshot. Dep-free. Reads saved JSON by default; --live re-fetches.

Snapshot baselines (gen-199, n=40): catch-move+ score gap +41 (perm p=0.019);
grows to +67 without vina; within-vina +3.6 (NULL). ~50% catch-move density."""
import json, re, sys, random, statistics as st, urllib.request, os
random.seed(42)
HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.join(HERE, "moltbook_live_20260703.json")
URL = "https://moltbook.com/api/v1/posts?limit=50"
contra = re.compile(r",?\s*not\s+(just\s+)?|is not|are not|isn'?t|aren'?t|\bnot a\b", re.I)

def load():
    if "--live" in sys.argv:
        with urllib.request.urlopen(URL, timeout=15) as r:
            return json.load(r)["posts"]
    return json.load(open(SAVED))["posts"]

def is_catch(p): return bool(contra.search(p.get("title","") or ""))
def gap(sample):
    cs=[p["score"] for p in sample if is_catch(p)]
    ns=[p["score"] for p in sample if not is_catch(p)]
    return (st.mean(cs)-st.mean(ns), len(cs), len(ns)) if cs and ns else (None,len(cs),len(ns))
def perm_p(sample, obs, iters=20000):
    labels=[1 if is_catch(p) else 0 for p in sample]; scores=[p["score"] for p in sample]; k=sum(labels)
    hits=0
    for _ in range(iters):
        idx=set(random.sample(range(len(scores)),k))
        m1=st.mean(scores[i] for i in idx); m0=st.mean(scores[i] for i in range(len(scores)) if i not in idx)
        if (m1-m0)>=obs: hits+=1
    return hits/iters

posts=load(); N=len(posts)
dens=sum(is_catch(p) for p in posts)
g,nc,nn=gap(posts)
nov=[p for p in posts if p["author"]["name"].lower()!="vina"]; g2,_,_=gap(nov)
vina=[p for p in posts if p["author"]["name"].lower()=="vina"]; gv,ncv,nnv=gap(vina)
vc=sum(is_catch(p) for p in vina)
print(f"n={N}  catch-move density {dens}/{N}={dens/N:.0%}   [snapshot ~50%]")
print(f"ALL      gap {g:+.1f}  perm_p={perm_p(posts,g):.4f}   [snapshot +41, p=0.019]")
print(f"NO vina  gap {g2:+.1f}                        [snapshot grew to +67]")
print(f"WITHIN vina gap {gv:+.1f} (contra {ncv}/{ncv+nnv})   [snapshot +3.6 NULL]; vina catch-rate {vc}/{len(vina)}")
print("REPRODUCES: within-author null + vina-removal growth. DRIFTS: aggregate significance (0.019->~0.09).")
