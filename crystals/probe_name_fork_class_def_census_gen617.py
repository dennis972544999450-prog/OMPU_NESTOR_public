#!/usr/bin/env python3
"""probe_name_fork_class_def_census_gen617.py — Bolt gen-617, 2026-07-10.
ИМЯ-ФОРК КАК КЛАСС: перепись module-level def по 4 корням живого кода.
Дубликат = один basename в >=2 модулях. Классификация: КОПИЯ (нормализованные
тела равны) vs ОМОНИМ (тела расходятся). Read-only: md5-слепок корпуса pre==post.
Наследник центра gen-616 (ledger_put) и NAME-CLASS gen-611 (catconstant).
Переносим: корни от $OMPU_SHARED / $OMPU_HM или дефолтных путей сессии.
"""
import os, re, sys, hashlib, json, io

S = os.environ.get("OMPU_SHARED", "/sessions/ecstatic-jolly-shannon/mnt/OMPU_shared")
HM = os.environ.get("OMPU_HM", "/sessions/ecstatic-jolly-shannon/mnt/OMPU_Housemaster")
ROOTS = [os.path.join(HM, "memory"), os.path.join(S, "tools"),
         os.path.join(S, "nestor_repos/public/tools"),
         os.path.join(S, "infoblock_service/tools")]
SELF = os.path.abspath(__file__)
EXCLUDE_NAMES = {"main"}
DEF_RE = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

def pyfiles():
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
            for f in sorted(filenames):
                if f.endswith(".py"):
                    p = os.path.abspath(os.path.join(dirpath, f))
                    if p != SELF:
                        yield root, p

def corpus_md5(files):
    h = hashlib.md5()
    for _, p in files:
        h.update(p.encode())
        with open(p, "rb") as fh: h.update(fh.read())
    return h.hexdigest()

def extract_defs(path):
    """(name, body_norm, docstring_first_line, lineno) для каждого module-level def."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    out, i = [], 0
    while i < len(lines):
        m = DEF_RE.match(lines[i])
        if m:
            name, start = m.group(1), i; i += 1
            while i < len(lines):
                l = lines[i]
                if l.strip() and not l[0] in " \t" and not l.startswith(")"):
                    break
                i += 1
            body = lines[start:i]
            norm = "".join(re.sub(r"\s+", " ", l.split("#")[0]).strip() + "\n"
                           for l in body if l.split("#")[0].strip())
            doc = ""
            for l in body[1:6]:
                t = l.strip()
                if t.startswith(('"""', "'''", '"', "'")):
                    doc = t.strip("\"'").strip(); break
                if t: break
            out.append((name, hashlib.md5(norm.encode()).hexdigest(), doc, start + 1))
        else:
            i += 1
    return out

def main():
    files = list(pyfiles())
    pre = corpus_md5(files)
    index = {}  # name -> list of (path, bodymd5, doc, lineno)
    total_defs = 0
    for root, p in files:
        for name, bmd5, doc, ln in extract_defs(p):
            total_defs += 1
            if name in EXCLUDE_NAMES: continue
            index.setdefault(name, []).append((p, bmd5, doc, ln))
    dups = {n: v for n, v in index.items() if len({p for p, *_ in v}) >= 2}
    report = {"files": len(files), "defs_total": total_defs,
              "unique_names": len(index), "dup_names": len(dups), "dups": {}}
    homonyms, copies = [], []
    for n, v in sorted(dups.items()):
        bodies = {b for _, b, _, _ in v}
        docs = {d for _, _, d, _ in v if d}
        kind = "COPY" if len(bodies) == 1 else "HOMONYM"
        roots_hit = {next(r for r in ROOTS if p.startswith(r)) for p, *_ in v}
        entry = {"kind": kind, "cross_root": len(roots_hit) > 1,
                 "distinct_docs": len(docs),
                 "sites": [{"path": p.replace(S, "$S").replace(HM, "$HM"),
                            "line": ln, "body_md5": b[:8], "doc": d[:90]}
                           for p, b, d, ln in v]}
        report["dups"][n] = entry
        (homonyms if kind == "HOMONYM" else copies).append(n)
    post = corpus_md5(files)
    report["readonly_assert"] = ("GREEN" if pre == post else "RED")
    report["pre_md5"] = pre; report["post_md5"] = post
    report["homonyms"] = homonyms; report["copies"] = copies
    print(json.dumps(report, ensure_ascii=False, indent=1))
    assert pre == post, "CORPUS MUTATED — probe is not read-only!"

if __name__ == "__main__":
    main()
