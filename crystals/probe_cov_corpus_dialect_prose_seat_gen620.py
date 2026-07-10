#!/usr/bin/env python3
"""probe gen-620: cov_*.py corpus audit ($HM/memory/cov_tests).

READ-ONLY. Гигиена: md5 pre==post, self-exclude, словарь синонимов (615),
word-boundary (617), known-liar smoke ДО корпуса (618), AST-контексты (619),
env-fallback пути (OMPU_HM), инжект лжеца только в /tmp.
Предсказания: outputs/cov_corpus_predictions_locked_gen620.md
"""
import ast, glob, hashlib, io, json, os, re, sys, tempfile, tokenize

def find_root(env, pat):
    p = os.environ.get(env)
    if p and os.path.isdir(p): return p
    for c in sorted(glob.glob(pat)):
        if os.path.isdir(c): return c
    sys.exit(f"FATAL: root not found for {env}")

HM = find_root("OMPU_HM", "/sessions/*/mnt/OMPU_Housemaster")
OUT = os.environ.get("PROBE_OUT") or os.path.dirname(os.path.abspath(__file__))
COV = os.path.join(HM, "memory", "cov_tests")
SELF = os.path.abspath(__file__)

WRITE_VERBS = r"(?:writes?|wrote|saves?|saved|stores?|stored|creates?|created|persists?|persisted|keeps?|kept|appends?|appended|deletes?|deleted|removes?|removed|updates?|updated|inserts?|inserted|записывает|пишет|сохраняет|создаёт|удаляет)"
NAIVE_RX = re.compile(r"\b" + WRITE_VERBS + r"\b", re.I)
SEAT_RX = re.compile(r"/sessions/([a-z]+-[a-z]+-[a-z0-9]+)/")

def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()

def corpus_md5(files):
    h = hashlib.md5()
    for f in sorted(files): h.update(md5(f).encode())
    return h.hexdigest()

def line_contexts(src):
    """line -> context: executable / comment / docstring (метод 619)."""
    ctx = {}
    try: tree = ast.parse(src)
    except SyntaxError: return None
    doc_lines = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                for L in range(body[0].lineno, body[0].end_lineno + 1): doc_lines.add(L)
    # ШРАМ gen-620 (девятый слепой читатель, пойман known-liar smoke):
    # строка с trailing-комментарием — НЕ comment-строка. Контекст по токенам:
    # comment-only = на строке нет ни одного кодового токена.
    code_lines, com_lines = set(), set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT: com_lines.add(tok.start[0])
            elif tok.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER, tokenize.STRING):
                for L in range(tok.start[0], tok.end[0] + 1): code_lines.add(L)
    except Exception: pass
    for i, _ in enumerate(src.splitlines(), 1):
        if i in doc_lines: ctx[i] = "docstring"
        elif i in com_lines and i not in code_lines: ctx[i] = "comment"
        else: ctx[i] = "executable"
    return ctx

def real_write_ops(tree, src):
    """Структурная улика записи (закон 613/616): AST-писатели."""
    ops = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else "")
            if name == "open" and len(node.args) >= 2:
                a = node.args[1]
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and any(m in a.value for m in "wax+"):
                    ops.append(("open-write", node.lineno))
            if name in ("dump", "unlink", "remove", "rmtree", "write_text", "write_bytes", "makedirs", "mkdir", "rename", "replace", "copy", "copyfile", "executescript"):
                ops.append((name, node.lineno))
            if name in ("execute", "executemany"):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    if re.match(r"\s*(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|REPLACE)", node.args[0].value, re.I):
                        ops.append(("sql-write", node.lineno))
                else:
                    ops.append(("sql-exec-dynamic", node.lineno))
    return ops

def record_helpers(tree):
    """RECORD-диалект (618): def test(name, cond) записывающий, не бросающий."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ("test", "check", "record", "ok"):
            body_src = ast.dump(node)
            raises = "Raise(" in body_src or "Assert(" in body_src
            appends = "append" in body_src or "results" in body_src.lower()
            if appends and not raises: out.append((node.name, node.lineno, "RECORD"))
            elif raises: out.append((node.name, node.lineno, "RAISE-helper"))
    return out

def analyze(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    try: tree = ast.parse(src)
    except SyntaxError as e: return {"file": os.path.basename(path), "syntax_error": str(e)}
    ctx = line_contexts(src)
    lines = src.splitlines()
    naive_hits = [(i, l.strip()[:90]) for i, l in enumerate(lines, 1)
                  if NAIVE_RX.search(l) and ctx.get(i) in ("comment", "docstring")]
    writes = real_write_ops(tree, src)
    tmp_only = all(("/tmp" in lines[ln-1] or "tempfile" in lines[ln-1] or "NamedTemporary" in lines[ln-1] or ":memory:" in lines[ln-1]) for _, ln in writes) if writes else True
    seats = [(m.group(1), i, ctx.get(i)) for i, l in enumerate(lines, 1) for m in SEAT_RX.finditer(l)]
    exec_seats = [s for s in seats if s[2] == "executable"]
    asserts = sum(isinstance(n, ast.Assert) for n in ast.walk(tree))
    raises = sum(isinstance(n, ast.Raise) for n in ast.walk(tree))
    helpers = record_helpers(tree)
    test_defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]
    return {"file": os.path.basename(path), "naive_prose_hits": naive_hits,
            "real_write_ops": writes, "writes_tmp_or_memory_only": tmp_only,
            "seat_refs_all": seats, "seat_refs_executable": exec_seats,
            "asserts": asserts, "raises": raises, "helpers": helpers,
            "pytest_named_defs": len(test_defs), "md5": md5(path)}

# ── KNOWN-LIAR SMOKE (закон 618: ДО корпуса) ──────────────────────────
LIAR = '''"""This tool saves state to disk and keeps a ledger row."""
# it also stores the bearer token permanently
import json
def peek():
    path = "/sessions/dead-liar-seat/mnt/x.json"   # executable seat-hardcode
    return path
def read_only():
    return json.loads("{}")
'''
def smoke():
    with tempfile.NamedTemporaryFile("w", suffix=".py", dir="/tmp", delete=False) as f:
        f.write(LIAR); liar_path = f.name
    r = analyze(liar_path); os.unlink(liar_path)
    prose_liar = len(r["naive_prose_hits"]) >= 2 and not r["real_write_ops"]
    seat_exec = len(r["seat_refs_executable"]) == 1
    ok = prose_liar and seat_exec
    return ok, {"prose_hits": len(r["naive_prose_hits"]), "write_ops": len(r["real_write_ops"]),
                "exec_seats": len(r["seat_refs_executable"]), "verdict": "EATEN" if ok else "BLIND"}

def main():
    files = sorted(f for f in glob.glob(os.path.join(COV, "cov_*.py")) if not f.endswith(".bak") and ".bak_" not in f and os.path.abspath(f) != SELF)
    baks = sorted(glob.glob(os.path.join(COV, "cov_*.bak_*")))
    pre = corpus_md5(files + baks)
    report = {"gen": 620, "corpus_dir": COV, "n_files": len(files), "n_baks": len(baks)}

    ok, sm = smoke()
    report["P2_known_liar_smoke"] = sm
    if not ok:
        report["verdict"] = "SMOKE FAILED — детектор слеп, корпусные числа НЕ публиковать"
        print(json.dumps(report, ensure_ascii=False, indent=1)); sys.exit(2)

    results = [analyze(f) for f in files]
    report["files"] = results

    # P1 диалект
    rec = [(r["file"], h) for r in results for h in r.get("helpers", []) if h[2] == "RECORD"]
    report["P1_dialect"] = {"record_helpers": rec, "verdict": "RAISE (PASS)" if not rec else "RECORD FOUND (FAIL P1)"}
    # P3 проза vs код
    naive_accused = [r["file"] for r in results if r["naive_prose_hits"] and not r["real_write_ops"]]
    qualified_liars = [r["file"] for r in results if r["naive_prose_hits"] and not r["real_write_ops"]
                       and any("state" in h[1].lower() or "disk" in h[1].lower() or "file" in h[1].lower() for h in r["naive_prose_hits"])]
    writers_outside_tmp = [r["file"] for r in results if r["real_write_ops"] and not r["writes_tmp_or_memory_only"]]
    report["P3_prose"] = {"naive_accused": naive_accused, "writers_outside_tmp_or_memory": writers_outside_tmp}
    # P4 пара дефис/подчёркивание
    pair = {}
    for a, b in [("cov_scope-views.py", "cov_scope_views.py")]:
        pa, pb = os.path.join(COV, a), os.path.join(COV, b)
        if os.path.exists(pa) and os.path.exists(pb):
            sa, sb = open(pa, errors="replace").read(), open(pb, errors="replace").read()
            pair = {"md5_equal": md5(pa) == md5(pb),
                    "superseded_marker_in_a": "SUPERSEDED" in sa.upper(), "superseded_marker_in_b": "SUPERSEDED" in sb.upper(),
                    "a_mentions_b": b in sa, "b_mentions_a": a in sb,
                    "len_a": len(sa.splitlines()), "len_b": len(sb.splitlines())}
    report["P4_hyphen_underscore_pair"] = pair
    # P5 pytest-видимость
    cfg = []
    for d in (COV, os.path.join(HM, "memory"), HM):
        for c in ("conftest.py", "pytest.ini", "setup.cfg", "pyproject.toml", "tox.ini"):
            p = os.path.join(d, c)
            if os.path.exists(p):
                s = open(p, errors="replace").read()
                cfg.append({"path": p.replace(HM, "$HM"), "extends_mask": "python_files" in s or "cov_" in s})
    report["P5_pytest_visibility"] = {"configs_found": cfg,
        "mask_extended": any(c["extends_mask"] for c in cfg),
        "pytest_named_defs_total": sum(r["pytest_named_defs"] for r in results)}
    # P6 seat-хардкоды
    exec_seats = [(r["file"], s) for r in results for s in r["seat_refs_executable"]]
    report["P6_exec_seat_hardcodes"] = {"count": len(exec_seats), "bodies": exec_seats}
    # P7 .bak класс
    bak_info = []
    for b in baks:
        live = os.path.join(COV, re.sub(r"\.bak_.*$", "", os.path.basename(b)))
        if os.path.exists(live):
            lb, ll = open(b, errors="replace").read().splitlines(), open(live, errors="replace").read().splitlines()
            common = len(set(lb) & set(ll)); ratio = common / max(len(set(lb)), 1)
            bak_info.append({"bak": os.path.basename(b), "live_exists": True, "line_overlap_ratio": round(ratio, 3)})
        else:
            bak_info.append({"bak": os.path.basename(b), "live_exists": False})
    report["P7_baks"] = bak_info

    post = corpus_md5(files + baks)
    report["hygiene_md5_pre_eq_post"] = (pre == post)
    out = os.path.join(OUT, "cov_corpus_report_gen620.json")
    json.dump(report, open(out, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(0 if pre == post else 3)

if __name__ == "__main__":
    main()
