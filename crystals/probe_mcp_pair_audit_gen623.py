#!/usr/bin/env python3
"""probe gen-623: MCP-pair audit. read-only. root-агностичен (пути аргументами)."""
import ast, sys, json, hashlib, tokenize, io

def md5(p):
    return hashlib.md5(open(p,'rb').read()).hexdigest()

def parse(p):
    src = open(p, encoding='utf-8', errors='replace').read()
    try:
        return ast.parse(src), src, None
    except SyntaxError as e:
        return None, src, f"SyntaxError L{e.lineno}"

def top_defs(tree):
    return sorted(n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))

def all_defs(tree):
    return sorted(n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)))

def env_dead_defaults(tree):
    """env-переменные с default-веткой, несущей host-литерал /Users/ (единица: env-имя)."""
    out=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Call):
            f=n.func
            name=None
            if isinstance(f,ast.Attribute) and f.attr in ('get','getenv'): name=f.attr
            elif isinstance(f,ast.Name) and f.id=='getenv': name='getenv'
            if not name: continue
            args=n.args
            if len(args)>=2 and isinstance(args[0],ast.Constant) and isinstance(args[0].value,str):
                dead = any(isinstance(c,ast.Constant) and isinstance(c.value,str) and '/Users/' in c.value
                           for c in ast.walk(args[1]))
                if dead: out.append((args[0].value, n.lineno))
    return out

def exec_anchor_lines(src, tree):
    """exec-хиты line-match: строки с /Users/ или /sessions/ вне комментариев и инертных строк (грамматика 620/621/622)."""
    inert_lines=set()
    if tree:
        for n in ast.walk(tree):
            if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
                inert_lines.update(range(n.lineno,(n.value.end_lineno or n.lineno)+1))
    hits=[]
    try:
        toks=list(tokenize.generate_tokens(io.StringIO(src).readline))
    except Exception:
        toks=None
    if toks is not None:
        code_lines=set(); anchor_lines={}
        for t in toks:
            if t.type in (tokenize.COMMENT,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT,tokenize.ENDMARKER):
                continue
            code_lines.add(t.start[0])
            if t.type==tokenize.STRING and ('/Users/' in t.string or '/sessions/' in t.string):
                anchor_lines[t.start[0]]=t.string[:60]
        for ln,s in sorted(anchor_lines.items()):
            if ln in code_lines and ln not in inert_lines:
                hits.append((ln,s))
    else:
        for i,l in enumerate(src.splitlines(),1):
            ls=l.strip()
            if ls.startswith('#'): continue
            if '/Users/' in l or '/sessions/' in l: hits.append((i,l.strip()[:60]+' [FALLBACK-GREP]'))
    return hits

def analyze(p):
    tree,src,err=parse(p)
    r={'file':p,'md5':md5(p),'syntax_error':err}
    if tree:
        r['top_defs']=top_defs(tree); r['all_defs']=all_defs(tree)
        r['env_dead_defaults']=env_dead_defaults(tree)
    else:
        r['top_defs']=[]; r['all_defs']=[]; r['env_dead_defaults']=['UNPARSEABLE — см. exec_anchors fallback']
    r['exec_anchors']=exec_anchor_lines(src,tree)
    return r

if __name__=='__main__':
    res=[analyze(p) for p in sys.argv[1:]]
    print(json.dumps(res,ensure_ascii=False,indent=1,default=str))
