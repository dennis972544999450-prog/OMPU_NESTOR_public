"""
osc_degree_leak_gen317.py — Bolt gen-317.
TRUE degree-LEAK decay (the lever whose NAME matches its intent), answering
Den's fork "нет вечных королей" and Nestor's membrane M-NESTOR-0915 (1783170695).

gen-316 SCAR: named its lever "decay" but built a TAX (price += lam*tenure) — it
FROZE the throne (backfire). Honest decay = SUBTRACT accumulated capital, not
surcharge access. This probe subtracts.

MECHANISM (per round, after fresh citations flow in):
    indeg[n] *= (1 - DELTA)   for all n   (global multiplicative capital leak)
This is the discrete analog of Dorogovtsev-Mendes node-aging Pi ~ k*tau^(-alpha):
old accumulated degree erodes; a node uncited for a while decays off the throne.
DELTA=0 == gen-308/309 baseline (pure inverse pricing, no leak).

NESTOR MEMBRANE PREDICTION (falsifiable, DM literature):
 NOT monotonic "more leak -> more rotation". Expect a PHASE TRANSITION across DELTA:
  (a) weak leak   -> throne HOLDS, softened (~ freeze): tenure_frac high, gini high.
  (b) narrow crit -> TRUE king rotation: tenure_frac drops, distinct_rank1 rises,
                     WHILE gini stays elevated (a throne still exists, occupant changes)
                     AND topic-anchor (gen-314 central node) survives.
  (c) strong leak -> leadership STRUCTURE DISSOLVES: degree collapses toward
                     exponential, gini->low, max_indeg->low, topic-anchor gone.
                     Throne is not rotated but ABOLISHED.
 If DELTA-sweep shows boundary freeze->rotate->dissolve => DM holds.
 If MONOTONIC (rotation grows smoothly with no dissolution, or no rotation ever)
   => finding AGAINST DM in this discrete topic-sim regime => separate crystal.

Nestor CAVEAT tracked: dissolution vs rotation is distinguished by whether a
THRONE still exists (gini elevated + max_indeg elevated) and whether the leader is
still TOPIC-CENTRAL (gen-314 anchor). We measure leader topic-centrality percentile.

curl read-only. worker/schedule untouched. NOT deployed.
"""
import json, collections, math, random, subprocess

def fetch(u):
    out = subprocess.check_output(["curl","-s","-H","Accept: application/json","-A","bolt-gen317/1.0",u], timeout=40)
    return json.loads(out)

def corpus():
    ps=[]; pg=1
    while True:
        d=fetch(f"https://jsontube.org/feed?limit=100&page={pg}"); b=d.get("posts",[])
        if not b: break
        ps+=b
        if len(b)<100 or len(ps)>=d.get("total_posts",1e9): break
        pg+=1
    s={}; [s.__setitem__(p.get("post_id") or p.get("slug"),p) for p in ps]; return list(s.values())

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

# topic-centrality: sum of sim(node, all others) — gen-314 anchor lives at the top of this
def topic_centrality():
    cent={}
    for p in POSTS:
        pid=ID(p); tp=p.get("tags")
        cent[pid]=sum(sim(tp,q.get("tags")) for q in POSTS if ID(q)!=pid)
    return cent
CENT=topic_centrality()
CENT_RANK={pid:r for r,(pid,_) in enumerate(sorted(CENT.items(),key=lambda x:-x[1]))}  # 0=most central

def run(delta, seedval, rounds=400, k=3, sim_th=0.15):
    """delta = per-round multiplicative capital leak. delta=0 => baseline."""
    rng=random.Random(seedval)
    indeg=collections.Counter({ID(p):0.0 for p in POSTS})
    for p in POSTS:
        for key in ("edges","refs","references"):
            for tgt in (p.get(key) or []):
                if isinstance(tgt,str): indeg[tgt]+=1.0
    authors=[p.get("author",{}).get("agent_id") for p in POSTS]; authors=[a for a in authors if a]
    node_order=[ID(p) for p in POSTS]
    per_round_top=[]; gini_traj={}
    for r in range(rounds):
        seed=rng.choice(POSTS); draft_tags=seed.get("tags") or []; me=rng.choice(authors)
        cand=[]
        for q in POSTS:
            if q.get("author",{}).get("agent_id")==me: continue
            s=sim(draft_tags,q.get("tags"))
            if s>=sim_th: cand.append((s,ID(q)))
        if len(cand)>=2:
            # pure inverse pricing (cheapest = lowest current indeg wins citations)
            cand.sort(key=lambda x:(indeg[x[1]], -x[0]))
            for _,cid in cand[:k]: indeg[cid]+=1.0
        # HONEST DECAY: erode accumulated capital of EVERY node
        if delta>0:
            for n in indeg: indeg[n]*=(1.0-delta)
        # rank-1 = most-cited node (throne), random tie-break within eps
        mx=max(indeg.values())
        tied=[n for n in node_order if mx-indeg[n]<1e-9]
        top=rng.choice(tied)
        per_round_top.append(top)
        if (r+1) in (100,200,300,400): gini_traj[r+1]=round(gini(list(indeg.values())),3)
    tc=collections.Counter(per_round_top)
    dom_top,dom_ten=tc.most_common(1)[0]
    active=len(per_round_top)
    vals=list(indeg.values()); mean_deg=sum(vals)/len(vals)
    return {
        "delta":delta,
        "final_gini":round(gini(vals),3),
        "gini_traj":gini_traj,
        "final_max_indeg":round(max(vals),1),
        "max_over_mean":round(max(vals)/mean_deg,1) if mean_deg else None,  # throne sharpness; ->1 = dissolved
        "tenure_frac":round(dom_ten/active,3) if active else None,
        "distinct_rank1":len(tc),
        "leader_cent_rank":CENT_RANK.get(dom_top),   # 0=most topic-central (gen-314 anchor); high=arbitrary
    }

def avg(delta, seeds, rounds=400):
    rs=[run(delta,sd,rounds) for sd in seeds]
    g=lambda key:[r[key] for r in rs if r[key] is not None]
    return {
        "delta":delta,
        "gini":round(sum(g("final_gini"))/len(g("final_gini")),3),
        "tenure_frac":round(sum(g("tenure_frac"))/len(g("tenure_frac")),3),
        "distinct_rank1":round(sum(g("distinct_rank1"))/len(g("distinct_rank1")),1),
        "max_indeg":round(sum(g("final_max_indeg"))/len(g("final_max_indeg")),1),
        "max_over_mean":round(sum(g("max_over_mean"))/len(g("max_over_mean")),1),
        "leader_cent_rank":round(sum(g("leader_cent_rank"))/len(g("leader_cent_rank")),1),
    }

SEEDS=(1,7,13,29,42,101)
print(f"corpus N={N}  hub-excluded={len(HUB)}  seeds={SEEDS}")
print("HONEST DECAY: indeg *= (1-delta) per round (SUBTRACT capital, not surcharge).")
print("Nestor DM prediction: freeze (small d) -> ROTATE (crit window) -> DISSOLVE (large d).")
print("  rotate = distinct_rank1 UP & tenure_frac DOWN while gini/max_over_mean STAY elevated.")
print("  dissolve = gini->low, max_over_mean->~1, leader_cent_rank goes arbitrary (throne gone).\n")
print("=== per-seed detail at seed=42 (gen-314 anchor seed), delta sweep ===")
for d in (0.0,0.01,0.02,0.05,0.1,0.2,0.4):
    print(json.dumps(run(d,42), ensure_ascii=False))
print("\n=== averaged over 6 seeds, fine delta sweep (hunt the phase boundary) ===")
for d in (0.0,0.005,0.01,0.02,0.03,0.05,0.08,0.12,0.2,0.35,0.5):
    print(json.dumps(avg(d,SEEDS), ensure_ascii=False))
