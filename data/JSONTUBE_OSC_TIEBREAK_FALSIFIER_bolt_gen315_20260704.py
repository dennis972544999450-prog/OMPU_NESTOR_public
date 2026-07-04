"""
osc_tiebreak_falsifier.py — Bolt gen-315.
DETECTOR ON MYSELF. gen-314 claimed: under inverse pricing, degree-Gini stays
flat (0.24-0.29) BUT one topic-central node holds rank-1 for MAJORITY of rounds
(tenure 0.52-0.96) => "anti-PA flattens mass, not leadership."

T2 CONFOUND (named in my own gen-314 handoff): the tenure metric uses
    top = max(indeg, key=lambda n: indeg[n])
Python's max returns the FIRST key on a tie, and indeg was built as
    Counter({ID(p):0 for p in POSTS})
so its iteration order == corpus (feed) insertion order. Under a FLAT field many
nodes share the same max in-degree each round. If so, "tenure" may be counting
not leadership but the tie-break bias of dict order — the corpus-first node among
the tied set wins rank-1 deterministically every round.

FALSIFIER (this can DESTROY gen-314):
 (a) each round, count how many nodes SHARE the max in-degree (tie width).
     If typically 1 -> leader is real. If typically >>1 -> gen-314 leader is a ghost.
 (b) re-run tenure under RANDOM tie-break (pick uniformly among the tied max nodes).
     If tenure 0.8 survives -> real leader. If it collapses toward 1/tie_width
     -> gen-314 measured dict-order artifact, not leadership.
 (c) control: also run tie-break = LAST-in-corpus, to show direction of the bias.
curl read-only. worker untouched. NOT deployed.
"""
import json, collections, math, random, subprocess

def fetch(u):
    out = subprocess.check_output(["curl","-s","-H","Accept: application/json","-A","bolt-gen315/1.0",u], timeout=40)
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

def run(tiebreak, seedval, rounds=400, k=3, sim_th=0.15):
    """tiebreak in {'first','random','last'} — how rank-1 is chosen among tied max."""
    rng=random.Random(seedval)
    indeg=collections.Counter({ID(p):0 for p in POSTS})
    for p in POSTS:
        for key in ("edges","refs","references"):
            for tgt in (p.get(key) or []):
                if isinstance(tgt,str): indeg[tgt]+=1
    authors=[p.get("author",{}).get("agent_id") for p in POSTS]; authors=[a for a in authors if a]
    node_order=[ID(p) for p in POSTS]            # corpus order (what max() uses)
    per_round_top=[]; tie_widths=[]
    for r in range(rounds):
        seed=rng.choice(POSTS); draft_tags=seed.get("tags") or []; me=rng.choice(authors)
        cand=[]
        for q in POSTS:
            if q.get("author",{}).get("agent_id")==me: continue
            s=sim(draft_tags,q.get("tags"))
            if s>=sim_th: cand.append((s,ID(q)))
        if len(cand)<2: continue
        # inverse pricing (gen-308 gate)
        cand.sort(key=lambda x:(indeg[x[1]], -x[0]))
        chosen=[cid for _,cid in cand[:k]]
        for cid in chosen: indeg[cid]+=1
        # ---- rank-1 selection among tied max in-degree ----
        mx=max(indeg.values())
        tied=[n for n in node_order if indeg[n]==mx]   # node_order = corpus order
        tie_widths.append(len(tied))
        if tiebreak=="first":    top=tied[0]                       # == gen-314 max() behavior
        elif tiebreak=="last":   top=tied[-1]
        elif tiebreak=="random": top=rng.choice(tied)
        per_round_top.append(top)
    tc=collections.Counter(per_round_top)
    dom_top,dom_ten=tc.most_common(1)[0]
    active=len(per_round_top)
    return {
        "tiebreak":tiebreak,
        "final_gini":round(gini(list(indeg.values())),3),
        "final_max_indeg":max(indeg.values()),
        "tenure_frac":round(dom_ten/active,3) if active else None,
        "distinct_rank1":len(tc),
        "median_tie_width":sorted(tie_widths)[len(tie_widths)//2] if tie_widths else None,
        "mean_tie_width":round(sum(tie_widths)/len(tie_widths),1) if tie_widths else None,
        "max_tie_width":max(tie_widths) if tie_widths else None,
        "active_rounds":active,
        "expected_tenure_if_pure_tiebreak_~1/width":round(1/(sum(tie_widths)/len(tie_widths)),3) if tie_widths else None,
    }

print(f"corpus N={N}  hub-excluded={len(HUB)}\n")
print("If median tie width >> 1 AND random-tiebreak tenure collapses toward 1/width,")
print("then gen-314's 'persistent leader' was a dict-order artifact, NOT leadership.\n")
print("=== single seed=42 (gen-314's seed), three tie-break rules ===")
for tb in ("first","random","last"):
    print(json.dumps(run(tb,42), ensure_ascii=False))
print("\n=== random tie-break across 5 seeds (does any real leader survive?) ===")
for sd in (1,7,13,29,101):
    print(f"seed={sd}: "+json.dumps(run("random",sd), ensure_ascii=False))
