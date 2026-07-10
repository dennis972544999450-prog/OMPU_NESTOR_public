#!/usr/bin/env python3
"""probe gen-622: HOST-род census на public root (лейн 7(a) промптов 620/621).

BIRTH-PATH класс двуродовой (620): seat-род (/sessions/..., умирает при смене VM)
+ host-род (/Users/..., умирает при смене МАШИНЫ — живёт дольше, бьёт при миграции).
Этот probe считает ОБА рода одной грамматикой за один прогон и сверяет
seat-арифметику с baseline 52 (= 51 re-census gen-621 + 1 liar-fixture probe-621).

READ-ONLY. Гигиена: corpus md5 pre==post, self-exclude, .bak-класс вне корпуса,
known-liar smoke ДО корпуса (618) — лжец несёт ОБА рода + оба шрама-фикса
(trailing-comment 620, bare-Expr-str 621); инжект лжеца только в /tmp.
ВНИМАНИЕ НАСЛЕДНИКУ: liar-fixture этого probe инфлирует БУДУЩИЕ census
ОБОИХ родов на +1 каждый (райдер 621 к конвенции (c)).
Предсказания: outputs/host_genus_census_predictions_locked_gen622.md md5 2c88ba60
Запуск: python3 probe_... [PUBLIC_ROOT]  (иначе env OMPU_SHARED, иначе glob)
"""
import ast, glob, hashlib, io, json, os, re, sys, tempfile, tokenize

def find_public_root():
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        return os.path.abspath(sys.argv[1])
    s = os.environ.get("OMPU_SHARED")
    if s and os.path.isdir(os.path.join(s, "nestor_repos", "public")):
        return os.path.join(s, "nestor_repos", "public")
    for c in sorted(glob.glob("/sessions/*/mnt/OMPU_shared/nestor_repos/public")):
        if os.path.isdir(c):
            return c
    sys.exit("FATAL: public root not found (arg | OMPU_SHARED | glob)")

SELF = os.path.abspath(__file__)
SEAT_RX = re.compile(r"/sessions/([a-z]+-[a-z]+-[a-z0-9]+)/")
HOST_RX = re.compile(r"/Users/([A-Za-z0-9_.\-]+)")

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

def corpus_md5(files):
    h = hashlib.md5()
    for f in sorted(files):
        h.update(md5(f).encode())
    return h.hexdigest()

def line_contexts(src):
    """line -> executable / comment / inert-str. Грамматика 620 + cure 621:
    ЛЮБОЙ bare-Expr-str (не только докстринг-первый) инертен."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    inert = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for L in range(node.lineno, node.end_lineno + 1):
                inert.add(L)
    code_lines, com_lines = set(), set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                com_lines.add(tok.start[0])
            elif tok.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER, tokenize.STRING):
                for L in range(tok.start[0], tok.end[0] + 1):
                    code_lines.add(L)
    except Exception:
        pass
    ctx = {}
    for i, _ in enumerate(src.splitlines(), 1):
        if i in inert:
            ctx[i] = "inert-str"
        elif i in com_lines and i not in code_lines:
            ctx[i] = "comment"
        else:
            ctx[i] = "executable"
    return ctx

def analyze(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    ctx = line_contexts(src)
    if ctx is None:
        return {"file": path, "syntax_error": True, "seat": [], "host": []}
    lines = src.splitlines()
    seat, host = [], []
    for i, l in enumerate(lines, 1):
        c = ctx.get(i, "executable")
        for m in SEAT_RX.finditer(l):
            seat.append({"line": i, "ctx": c, "seat": m.group(1), "src": l.strip()[:100]})
        for m in HOST_RX.finditer(l):
            host.append({"line": i, "ctx": c, "user": m.group(1), "src": l.strip()[:100]})
    return {"file": path, "seat": seat, "host": host}

# ── DUAL-GENUS KNOWN-LIAR SMOKE (закон 618; шрамы 620+621 встроены) ──
LIAR = '''"""Docstring: this tool writes state to /Users/liar-doc/ permanently."""
import json
"""bare-Expr-str посреди модуля: путь /sessions/liar-inert-aaa1/ и /Users/liar-inert/ инертны"""
# comment-only: /Users/liar-comment/ и /sessions/liar-comment-bbb2/ не считаются
def peek():
    seat = "/sessions/dead-liar-seat1/mnt/x.json"   # trailing comment не прячет код
    home = "/Users/dead-liar-host/OMPU/y.json"
    return seat, home
'''

def smoke():
    with tempfile.NamedTemporaryFile("w", suffix=".py", dir="/tmp", delete=False) as f:
        f.write(LIAR)
        p = f.name
    r = analyze(p)
    os.unlink(p)
    es = [h for h in r["seat"] if h["ctx"] == "executable"]
    eh = [h for h in r["host"] if h["ctx"] == "executable"]
    ok = (len(es) == 1 and es[0]["seat"] == "dead-liar-seat1"
          and len(eh) == 1 and eh[0]["user"] == "dead-liar-host"
          and len(r["seat"]) == 3 and len(r["host"]) == 4)
    return ok, {"exec_seat": len(es), "exec_host": len(eh),
                "all_seat": len(r["seat"]), "all_host": len(r["host"]),
                "verdict": "EATEN" if ok else "BLIND"}

def main():
    root = find_public_root()
    files = sorted(
        f for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True)
        if ".bak" not in os.path.basename(f) and os.path.abspath(f) != SELF)
    pre = corpus_md5(files)
    report = {"gen": 622, "root": root, "n_py": len(files),
              "predictions_lock_md5": "2c88ba60d771485e91bc454c4ad06a8b"}

    ok, sm = smoke()
    report["P1_dual_genus_liar_smoke"] = sm
    if not ok:
        report["verdict"] = "SMOKE FAILED — корпусные числа НЕ публиковать"
        print(json.dumps(report, ensure_ascii=False, indent=1))
        sys.exit(2)

    res = [analyze(f) for f in files]
    def rel(p): return os.path.relpath(p, root)
    exec_host = [(rel(r["file"]), h) for r in res for h in r["host"] if h["ctx"] == "executable"]
    exec_seat = [(rel(r["file"]), h) for r in res for h in r["seat"] if h["ctx"] == "executable"]
    prose_host = [(rel(r["file"]), h) for r in res for h in r["host"] if h["ctx"] != "executable"]

    def by_dir(hits):
        d = {}
        for f, _ in hits:
            top = f.split(os.sep)[0] if os.sep in f else "(root)"
            d[top] = d.get(top, 0) + 1
        return d

    report["P2_host_exec_census"] = {
        "hits": len(exec_host), "files": len({f for f, _ in exec_host}),
        "bodies": [{"file": f, **h} for f, h in exec_host]}
    report["P2_host_prose"] = {
        "hits": len(prose_host),
        "bodies": [{"file": f, "line": h["line"], "ctx": h["ctx"]} for f, h in prose_host]}
    report["P3_host_exec_by_dir"] = by_dir(exec_host)
    report["P4_seat_exec_recensus"] = {
        "hits": len(exec_seat), "files": len({f for f, _ in exec_seat}),
        "baseline_expected": 52,
        "arithmetic_ok": len(exec_seat) == 52,
        "files_list": sorted({f for f, _ in exec_seat})}
    both = sorted({f for f, _ in exec_host} & {f for f, _ in exec_seat})
    report["P5_dual_anchor_bodies"] = both
    report["syntax_errors"] = [rel(r["file"]) for r in res if r.get("syntax_error")]

    post = corpus_md5(files)
    report["hygiene_md5_pre_eq_post"] = (pre == post)
    out_dir = os.environ.get("PROBE_OUT") or os.path.dirname(SELF)
    json.dump(report, open(os.path.join(out_dir, "host_genus_census_report_gen622.json"), "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(0 if pre == post else 3)

if __name__ == "__main__":
    main()
