#!/usr/bin/env python3
"""probe gen-618: test-docstring-vs-assertion census. READ-ONLY.
Stage-1 naive: identifier-like token in test-function docstring absent from executable body text.
Also: vacuous-pass detector (no Assert node, no assert*-call, no pytest.raises).
md5 snapshot of corpus pre==post asserted. Portable via OMPU_SHARED/OMPU_HM env."""
import ast, hashlib, json, os, re, sys, glob

S  = os.environ.get("OMPU_SHARED") or glob.glob("/sessions/*/mnt/OMPU_shared")[0]
HM = os.environ.get("OMPU_HM") or glob.glob("/sessions/*/mnt/OMPU_Housemaster")[0]
SELF = os.path.abspath(__file__)

def corpus():
    fs=[]
    for root in (S, os.path.join(HM,"memory")):
        for dp,dn,fn in os.walk(root):
            if ".git" in dp or "node_modules" in dp: continue
            for f in fn:
                if f.startswith("test_") and f.endswith(".py"):
                    p=os.path.join(dp,f)
                    if os.path.abspath(p)!=SELF: fs.append(p)
    return sorted(fs)

def md5corpus(fs):
    h=hashlib.md5()
    for p in fs:
        h.update(open(p,"rb").read())
    return h.hexdigest()

IDTOK = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
def referents(doc):
    out=set()
    for t in IDTOK.findall(doc):
        if ("_" in t and len(t)>=6) or t.endswith(".py") or t.endswith("py"):
            if "_" in t and len(t)>=6: out.add(t)
    for m in re.findall(r"[A-Za-z0-9_./]+\.py", doc): out.add(m)
    return out

STOP = set()  # filled after first pass with hyper-common tokens? no — keep naive, stage-2 is manual

def body_text(fn_node, src_lines):
    # executable body text excluding the docstring
    segs=[]
    body=fn_node.body
    start_idx=0
    if body and isinstance(body[0],ast.Expr) and isinstance(getattr(body[0],'value',None),ast.Constant) and isinstance(body[0].value.value,str):
        start_idx=1
    for n in body[start_idx:]:
        segs.append(ast.get_source_segment("\n".join(src_lines), n) or "")
    return "\n".join(segs)

def has_assertion(fn_node):
    for n in ast.walk(fn_node):
        if isinstance(n,ast.Assert): return True
        if isinstance(n,ast.Call):
            f=n.func
            name = f.attr if isinstance(f,ast.Attribute) else (f.id if isinstance(f,ast.Name) else "")
            if name.startswith("assert") or name in ("raises","fail","check"): return True
        if isinstance(n,ast.Raise): return True
    return False

fs=corpus()
pre=md5corpus(fs)
report={"files":len(fs),"funcs":0,"fired":[],"vacuous":[],"parse_errors":[]}
for p in fs:
    try:
        src=open(p,encoding="utf-8",errors="replace").read()
        tree=ast.parse(src)
    except Exception as e:
        report["parse_errors"].append([p,str(e)]); continue
    src_lines=src.split("\n")
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test"):
            report["funcs"]+=1
            doc=ast.get_docstring(node) or ""
            bt = body_text(node, src_lines)
            missing=sorted(t for t in referents(doc) if t not in bt and t not in node.name)
            if missing and doc:
                report["fired"].append({"file":p.replace(S,"$S").replace(HM,"$HM"),"func":node.name,"missing":missing,"doc":doc[:200]})
            if not has_assertion(node):
                report["vacuous"].append({"file":p.replace(S,"$S").replace(HM,"$HM"),"func":node.name})
    # module docstring vs whole module? out of scope this pass
post=md5corpus(fs)
assert pre==post, "CORPUS MUTATED"
report["md5_corpus"]=pre
out=os.path.join(os.path.dirname(SELF),"test_prose_vs_assert_report_gen618.json")
json.dump(report,open(out,"w"),ensure_ascii=False,indent=1)
print(json.dumps({"files":report["files"],"funcs":report["funcs"],"fired":len(report["fired"]),"vacuous":len(report["vacuous"]),"parse_errors":len(report["parse_errors"]),"md5":pre},indent=1))
