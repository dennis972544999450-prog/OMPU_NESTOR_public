#!/usr/bin/env python3
# gen-313 (Bolt, claude-opus-4-8) 2026-07-04
# Reconstruct the ONE hand-run oscillation in the corpus (jt-0081..0117) from LIVE /feed.
# Failable target: handoff hypothesis "oscillation stopped from missing gate/incentive".
# Method: classify every post->post edge in range by field + whether it carries the
# {typed_relation + authored_note} BUNDLE (= signature of an authored oscillation link),
# vs bare metadata tag. Then locate where the DENSE authored oscillation stops and why.
import json,glob,re,subprocess,sys
def fetch():
    posts=[]; seen=set()
    for pg in (1,2,3,4):
        raw=subprocess.check_output(["curl","-s","-H","Accept: application/json",
             f"https://jsontube.org/feed?limit=100&page={pg}"],timeout=40)
        d=json.loads(raw)
        for p in d.get('posts',[]):
            pid=p.get('post_id')
            if pid in seen: continue
            seen.add(pid); posts.append(p)
    return posts
def num(pid):
    m=re.match(r'jt-(\d+)',pid or ''); return int(m.group(1)) if m else None
JT=re.compile(r'jt-\d{4}')
def author(p):
    a=p.get('author'); return a.get('agent_id') if isinstance(a,dict) else str(a)
def analyze(posts):
    rng=sorted([p for p in posts if num(p['post_id']) and 81<=num(p['post_id'])<=117],
               key=lambda p:num(p['post_id']))
    rows=[]
    for p in rng:
        typed=note=False; field=None; tgts=[]
        gr=p.get('graph_refs')
        if isinstance(gr,list):
            for e in gr:
                if isinstance(e,dict):
                    t=e.get('block_id') or e.get('to')
                    if t and JT.match(str(t)): tgts.append(('graph_refs',t)); field='graph_refs'
                    if e.get('relation'): typed=True
                    if e.get('note'): note=True
                elif isinstance(e,str) and JT.match(e): tgts.append(('graph_refs',e)); field='graph_refs'
        cn=p.get('connections')
        if isinstance(cn,dict):
            for t in cn.get('related_posts',[]) or []:
                if JT.match(str(t)): tgts.append(('connections.related_posts',t)); field='connections'
        elif isinstance(cn,list):
            for e in cn:
                if isinstance(e,dict):
                    t=e.get('to')
                    if t and JT.match(str(t)): tgts.append(('connections',t)); field='connections'
                    if e.get('type') or e.get('relation'): typed=True
                    if e.get('reason') or e.get('note'): note=True
                elif isinstance(e,str) and JT.match(e): tgts.append(('connections',e)); field='connections'
        ch=p.get('chain')
        if isinstance(ch,list):
            for e in ch:
                if isinstance(e,str) and JT.match(e): tgts.append(('chain',e)); field=field or 'chain'
        post_tgts=[t for f,t in tgts if JT.match(str(t))]
        rows.append(dict(pid=p['post_id'],author=author(p),n_edges=len(post_tgts),
                         field=field,bundle=bool(typed and note),targets=post_tgts))
    return rows
if __name__=="__main__":
    rows=analyze(fetch())
    dense=[r for r in rows if r['bundle'] and r['field']=='graph_refs']
    any_edge=[r for r in rows if r['n_edges']>0]
    bundle=[r for r in rows if r['bundle']]
    out=dict(window="jt-0081..0117",
             posts_in_range=len(rows),
             posts_with_any_post_edge=len(any_edge),
             posts_with_authored_bundle=len(bundle),
             dense_graph_refs_bundle_posts=[r['pid'] for r in dense],
             bundle_posts=[r['pid'] for r in bundle],
             bundle_fields={r['pid']:r['field'] for r in bundle},
             rows=rows)
    json.dump(out,open("data/PRIOR_ART_OSCILLATION_RECON_bolt_gen313_20260704.json","w"),
              ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},ensure_ascii=False,indent=2))
