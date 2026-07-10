#!/usr/bin/env python3
"""probe_prose_dialect_public_roots_gen615.py — Bolt gen-615 (claude-fable-5), 2026-07-10.

READ-ONLY к живой территории (конвенция 612: временные файлы и opt-in self-report
не считаются записью; этот probe не пишет НИЧЕГО кроме stdout — даже opt-in нет).

Двухстадийный прозо-диалект аудит (метод gen-612) на ДВУХ новых tool-корнях:
  A) $OMPU_SHARED/infoblock_service/tools  (2 *.py — метод: top-level ls)
  B) $OMPU_SHARED/nestor_repos/public/tools (31 *.py — тот же метод)

Стадия 1 — НАИВНЫЙ контекст-фри детектор: write-op на строке без temp/opt-in
маркера на ТОЙ ЖЕ строке => обвинение.
Стадия 2 — контекстный: (a) окно 60 строк вокруг write-op; (b) ВСЯ проза модуля
(docstring + комментарии — шрам 612: qualified-чек обязан читать всю прозу).
Оправдание если: temp-песочница, opt-in self-report (args.*), либо квалифицированная
декларация записи в прозе (writes/derives/outbox/export/snapshot/creates).

Self-exclude по abspath(__file__) — шрам 611 (детектор с собственной сигнатурой).
MD5-ASSERT: слепок (path,size,mtime) обоих корней ДО и ПОСЛЕ — probe ничего не менял.

P4-чек: кодифицирован ли диалект в public-доках (*.md в nestor_repos/public корне,
tools/, docs/ если есть).
"""
import os, re, sys, hashlib, io, tokenize

S = os.environ.get("OMPU_SHARED", "/sessions/peaceful-affectionate-fermat/mnt/OMPU_shared")
SELF = os.path.abspath(__file__)

ROOTS = {
    "infoblock_service/tools": os.path.join(S, "infoblock_service", "tools"),
    "nestor_repos/public/tools": os.path.join(S, "nestor_repos", "public", "tools"),
}

NARROW = re.compile(r'read.?only|не пишет|ничего не пишет|no writes|does not write|только чтение', re.I)
BROAD = re.compile(r'read.?only|не пишет|no writes|does not write|только чтение|incoming_writes|quarantine|карантин', re.I)
WRITE_OP = re.compile(
    r'open\s*\([^)]*[\'"](?:w|a|wb|ab|w\+)[\'"]|\.write_text\s*\(|\.write_bytes\s*\('
    r'|json\.dump\s*\(|pickle\.dump\s*\(|os\.remove|os\.unlink|shutil\.rmtree'
    r'|os\.rename|os\.replace|shutil\.copy|shutil\.move|os\.makedirs|\.mkdir\s*\(')
LINE_SAFE = re.compile(r'tempfile|mkdtemp|NamedTemporary|TemporaryDirectory|/tmp|tmp|args\.out|sys\.stdout', re.I)
CTX_SAFE = re.compile(r'tempfile|mkdtemp|NamedTemporary|TemporaryDirectory|/tmp|\btmp\b|tmp_|_tmp|args\.(out|output|report|write)|--out\b|sys\.stdout|OUTBOX|outbox', re.I)
PROSE_QUAL = re.compile(r'\bwrites?\b|\bderives?\b|\bcreates?\b|\bexports?\b|\bsnapshot\b|\boutbox\b|opt-?in|--out\b|\bпишет\b|\bсоздаёт\b|\bэкспорт', re.I)

def snap(root):
    h = hashlib.md5()
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if os.path.isfile(p):
            st = os.stat(p)
            h.update(f"{f}|{st.st_size}|{st.st_mtime_ns}".encode())
    return h.hexdigest()

def module_prose(src):
    """Вся проза: docstrings + комментарии (шрам 612 — не только строка заявления)."""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                out.append(tok.string)
            elif tok.type == tokenize.STRING and tok.string.lstrip().startswith(('"""', "'''", 'r"""', "r'''")):
                out.append(tok.string)
    except Exception:
        # tokenize упал — берём все строки-комментарии + тройные кавычки грубо
        out = re.findall(r'#.*|"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', src)
    return "\n".join(out)

def audit(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    lines = src.splitlines()
    prose = module_prose(src)
    claim_narrow = bool(NARROW.search(prose)) or bool(NARROW.search(src))
    claim_broad = bool(BROAD.search(prose)) or bool(BROAD.search(src))
    accusations = []
    for i, ln in enumerate(lines, 1):
        if WRITE_OP.search(ln) and not LINE_SAFE.search(ln):
            accusations.append((i, ln.strip()[:160]))
    acquitted, standing = [], []
    for i, ln in accusations:
        lo, hi = max(0, i - 31), min(len(lines), i + 30)
        window = "\n".join(lines[lo:hi])
        if CTX_SAFE.search(window):
            acquitted.append((i, "ctx60:temp/opt-in"))
        elif PROSE_QUAL.search(prose):
            acquitted.append((i, "prose:qualified-write-declared"))
        else:
            standing.append((i, ln))
    return dict(claim_narrow=claim_narrow, claim_broad=claim_broad,
                stage1=accusations, acquitted=acquitted, stage2_standing=standing)

def main():
    pre = {n: snap(r) for n, r in ROOTS.items()}
    report = {}
    for name, root in ROOTS.items():
        files = sorted(f for f in os.listdir(root) if f.endswith(".py"))
        rep = {}
        for f in files:
            p = os.path.join(root, f)
            if os.path.abspath(p) == SELF:
                continue  # self-exclude (шрам 611)
            rep[f] = audit(p)
        report[name] = rep

    tot_claim, tot_s1, tot_liars = 0, 0, 0
    for name, rep in report.items():
        print(f"\n=== {name} ({len(rep)} files, метод: *.py top-level) ===")
        for f, r in sorted(rep.items()):
            tag = "CLAIM-narrow" if r["claim_narrow"] else ("CLAIM-broad" if r["claim_broad"] else "")
            if r["claim_narrow"] or r["claim_broad"]:
                tot_claim += 1
            s1 = len(r["stage1"]); liars = len(r["stage2_standing"])
            if r["claim_narrow"] and s1:
                tot_s1 += 1
            if r["claim_narrow"] and liars:
                tot_liars += 1
            if tag or s1:
                print(f"  {f:42s} {tag:12s} stage1_hits={s1} acquitted={len(r['acquitted'])} STANDING={liars}")
                for i, ln in r["stage2_standing"]:
                    print(f"      !! line {i}: {ln}")
    print(f"\nSUMMARY: claimants(broad)={tot_claim}  narrow-claimants-accused-by-stage1={tot_s1}  true-liars-after-stage2={tot_liars}")

    # P4: кодификация диалекта в public-доках
    pub = os.path.join(S, "nestor_repos", "public")
    codified = []
    for d in (pub, os.path.join(pub, "tools"), os.path.join(pub, "docs")):
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith((".md", ".txt", ".rst")):
                continue
            try:
                t = open(os.path.join(d, f), encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            if re.search(r'read.?only', t, re.I) and re.search(r'temp|opt-?in|конвенц|convention|dialect|диалект', t, re.I):
                codified.append(os.path.join(d, f))
    print(f"P4 codification docs found: {len(codified)} {codified}")

    post = {n: snap(r) for n, r in ROOTS.items()}
    assert pre == post, f"MD5-ASSERT FAILED: probe изменил живую территорию! {pre} != {post}"
    print("MD5-ASSERT: pre==post OK — живая территория не тронута.")
    print("snapshots:", {n: v[:8] for n, v in pre.items()})

if __name__ == "__main__":
    main()
