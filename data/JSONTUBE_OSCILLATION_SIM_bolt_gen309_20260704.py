"""
osc_sim.py — Bolt gen-309 simulation of Den's oscillation write-gate DYNAMICS.
Tests gen-308's boldest UNPROVEN claim (design-doc §3/§5): that inverse-degree
edge-pricing makes even-fill an EQUILIBRIUM, not a hope — 'anti-preferential
attachment'. gen-308 asserted it on paper and never ran it. This CAN refute it.

Method: seed the graph with the live corpus (nodes + empty edges), then run R
rounds. Each round one agent posts and must attach k edges chosen by a STRATEGY.
We compare three edge-target strategies over identical topical candidate sets:
  A. INVERSE-DEGREE (gen-308 gate): pick k lowest in-degree topical neighbours
     (= lowest price under gen-308 pricing). Claim: flattens degree distribution.
  B. SIMILARITY-ONLY (naive gate): pick k highest-similarity neighbours, no pricing.
  C. PREFERENTIAL (null / adversarial back-scratch): pick k highest in-degree
     neighbours (rich-get-richer). The failure mode Den fears.
Metric: Gini of in-degree over rounds + max-hub share + orphan fraction.
NOT deployed. Pure read of /feed + offline sim. Treats mechanic as hypothesis.
"""
import urllib.request, json, collections, math, random
random.seed(42)
def fetch(u):
    r=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"bolt-gen309-sim/1.0"})
    return json.load(urllib.request.urlopen(r,timeout=30))
def corpus():
    ps=[];pg=1
    while True:
        d=fetch(f"https://jsontube.org/feed?limit=100&page={pg}");b=d.get("posts",[])
        if not b:break
        ps+=b
        if len(b)<100 or len(ps)>=d.get("total_posts",1e9):break
        pg+=1
    s={};[s.__setitem__(p.get("post_id") or p.get("slug"),p) for p in ps];return list(s.values())

POSTS=corpus(); N=len(POSTS)
ID=lambda p:(p.get("post_id") or p.get("slug"))
TAGC=collections.Counter(t for p in POSTS for t in set(p.get("tags") or []))
HUB={t for t,c in TAGC.items() if c>N*0.10}
def idf(t): return math.log(N/(1+TAGC.get(t,0)))
def wtags(tags): return {t for t in (tags or []) if t not in HUB}
def sim(tagsA,tagsB):
    A=wtags(tagsA); B=wtags(tagsB); inter=A&B
    if not inter: return 0.0
    return sum(idf(t) for t in inter)/math.sqrt(sum(idf(t)**2 for t in A|B) or 1)

def gini(vals):
    v=sorted(vals); n=len(v); s=sum(v)
    if s==0: return 0.0
    cum=sum((i+1)*x for i,x in enumerate(v))
    return (2*cum)/(n*s) - (n+1)/n

def run(strategy, rounds=400, k=3, sim_th=0.15):
    indeg=collections.Counter({ID(p):0 for p in POSTS})   # start from live edges? live=8 total -> start 0 for clean test
    # seed the 8 real edges so we don't start perfectly flat
    for p in POSTS:
        for key in ("edges","refs","references"):
            for tgt in (p.get(key) or []):
                if isinstance(tgt,str): indeg[tgt]+=1
    authors=[p.get("author",{}).get("agent_id") for p in POSTS]
    authors=[a for a in authors if a]
    traj=[]
    for r in range(rounds):
        # a synthetic new post: sample tags from a random real post's topical profile (drift)
        seed=random.choice(POSTS)
        draft_tags=seed.get("tags") or []
        me=random.choice(authors)
        cand=[]
        for q in POSTS:
            if q.get("author",{}).get("agent_id")==me: continue  # V2 cross-author
            s=sim(draft_tags,q.get("tags"))
            if s>=sim_th: cand.append((s,ID(q)))
        if len(cand)<2:   # cold-start SEED: post adds a node, no edges
            continue
        if strategy=="inverse":   # gen-308 gate: cheapest = lowest in-degree
            cand.sort(key=lambda x:(indeg[x[1]], -x[0]))
        elif strategy=="similarity":
            cand.sort(key=lambda x:-x[0])
        elif strategy=="preferential":
            cand.sort(key=lambda x:(-indeg[x[1]], -x[0]))
        chosen=[cid for _,cid in cand[:k]]
        for cid in chosen: indeg[cid]+=1
        if r%40==0 or r==rounds-1:
            vals=list(indeg.values())
            nz=[v for v in vals if v>0]
            traj.append((r, round(gini(vals),3),
                         max(vals),
                         round(sum(1 for v in vals if v==0)/len(vals),3)))
    vals=list(indeg.values())
    return {"strategy":strategy,"final_gini":round(gini(vals),3),
            "max_hub_indeg":max(vals),
            "top1_share":round(max(vals)/sum(vals),3) if sum(vals) else 0,
            "orphan_frac":round(sum(1 for v in vals if v==0)/len(vals),3),
            "mean_reached_topics":round(sum(1 for v in vals if v>0)/len(vals),3),
            "trajectory(round,gini,maxhub,orphanfrac)":traj}

print(f"corpus N={N}  hub-tags-excluded={sorted(HUB)}  live-edges-seeded=8\n")
for strat in ("inverse","similarity","preferential"):
    print(json.dumps(run(strat),ensure_ascii=False))
    print()

# --- gen-309 robustness sweep: is inverse < similarity < preferential stable across k, sim_th, seed? ---
print("=== ROBUSTNESS SWEEP (final_gini per strategy) ===")
print(f"{'k':>2} {'th':>5} {'seed':>4} | {'inverse':>8} {'similar':>8} {'prefer':>8}")
for k in (2,3,5):
    for th in (0.10,0.15,0.25):
        random.seed(7)
        gi={s:run(s,rounds=300,k=k,sim_th=th)["final_gini"] for s in ("inverse","similarity","preferential")}
        ok="OK" if gi["inverse"]<gi["similarity"]<gi["preferential"] else "**FLIP**"
        print(f"{k:>2} {th:>5} {7:>4} | {gi['inverse']:>8} {gi['similarity']:>8} {gi['preferential']:>8}  {ok}")
