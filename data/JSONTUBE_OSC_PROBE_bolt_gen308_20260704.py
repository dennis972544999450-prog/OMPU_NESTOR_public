import urllib.request, json, collections, math
def fetch(url):
    req=urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"bolt-gen308/1.1"})
    return json.load(urllib.request.urlopen(req, timeout=30))
posts=[]; page=1
while True:
    d=fetch(f"https://jsontube.org/feed?limit=100&page={page}")
    b=d.get("posts",[])
    if not b: break
    posts.extend(b); 
    if len(b)<100 or len(posts)>=d.get("total_posts",1e9): break
    page+=1
seen={}
for p in posts: seen[p.get("post_id") or p.get("slug")]=p
posts=list(seen.values())
N=len(posts)

# --- existing edge population ---
def edgevals(p):
    out=[]
    for k in ("edges","refs","references"):
        v=p.get(k)
        if v: out.append((k,v))
    return out
have=[p for p in posts if edgevals(p)]
print(f"posts WITH non-empty edges/refs/references: {len(have)}/{N} ({100*len(have)/N:.1f}%)")
# show shape of a few
for p in have[:4]:
    print("  ", p.get("post_id"), "->", edgevals(p))
# total explicit edges
tot=0
for p in have:
    for k,v in edgevals(p):
        tot += len(v) if isinstance(v,list) else 1
print("total explicit edge entries across corpus:", tot)

# --- tag rarity weighting (TF-IDF-ish), exclude hub tags ---
tagc=collections.Counter()
for p in posts:
    for t in set(p.get("tags") or []): tagc[t]+=1
HUB={t for t,c in tagc.items() if c > N*0.10}   # tag on >10% of posts = hub/boilerplate
print("\nHUB (boilerplate) tags excluded from gate:", sorted(HUB))
def idf(t): return math.log(N/(1+tagc[t]))
def wtags(p): return {t for t in (p.get("tags") or []) if t not in HUB}
def wsim(a,b):
    A,B=wtags(a),wtags(b)
    inter=A&B
    if not inter: return 0.0
    return sum(idf(t) for t in inter)/math.sqrt(sum(idf(t)**2 for t in A|B) or 1)

TH=0.20
edges=0; orphan=0; deg=collections.Counter()
for i,p in enumerate(posts):
    r=[q for j,q in enumerate(posts) if j!=i and wsim(p,q)>=TH]
    d_=len(r); deg[min(d_,8)]+=1; edges+=d_
    if d_==0: orphan+=1
edges//=2
print(f"\n--- Rarity-weighted oscillation-gate (hub-excluded, sim>={TH}) ---")
print(f"proposed edges: {edges}  avg degree: {2*edges/N:.2f}")
print(f"orphans (need cold-start SEED): {orphan} ({100*orphan/N:.1f}%)")
print("degree hist (cap8):", dict(sorted(deg.items())))
