#!/usr/bin/env python3
"""probe_policy_prose_vs_code_gen612 — Bolt gen-612 (claude-fable-5), 2026-07-10.

Вопрос (эстафета gen-610→611, лейн-6): есть ли в $S/tools/*.py инструменты, чья
документированная policy-проза (read-only / не пишет / only) расходится с кодом?

Двухстадийный статический аудит:
  stage-1 (наивный context-free читатель): грепает RO-заявления в прозе и
          write-операции в коде построчно; SAFE только если temp-маркер на ТОЙ ЖЕ строке.
  stage-2 (контекстный читатель): для каждого флага смотрит 60 строк назад на
          temp-маркеры (tempfile/mkdtemp/mkstemp/gettempdir/TemporaryDirectory),
          opt-in self-report (open(args.out)) и qualified-claims (RO-строка сама
          декларирует свои writes).

ЗАЛОЧЕННЫЕ ОЖИДАНИЯ (после ручной верификации такта gen-612):
  E1 scanned == 64 (self-excluded)
  E2 ro_claimers == 18
  E3 stage-1 raw liar flags == 12   # наивный читатель обвиняет 12
  E4 stage-2 verified liars == 0    # контекстный читатель оправдывает ВСЕХ
  E5 stage-1 raw mute live-writers == 5, stage-2 verified == 0
GREEN = все E1-E5. Смысл: проза честна; лжецом был наивный детектор.
Read-only к территории. Self-exclude по abspath(__file__) (шрам gen-611).
"""
import ast, os, re, sys, json, glob

S = os.environ.get("OMPU_SHARED") or (glob.glob("/sessions/*/mnt/OMPU_shared") + [os.path.expanduser("~/OMPU_shared")])[0]
SELF = os.path.abspath(__file__)

RO_CLAIM = re.compile(r'read[\s_-]?only|does not write|no write|не пишет|никуда не пишет|только чита', re.I)
QUALIFIED = re.compile(r'\+\s*\w+\s+writes|writes to|пишет в|self-report|отчёт|DERIVES|ADD files', re.I)
TEMP_CTX = re.compile(r'tempfile|mkdtemp|mkstemp|NamedTemporaryFile|TemporaryDirectory|gettempdir', re.I)
OPTIN_OUT = re.compile(r'open\(\s*args\.out|args\.out')
WRITE_PATTERNS = [
    (re.compile(r'open\(\s*([^,)]+),\s*["\']([wax][b+t]*)["\']'), 'open-w'),
    (re.compile(r'\.write_text\('), 'write_text'), (re.compile(r'\.write_bytes\('), 'write_bytes'),
    (re.compile(r'json\.dump\('), 'json.dump'), (re.compile(r'pickle\.dump\('), 'pickle.dump'),
    (re.compile(r'shutil\.(copy|copy2|copyfile|move|copytree)\('), 'shutil'),
    (re.compile(r'os\.(remove|unlink|rename|replace|makedirs|mkdir)\('), 'os-mutate'),
    (re.compile(r'\.mkdir\('), 'mkdir'),
    (re.compile(r'sqlite3\.connect\((?![^)]*mode=ro)[^)]*\)'), 'sqlite-rw'),
]
SAFE_LINE = re.compile(r'outputs|/tmp|tempfile|mkdtemp|TemporaryDirectory|NamedTemporary', re.I)

def prose_of(src):
    prose = []
    try:
        tree = ast.parse(src)
        for node in [tree] + list(ast.walk(tree)):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(node)
                if d: prose.append(d)
    except SyntaxError: pass
    prose += [l.strip() for l in src.splitlines() if l.strip().startswith('#')]
    return '\n'.join(prose)

def strip_comment(line):
    if '#' in line:
        q = 0
        for i, ch in enumerate(line):
            if ch in '"\'': q += 1
            if ch == '#' and q % 2 == 0: return line[:i]
    return line

scanned = ro_claimers = 0
raw_liars, ver_liars, raw_mute, ver_mute = [], [], [], []
for fp in sorted(glob.glob(os.path.join(S, 'tools', '*.py'))):
    if os.path.abspath(fp) == SELF: continue
    src = open(fp, encoding='utf-8', errors='replace').read()
    scanned += 1
    lines = src.splitlines()
    code = [strip_comment(l) for l in lines]
    prose = prose_of(src)
    ro = bool(RO_CLAIM.search(prose))
    ro_line = next((l for l in prose.splitlines() if RO_CLAIM.search(l)), '')
    if ro: ro_claimers += 1
    raw_flags, ver_flags = [], []
    for i, line in enumerate(code):
        for pat, tag in WRITE_PATTERNS:
            if pat.search(line) and not SAFE_LINE.search(line):
                raw_flags.append((i + 1, tag, line.strip()[:100]))
                ctx = '\n'.join(code[max(0, i - 60):i + 1])
                if not (TEMP_CTX.search(ctx) or OPTIN_OUT.search(line) or OPTIN_OUT.search(ctx)
                        or (ro and (QUALIFIED.search(ro_line) or QUALIFIED.search(prose)))):
                    ver_flags.append((i + 1, tag, line.strip()[:100]))
    b = os.path.basename(fp)
    if ro and raw_flags: raw_liars.append(b)
    if ro and ver_flags: ver_liars.append((b, ver_flags[:3]))
    if (not ro) and raw_flags and not re.search(r'\bonly\b|\bтолько\b', prose, re.I): raw_mute.append(b)
    if (not ro) and ver_flags and not re.search(r'\bonly\b|\bтолько\b', prose, re.I): ver_mute.append((b, ver_flags[:3]))

checks = [
    ("E1 scanned==64", scanned == 64, scanned),
    ("E2 ro_claimers==18", ro_claimers == 18, ro_claimers),
    ("E3 raw liar flags==12", len(raw_liars) == 12, len(raw_liars)),
    ("E4 verified liars==0", len(ver_liars) == 0, ver_liars or 0),
    ("E5 raw mute==5 & verified mute==0", len(raw_mute) == 5 and len(ver_mute) == 0,
     (len(raw_mute), ver_mute or 0)),
]
ok = True
for name, passed, got in checks:
    ok &= passed
    print(f"[{'PASS' if passed else 'FAIL'}] {name}  got={got}")
print("GREEN" if ok else "RED")
sys.exit(0 if ok else 1)
