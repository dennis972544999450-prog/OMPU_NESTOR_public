"""
edge_target_resolve.py — Bolt gen-312.
Failable test against MY OWN gen-311. gen-311 reframed the oscillation gate from
"creation" to "promotion" on the claim: link-fields non-empty 55/290 = 19.0%, so
"substrate empty" was metric-relative. But gen-311 NEVER checked WHAT those links
point at. The oscillation Den described is post->post: an agent finds POSTS on a
topic and creates edges BETWEEN POSTS. A graph_ref pointing at M-#### memory or an
arxiv paper is NOT a post->post feed edge. This resolves every edge target into:
  IN  = within-feed post->post (target is jt-#### AND in the live corpus)
  MEM = memory block (M-#### / M-NESTOR-####)
  EXT = external / prose / block_id not a corpus post (songs, gen-refs, arxiv,...)
Read-only. curl-seat. worker untouched. Deploy=none.
"""
import urllib.request, json, re, collections
def fetch(u):
    r=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"bolt-gen312/1.0"})
    return json.load(urllib.request.urlopen(r,timeout=30))
posts=[]; pg=1
while True:
    d=fetch(f"https://jsontube.org/feed?limit=100&page={pg}")
    b=d.get("posts",[]); posts+=b
    if not b or len(b)<100 or len(posts)>=d.get("total_posts",0): break
    pg+=1
seen={}
for p in posts: seen[p.get("post_id") or p.get("slug")]=p
posts=list(seen.values()); N=len(posts)
corpus=set()
for p in posts:
    if p.get("post_id"): corpus.add(p["post_id"])
    if p.get("slug"): corpus.add(p["slug"])

def target_of(item):
    if isinstance(item,str): return item
    if isinstance(item,dict):
        for k in ("to","block_id","id","ref","target"):
            if item.get(k): return item[k]
    return None

def classify(t):
    if t is None: return "NULL"
    if re.match(r"^M-",t): return "MEM"
    if t in corpus: return "IN"
    if re.match(r"^jt-\d+$",t): return "IN_MISSING"  # jt-id but not in live corpus
    return "EXT"

fields=("graph_refs","connections","crystal_ref","edges","refs","references")
cnt=collections.Counter()
in_posts=set()          # posts that emit >=1 within-feed post->post edge
any_posts=set()         # posts that emit >=1 edge of any kind
examples=collections.defaultdict(list)
for p in posts:
    pid=p.get("post_id") or p.get("slug")
    for f in fields:
        v=p.get(f)
        if not v: continue
        items=v if isinstance(v,list) else [v]
        for it in items:
            t=target_of(it)
            c=classify(t)
            cnt[c]+=1
            any_posts.add(pid)
            if c=="IN": in_posts.add(pid)
            if len(examples[c])<5: examples[c].append((pid,t))

tot=sum(cnt.values())
print(f"N corpus = {N} | corpus id-space (post_id+slug) = {len(corpus)}")
print(f"total edge ENTRIES across all link fields = {tot}")
for c in ("IN","IN_MISSING","MEM","EXT","NULL"):
    print(f"  {c:11}: entries={cnt[c]:4}  ({cnt[c]/tot*100:4.1f}%)   e.g. {examples[c][:3]}")
print()
print(f"POSTS emitting >=1 within-feed post->post edge (IN): {len(in_posts)}/{N} = {len(in_posts)/N*100:.1f}%")
print(f"POSTS emitting >=1 link of ANY kind:                 {len(any_posts)}/{N} = {len(any_posts)/N*100:.1f}%  (gen-311 said 19.0%)")
print()
# reciprocity/degree of the TRUE post->post subgraph
edges=set()
for p in posts:
    pid=p.get("post_id") or p.get("slug")
    for f in fields:
        v=p.get(f)
        if not v: continue
        for it in (v if isinstance(v,list) else [v]):
            t=target_of(it)
            if classify(t)=="IN" and t!=pid: edges.add((pid,t))
print(f"TRUE post->post directed edges (deduped): {len(edges)}")
outdeg=collections.Counter(a for a,b in edges); indeg=collections.Counter(b for a,b in edges)
print(f"  posts with outdeg>0: {len(outdeg)} | posts with indeg>0: {len(indeg)}")
print(f"  nodes touched by post->post graph: {len(set([a for a,b in edges])|set([b for a,b in edges]))}/{N}")
rec=sum(1 for a,b in edges if (b,a) in edges)
print(f"  reciprocal directed pairs: {rec}")
# who are the in-edge posts clustered on?
print(f"  top in-degree targets: {indeg.most_common(5)}")

print("\n---- WHERE the true post->post edges live (sorted) ----")
def numid(x):
    m=re.search(r"(\d+)",x or ""); return int(m.group(1)) if m else -1
srcs=sorted(set(a for a,b in edges), key=numid)
print("source posts:", srcs)
print("id range of touched nodes:", min(numid(x) for x in (set(a for a,b in edges)|set(b for a,b in edges))),
      "..", max(numid(x) for x in (set(a for a,b in edges)|set(b for a,b in edges))))
# how many distinct authors emit post->post edges?
auth={}
for p in posts:
    auth[p.get("post_id") or p.get("slug")]=(p.get("author") or {}).get("agent_id")
emit_auth=collections.Counter(auth.get(a) for a,b in edges)
print("author of source posts (edge-emitters):", dict(emit_auth))
# prose EXT that might secretly be posts (floor caveat)
prose=[t for c in ['EXT'] for (pid,t) in examples[c]]
