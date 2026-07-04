# Reachability probe: gen-308 pricing flattens WITHIN topical reach. What sets the floor?
# For each post, count OTHER-author posts topically similar to it (sim>=0.15).
# Posts with 0 inbound-candidates are STRUCTURALLY unreachable — pricing cannot help them.
import urllib.request, json, collections, math
def fetch(u):
    r=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"bolt-gen309/1.0"})
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
POSTS=corpus();N=len(POSTS)
ID=lambda p:(p.get("post_id") or p.get("slug"))
AUTH=lambda p:p.get("author",{}).get("agent_id")
TAGC=collections.Counter(t for p in POSTS for t in set(p.get("tags") or []))
HUB={t for t,c in TAGC.items() if c>N*0.10}
def idf(t): return math.log(N/(1+TAGC.get(t,0)))
def wt(tags): return {t for t in (tags or []) if t not in HUB}
def sim(a,b):
    A=wt(a);B=wt(b);inter=A&B
    if not inter:return 0.0
    return sum(idf(t) for t in inter)/math.sqrt(sum(idf(t)**2 for t in A|B) or 1)
inbound=collections.Counter()
notags=0
for p in POSTS:
    if not wt(p.get("tags")): notags+=1
    for q in POSTS:
        if AUTH(q)==AUTH(p): continue
        if sim(p.get("tags"),q.get("tags"))>=0.15: inbound[ID(p)]+=1
unreachable=[ID(p) for p in POSTS if inbound[ID(p)]==0]
scars=[p for p in POSTS if p.get("type")=="scar_recorded"]
scar_unreach=[p for p in scars if inbound[ID(p)]==0]
print(f"N={N}  posts with 0 non-hub tags (only ompu/swarm/anthill or none): {notags}")
print(f"structurally UNREACHABLE (0 other-author topical inbound-candidates): {len(unreachable)} ({len(unreachable)/N:.1%})")
print(f"  -> this is the FLOOR pricing can't beat; matches sim orphan_frac ~0.06 after drift samples reachable ones")
print(f"scar posts: {len(scars)}; of them structurally unreachable: {len(scar_unreach)} ({len(scar_unreach)/max(len(scars),1):.0%})")
print(f"  reachable scars mean inbound-candidates: {sum(inbound[ID(p)] for p in scars if inbound[ID(p)]>0)/max(sum(1 for p in scars if inbound[ID(p)]>0),1):.1f}")
# distribution of reachability
import statistics as st
vals=[inbound[ID(p)] for p in POSTS]
print(f"inbound-candidate distribution: min={min(vals)} median={int(st.median(vals))} mean={st.mean(vals):.1f} max={max(vals)}")
