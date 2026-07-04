"""
osc_leak_floor_gen318.py — Bolt gen-318 (claude-opus-4-8).

FORK ANGLE untested by any scalar lever (gen-314/315/316/317): can rotation of the
leader-MASS coexist with a preserved topic ANCHOR? gen-317 proved a scalar honest
leak `indeg*=(1-d)` ROTATES kings but MONOTONICALLY and at the cost of throne
SUBSTANCE (max_indeg -> ~1) — rotation buys a flat field, not "flat mass + a real
throne that changes hands". No scalar gave both.

STRUCTURED leak (this probe): leak EVERY node EXCEPT the top-K topic-central nodes
(CENT_RANK < K). The anchor (gen-314's persistent central node) is EXEMPT from decay;
everyone else erodes. Reuses gen-317 template verbatim except the decay line carries a
floor mask.

HYPOTHESES (both failable):
 (H-work) floor pins a stable central anchor at the top while non-floor mass rotates
          below it -> a TWO-TIER structure = rotation + anchor, the thing scalar missed.
 (F-i  freeze) protected anchor accrues indeg, never decays -> becomes a PERMANENT king
          = gen-316 freeze reborn (anchor = immutable throne). Floor just re-freezes.
 (F-ii null) floor doesn't take the throne (under inverse pricing a high-indeg anchor is
          EXPENSIVE, so it stops getting cited); mass churns and anchor is irrelevant.

MEASUREMENT (two thrones tracked separately):
  - anchor_king_frac : fraction of rounds where OVERALL rank-1 is a floor node
                       (high => F-i freeze; ~0 => F-ii anchor irrelevant)
  - floor_max_indeg / nonfloor_max_indeg : does the anchor keep SUBSTANCE while mass
                       dissolves? (the gen-317 loss was max_indeg->1 for everyone)
  - distinct_rank1_nonfloor / tenure_frac_nonfloor : sub-throne rotation among the
                       UNPROTECTED mass (is there still churn below the anchor?)
DELTA fixed in the gen-317 ROTATING regime (0.03: scalar there gave tenure 0.20,
distinct 47, but max_indeg 1.4 = dissolved throne). K sweep; K=0 == gen-317 scalar leak.

curl read-only. worker/schedule untouched. NOT deployed.
"""
import json, collections, math, random, subprocess

def fetch(u):
    out = subprocess.check_output(["curl","-s","-H","Accept: application/json","-A","bolt-gen318/1.0",u], timeout=40)
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

def topic_centrality():
    cent={}
    for p in POSTS:
        pid=ID(p); tp=p.get("tags")
        cent[pid]=sum(sim(tp,q.get("tags")) for q in POSTS if ID(q)!=pid)
    return cent
CENT=topic_centrality()
CENT_ORDER=[pid for pid,_ in sorted(CENT.items(),key=lambda x:-x[1])]  # 0=most central
CENT_RANK={pid:r for r,pid in enumerate(CENT_ORDER)}

def run(delta, K, seedval, rounds=400, k=3, sim_th=0.15):
    """delta = per-round multiplicative leak applied to NON-floor nodes only.
       K = number of top topic-central nodes EXEMPT from decay (the floor). K=0 => gen-317."""
    rng=random.Random(seedval)
    floor=set(CENT_ORDER[:K])          # protected anchor set
    indeg=collections.Counter({ID(p):0.0 for p in POSTS})
    for p in POSTS:
        for key in ("edges","refs","references"):
            for tgt in (p.get(key) or []):
                if isinstance(tgt,str): indeg[tgt]+=1.0
    authors=[p.get("author",{}).get("agent_id") for p in POSTS]; authors=[a for a in authors if a]
    node_order=[ID(p) for p in POSTS]
    top_series=[]; nonfloor_top_series=[]; anchor_king=0
    for r in range(rounds):
        seed=rng.choice(POSTS); draft_tags=seed.get("tags") or []; me=rng.choice(authors)
        cand=[]
        for q in POSTS:
            if q.get("author",{}).get("agent_id")==me: continue
            s=sim(draft_tags,q.get("tags"))
            if s>=sim_th: cand.append((s,ID(q)))
        if len(cand)>=2:
            cand.sort(key=lambda x:(indeg[x[1]], -x[0]))   # pure inverse pricing
            for _,cid in cand[:k]: indeg[cid]+=1.0
        # STRUCTURED HONEST DECAY: erode every node EXCEPT the protected floor
        if delta>0:
            for n in indeg:
                if n not in floor: indeg[n]*=(1.0-delta)
        # overall throne (random tie-break within eps)
        mx=max(indeg.values())
        tied=[n for n in node_order if mx-indeg[n]<1e-9]
        top=rng.choice(tied); top_series.append(top)
        if top in floor: anchor_king+=1
        # sub-throne among NON-floor nodes only
        nf_vals=[(indeg[n],n) for n in node_order if n not in floor]
        nfmx=max(v for v,_ in nf_vals)
        nf_tied=[n for v,n in nf_vals if nfmx-v<1e-9]
        nonfloor_top_series.append(rng.choice(nf_tied))
    tc=collections.Counter(top_series); dom_top,dom_ten=tc.most_common(1)[0]
    ntc=collections.Counter(nonfloor_top_series); _,ndom_ten=ntc.most_common(1)[0]
    vals=list(indeg.values()); mean_deg=sum(vals)/len(vals)
    floor_vals=[indeg[n] for n in floor] if floor else [0.0]
    nonfloor_vals=[indeg[n] for n in node_order if n not in floor]
    return {
        "delta":delta,"K":K,
        "gini":round(gini(vals),3),
        "anchor_king_frac":round(anchor_king/rounds,3),
        "floor_max_indeg":round(max(floor_vals),1),
        "nonfloor_max_indeg":round(max(nonfloor_vals),1),
        "overall_tenure_frac":round(dom_ten/rounds,3),
        "overall_distinct_rank1":len(tc),
        "leader_cent_rank":CENT_RANK.get(dom_top),
        "nonfloor_tenure_frac":round(ndom_ten/rounds,3),
        "nonfloor_distinct_rank1":len(ntc),
    }

def avg(delta,K,seeds,rounds=400):
    rs=[run(delta,K,sd,rounds) for sd in seeds]
    g=lambda key:[r[key] for r in rs if r[key] is not None]
    m=lambda key:round(sum(g(key))/len(g(key)),3)
    return {"delta":delta,"K":K,"gini":m("gini"),"anchor_king_frac":m("anchor_king_frac"),
            "floor_max_indeg":m("floor_max_indeg"),"nonfloor_max_indeg":m("nonfloor_max_indeg"),
            "overall_tenure_frac":m("overall_tenure_frac"),"overall_distinct_rank1":m("overall_distinct_rank1"),
            "leader_cent_rank":m("leader_cent_rank"),
            "nonfloor_tenure_frac":m("nonfloor_tenure_frac"),"nonfloor_distinct_rank1":m("nonfloor_distinct_rank1")}

SEEDS=(1,7,13,29,42,101)
print(f"corpus N={N}  hub-excluded={len(HUB)}  seeds={SEEDS}")
print(f"anchor set (top topic-central): {CENT_ORDER[:5]} ...")
print("STRUCTURED leak: indeg*=(1-delta) for all EXCEPT top-K central (floor). K=0 == gen-317 scalar.")
print("Testing: can a pinned anchor coexist with a rotating non-floor mass? (H-work vs F-i freeze vs F-ii null)")
print()
print("=== delta=0.03 (gen-317 ROTATING regime), K sweep, avg over 6 seeds ===")
for K in (0,1,3,5,10):
    print(json.dumps(avg(0.03,K,SEEDS)))
print()
print("=== cross-check delta=0.02 and 0.05 at K=3 ===")
for d in (0.02,0.05):
    print(json.dumps(avg(d,3,SEEDS)))
print()
print("=== per-seed detail seed=42 (gen-314 anchor seed), delta=0.03 ===")
for K in (0,1,3,5):
    print(json.dumps(run(0.03,K,42)))
