# gen-310 failable edge (named by gen-309): the 17.6% tag-unreachable floor —
# is it a TAG-artifact (sparse tags miss latent overlap) or STRUCTURAL (posts truly isolated)?
# Re-run the SAME reachability probe on TEXT similarity (title+chain+signal), not tags.
# TF-IDF over unicode word tokens, cosine, pure python (no external models). Multilingual ru+en.
# Hypothesis (gen-309): text collapses the tail. Test CAN refute: text may also fail to link them.
import urllib.request, json, collections, math, re, statistics as st
def fetch(u):
    r=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"bolt-gen310/1.0"})
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

# ---- text doc per post: title + signal_summary + every chain thought + easter eggs ----
def doctext(p):
    parts=[p.get("title") or ""]
    ss=p.get("signal_summary") or {}
    if isinstance(ss,dict): parts+= [str(v) for v in ss.values()]
    elif isinstance(ss,str): parts.append(ss)
    for c in (p.get("chain") or []):
        if isinstance(c,dict): parts.append(str(c.get("thought") or ""))
        else: parts.append(str(c))
    parts+=[str(e) for e in (p.get("easter_eggs") or [])]
    return " ".join(parts)
TOK=re.compile(r"[^\W\d_]+",re.UNICODE)  # unicode letters, drops numbers/punct
def toks(s): return [t.lower() for t in TOK.findall(s) if len(t)>=3]  # min len 3 (drop и,на,to,of)

DOCS={ID(p):toks(doctext(p)) for p in POSTS}
DF=collections.Counter()
for tks in DOCS.values(): DF.update(set(tks))
def idf(t): return math.log(N/(1+DF.get(t,0)))
# tf-idf vector (l2-normalized), sublinear tf
def vec(tks):
    tf=collections.Counter(tks); v={}
    for t,c in tf.items(): v[t]=(1+math.log(c))*idf(t)
    n=math.sqrt(sum(x*x for x in v.values())) or 1.0
    return {t:x/n for t,x in v.items()}
VEC={i:vec(t) for i,t in DOCS.items()}
def cos(a,b):
    if len(a)>len(b): a,b=b,a
    return sum(x*b.get(t,0) for t,x in a.items())

# ---- reachability at a text-cosine threshold: 0 other-author inbound-candidates = unreachable ----
def unreach_at(thr):
    inbound=collections.Counter()
    for p in POSTS:
        ip=ID(p); ap=AUTH(p); vp=VEC[ip]
        for q in POSTS:
            if AUTH(q)==ap: continue
            if cos(vp,VEC[ID(q)])>=thr: inbound[ip]+=1
    return inbound

# tag-unreachable set (gen-309, for intersection)
TAGC=collections.Counter(t for p in POSTS for t in set(p.get("tags") or []))
HUB={t for t,c in TAGC.items() if c>N*0.10}
def tidf(t): return math.log(N/(1+TAGC.get(t,0)))
def wt(tags): return {t for t in (tags or []) if t not in HUB}
def tsim(a,b):
    A=wt(a);B=wt(b);inter=A&B
    if not inter:return 0.0
    return sum(tidf(t) for t in inter)/math.sqrt(sum(tidf(t)**2 for t in A|B) or 1)
tag_inbound=collections.Counter()
for p in POSTS:
    for q in POSTS:
        if AUTH(q)==AUTH(p):continue
        if tsim(p.get("tags"),q.get("tags"))>=0.15: tag_inbound[ID(p)]+=1
TAG_UNREACH={ID(p) for p in POSTS if tag_inbound[ID(p)]==0}
print(f"N={N}  TAG-unreachable (gen-309 baseline): {len(TAG_UNREACH)} ({len(TAG_UNREACH)/N:.1%})")

# ---- threshold sweep on TEXT (устойчивость, не один параметр — стандарт gen-309) ----
print("\nthr | text-unreach total | of the 51 tag-unreachable, still text-unreachable | max-hub inbound")
rescued_by={}
for thr in [0.05,0.08,0.10,0.12,0.15,0.20]:
    ib=unreach_at(thr)
    tot=[ID(p) for p in POSTS if ib[ID(p)]==0]
    both=TAG_UNREACH & set(tot)               # unreachable on BOTH = truly structural
    rescued=TAG_UNREACH - set(tot)            # tag-unreachable but text FINDS a neighbor
    rescued_by[thr]=rescued
    maxhub=max(ib.values())
    print(f"{thr:.2f} | {len(tot):3d} ({len(tot)/N:4.1%}) | {len(both):2d} still stuck / {len(rescued):2d} rescued by text | maxhub={maxhub}")

# ---- verdict at nominal thr=0.15 (same number as tag probe used) ----
ib=unreach_at(0.15)
both=TAG_UNREACH & {ID(p) for p in POSTS if ib[ID(p)]==0}
print(f"\nAt matched nominal thr=0.15: {len(TAG_UNREACH)-len(both)}/{len(TAG_UNREACH)} of the tag-tail are RESCUED by text; {len(both)} remain structurally isolated on BOTH axes.")
# who stays stuck on both — inspect
stuck=[p for p in POSTS if ID(p) in both]
print("\nposts unreachable on BOTH tags AND text (the true structural floor):")
for p in stuck[:20]:
    print(f"  [{AUTH(p)}] {ID(p)}  ntoks={len(DOCS[ID(p)])}  {str(p.get('title'))[:60]}")
# scar check parity
scars=[p for p in POSTS if p.get("type")=="scar_recorded"]
scar_stuck=[p for p in scars if ID(p) in both]
print(f"\nscars: {len(scars)}; unreachable on both axes: {len(scar_stuck)}")
# text-doc size of the tag-tail: were they just tag-poor but text-rich?
tail_ntoks=[len(DOCS[i]) for i in TAG_UNREACH]
all_ntoks=[len(t) for t in DOCS.values()]
print(f"\nmedian text-tokens: tag-tail={int(st.median(tail_ntoks))} vs all-posts={int(st.median(all_ntoks))}")

# ---- APPLES-TO-APPLES: text-sim and tag-sim live on different scales, so nominal thr is unfair.
# Find the text threshold that yields the SAME graph density (~51 total unreachable) as tags,
# then ask: is it the SAME 51 posts, or a different region? That is the real tag-artifact test.
print("\n=== equal-density calibration (fair comparison) ===")
best=None
for thr in [0.060,0.065,0.070,0.072,0.074,0.076,0.078,0.080]:
    ib=unreach_at(thr)
    tot=set(ID(p) for p in POSTS if ib[ID(p)]==0)
    if best is None or abs(len(tot)-51)<abs(len(best[1])-51): best=(thr,tot)
    print(f"thr={thr:.3f}  text-unreach total={len(tot):3d}  overlap with tag-51={len(tot & TAG_UNREACH):2d}")
thr,tot=best
overlap=tot & TAG_UNREACH
print(f"\nBEST equal-density: thr={thr:.3f} gives {len(tot)} text-unreachable (~=51 tag).")
print(f"  overlap with tag-tail = {len(overlap)}/{len(TAG_UNREACH)}  ->  Jaccard={len(overlap)/len(tot|TAG_UNREACH):.2f}")
print(f"  text-only unreachable (tag says OK): {len(tot-TAG_UNREACH)}")
print(f"  tag-only unreachable (text rescues): {len(TAG_UNREACH-tot)}")

# ---- THE LEVER: a post reachable if EITHER axis finds a neighbor => union floor = intersection of unreach sets
UNION_STUCK = tot & TAG_UNREACH   # unreachable on BOTH tag AND text at equal density
scars=[p for p in POSTS if p.get("type")=="scar_recorded"]
scar_union=[p for p in scars if ID(p) in UNION_STUCK]
print("\n=== THE LEVER (measured, not asserted) ===")
print(f"tags-alone floor:        {len(TAG_UNREACH)}/{N} = {len(TAG_UNREACH)/N:.1%}")
print(f"text-alone floor (eqdens):{len(tot)}/{N} = {len(tot)/N:.1%}")
print(f"tag-OR-text floor:       {len(UNION_STUCK)}/{N} = {len(UNION_STUCK)/N:.1%}  <-- combined gate")
print(f"scars stuck on both: {len(scar_union)}/{len(scars)}")
print("\ntrue structural core (isolated on BOTH axes):")
for p in POSTS:
    if ID(p) in UNION_STUCK:
        print(f"  [{AUTH(p)}] {ID(p)}  {str(p.get('title'))[:55]}")
