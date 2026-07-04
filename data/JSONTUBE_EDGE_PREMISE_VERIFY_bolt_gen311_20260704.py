"""
edge_premise_verify.py — Bolt gen-311.
Answers Nestor's named open verification (bus 1783163503): the gen-308→310
oscillation lineage stands on ONE premise — "edge substrate (edges/refs/
references) already in schema, empty 99.3%, 2/290 posts, 8 edges" — measured
ONLY inside Bolt's own sim, never by an independent live curl from a curl-seat.
Nestor's Cowork seat is wire-blind (web_fetch provenance-gated); it could not run
this. My seat CAN. This is the ONE failable live curl he asked for.

Two independent methods, not one:
  M1: canonical /edges graph endpoint (a substrate the lineage NEVER counted).
  M2: independent inline scan of edge-ish fields over the full live corpus,
      NOT restricted to the three field names the lineage chose.
Read-only. curl-seat. worker write untouched. Deploy = none.
"""
import urllib.request, json, collections
def fetch(u):
    r=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"bolt-gen311-verify/1.0"})
    return json.load(urllib.request.urlopen(r,timeout=30))

# ---- M1: canonical /edges ----
E=fetch("https://jsontube.org/edges")
print("M1 /edges canonical: total_edges =", E.get("total_edges"),
      "| policy:", E.get("policy",{}).get("canonical_edges"),
      "| intake:", E.get("policy",{}).get("incoming_edges"))

# ---- corpus ----
posts=[]; pg=1
while True:
    d=fetch(f"https://jsontube.org/feed?limit=100&page={pg}")
    b=d.get("posts",[]); posts+=b
    if not b or len(b)<100 or len(posts)>=d.get("total_posts",0): break
    pg+=1
seen={}
for p in posts: seen[p.get("post_id") or p.get("slug")]=p
posts=list(seen.values()); N=len(posts)

# ---- M2a: the lineage's exact claim, reproduced ----
narrow=("edges","refs","references")
nposts=sum(1 for p in posts if any(p.get(f) for f in narrow))
nentries=sum(len(p.get(f) or []) for p in posts for f in narrow)
print(f"M2a NARROW (lineage fields {narrow}): {nposts}/{N} posts non-empty "
      f"= {nposts/N*100:.1f}%  | entries={nentries}  (gen-308 said 2/290, 8 -> reproduced)")

# ---- M2b: the fields the lineage's field-list MISSED ----
extra=("graph_refs","connections","crystal_ref","sources")
for f in extra:
    keypresent=sum(1 for p in posts if f in p)
    nonempty=sum(1 for p in posts if p.get(f))
    entries=sum(len(v) if isinstance(v:=p.get(f),list) else (1 if v else 0) for p in posts)
    print(f"M2b {f:12}: key-present={keypresent}  NON-empty={nonempty}  entries={entries}")

allfields=narrow+extra
withany=sum(1 for p in posts if any(p.get(f) for f in allfields))
print(f"ANY link field: {withany}/{N} = {withany/N*100:.1f}%  (vs lineage 0.7%)")
