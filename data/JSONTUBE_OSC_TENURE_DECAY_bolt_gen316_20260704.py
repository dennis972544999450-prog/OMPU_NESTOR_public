"""
osc_tenure_decay.py — Bolt gen-316.
DIRECT ANSWER to Den's design-choice "нет вечных королей" (no eternal kings).

Lineage state (gen-308->315, twice-confirmed): inverse-degree pricing yields a
FLAT degree-mass (Gini ~0.25) but ALSO a PERSISTENT topic-central rank-1 leader
(gen-314 found it; gen-315 could not break it with random tie-break — existence
robust, exact tenure soft). So inverse pricing => stable anchor + flat mass.

Den's fork: if you want ROTATING leaders instead of a stable anchor, you need a
mechanism that unseats whoever sits on top. gen-314/315 handoff named the lever:
add a price term that grows with the DURATION a node holds rank-1 (tenure), not
only with its degree. This probe RUNS that lever.

MECHANISM: price(n) = indeg[n] + LAMBDA * tenure_count[n]
  where tenure_count[n] = number of past rounds n was rank-1 (leader).
  Citations flow to CHEAPEST candidates => a long-sitting leader becomes
  progressively expensive => avoided => unseated. LAMBDA=0 == gen-308/309 baseline.

FAILABLE (this can NOT work, two named failure modes):
 (F1) decay may unseat the leader but ROCK Gini BACK UP — leadership rotates at
      the cost of uniformity (a new spike each time the penalty resets the field).
      Then decay does NOT give Den "flat mass + rotation"; it trades one for other.
 (F2) decay may be INERT — if rank-1 is structurally pinned by topic-centrality
      (eligibility), the price penalty is dwarfed by degree and tenure_frac barely
      moves. Then "no eternal kings" is NOT reachable via pricing at all.
 SUCCESS = tenure_frac DROPS and distinct_rank1 RISES while final_gini STAYS flat
      (~0.25) AND Gini trajectory does not spike. Only then is Den's fork clean.

random tie-break (gen-315 honest control, avoids dict-order artifact).
curl read-only. worker untouched. NOT deployed.
"""
import json, collections, math, random, subprocess

def fetch(u):
    out = subprocess.check_output(["curl","-s","-H","Accept: application/json","-A","bolt-gen316/1.0",u], timeout=40)
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

def run(lam, seedval, rounds=400, k=3, sim_th=0.15):
    """lam = tenure-decay coefficient. lam=0 => gen-308/309 baseline (pure inverse)."""
    rng=random.Random(seedval)
    indeg=collections.Counter({ID(p):0 for p in POSTS})
    for p in POSTS:
        for key in ("edges","refs","references"):
            for tgt in (p.get(key) or []):
                if isinstance(tgt,str): indeg[tgt]+=1
    tenure_count=collections.Counter()          # rounds each node held rank-1
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
            # inverse pricing + tenure decay: price = indeg + lam*tenure_count
            cand.sort(key=lambda x:(indeg[x[1]]+lam*tenure_count[x[1]], -x[0]))
            for _,cid in cand[:k]: indeg[cid]+=1
        # rank-1 by RAW in-degree (leadership = who is most-cited), random tie-break
        mx=max(indeg.values())
        tied=[n for n in node_order if indeg[n]==mx]
        top=rng.choice(tied)
        per_round_top.append(top)
        tenure_count[top]+=1
        if (r+1) in (100,200,300,400): gini_traj[r+1]=round(gini(list(indeg.values())),3)
    tc=collections.Counter(per_round_top)
    dom_top,dom_ten=tc.most_common(1)[0]
    active=len(per_round_top)
    return {
        "lam":lam,
        "final_gini":round(gini(list(indeg.values())),3),
        "gini_traj":gini_traj,
        "final_max_indeg":max(indeg.values()),
        "tenure_frac":round(dom_ten/active,3) if active else None,
        "distinct_rank1":len(tc),
    }

def avg(lam, seeds, rounds=400):
    rs=[run(lam,sd,rounds) for sd in seeds]
    return {
        "lam":lam,
        "mean_final_gini":round(sum(r["final_gini"] for r in rs)/len(rs),3),
        "mean_tenure_frac":round(sum(r["tenure_frac"] for r in rs)/len(rs),3),
        "mean_distinct_rank1":round(sum(r["distinct_rank1"] for r in rs)/len(rs),1),
        "mean_final_max_indeg":round(sum(r["final_max_indeg"] for r in rs)/len(rs),1),
    }

SEEDS=(1,7,13,29,42,101)
print(f"corpus N={N}  hub-excluded={len(HUB)}  seeds={SEEDS}\n")
print("SUCCESS = tenure_frac DROPS & distinct_rank1 RISES while final_gini stays flat (~0.25).")
print("F1 = gini rises (rotation bought with uniformity). F2 = tenure_frac inert (leader structural).\n")
print("=== per-seed detail at seed=42 (gen-314's seed), lam sweep ===")
for lam in (0.0,0.5,1.0,2.0,5.0):
    print(json.dumps(run(lam,42), ensure_ascii=False))
print("\n=== averaged over 6 seeds, lam sweep ===")
for lam in (0.0,0.25,0.5,1.0,2.0,5.0,10.0):
    print(json.dumps(avg(lam,SEEDS), ensure_ascii=False))
