#!/usr/bin/env python3
"""gen-621 divergent verify: fixed dead-seat literals in EXECUTABLE string constants.
Grammar: tokenize (token-level: trailing comments are NOT code-blindness, 620 law),
STRING tokens only, excluding docstrings (first stmt strings), excluding wildcard
'/sessions/*'. Flags fixed '/sessions/<literal-name>/'. Self-exclude. Read-only."""
import io, os, re, sys, glob, json, tokenize

FIXED = re.compile(r"/sessions/(?!\*)[A-Za-z0-9_-]+/")
SELF = os.path.abspath(__file__)

def docstring_positions(src):
    # crude: collect (row) of module/def/class leading strings via ast
    import ast
    pos=set()
    try: tree=ast.parse(src)
    except SyntaxError: return pos, False
    for node in ast.walk(tree):
        # ANY bare string-expression statement is inert prose (docstring or no-op),
        # not only the first statement of a body — gen-621 smoke scar
        if isinstance(node, ast.Expr) and isinstance(getattr(node,'value',None), ast.Constant) and isinstance(node.value.value,str):
            for r in range(node.lineno, node.end_lineno+1): pos.add(r)
    return pos, True

def scan(path):
    hits=[]
    try: src=open(path,encoding='utf-8',errors='replace').read()
    except OSError: return hits
    docs,parsed = docstring_positions(src)
    try: toks=list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception: return hits
    for t in toks:
        if t.type==tokenize.STRING and t.start[0] not in docs:
            if FIXED.search(t.string):
                hits.append((t.start[0], t.string[:90]))
    return hits

def smoke():
    liar="/tmp/known_liar_gen621.py"
    open(liar,'w').write(
        'import json\n'
        'P="/sessions/dead-seat-liar/mnt/x.json"  # trailing comment must not hide me\n'
        '# comment only: /sessions/dead-seat-liar/mnt/y.json\n'
        '"""docstring: /sessions/dead-seat-liar/mnt/z.json"""\n'
        'W="/sessions/*/mnt/glob_ok.json"\n')
    h=scan(liar)
    ok = len(h)==1 and h[0][0]==2
    print(f"SMOKE: hits={h} -> {'EATEN' if ok else 'BLIND — ABORT'}")
    return ok

if __name__=='__main__':
    if not smoke(): sys.exit(2)
    root=sys.argv[1]
    report={}
    for p in sorted(glob.glob(os.path.join(root,'**','*.py'), recursive=True)):
        if os.path.abspath(p)==SELF or '__pycache__' in p or 'node_modules' in p: continue
        h=scan(p)
        if h: report[os.path.relpath(p,root)]=h
    n=sum(len(v) for v in report.values())
    print(json.dumps({"root":root,"files":len(report),"hits":n,
        "detail":{k:[list(x) for x in v] for k,v in report.items()}}, ensure_ascii=False, indent=1)[:4000])
