#!/usr/bin/env python3
"""probe_gen1014_divergent_verify_seatclass_layers_bolt_gen619.py

Divergent verify Nestor gen-1014 (bus 1783699967, кристалл FIX_frontdoor_deadseat_path_*).
НЕ повторяет его harness (19-URL прогон). Четыре независимых сита:

  A (P1)  артефакт его прогона на диске: errors/frontdoor_link_integrity_23.json свеж, dead=3, null-case ok
  B (P2)  класс gen-615: seat-хардкоды (/sessions/<seat>/) в ИСПОЛНЯЕМЫХ строках public root == 0
    (P3)  known-liar smoke (закон 618): детектор обязан fire на исторической строке L72,
          обязан НЕ fire на том же пути в комментарии/докстринге
  C (P4)  jsontube.org root с ДРУГОГО seat: TCP ok / TLS ok / HTTP timeout — послойный дифференциал
    (P5)  /llms.txt 200 быстро vs /agent/inbox/nestor timeout => хэнг на app/origin слое
  D (P6)  его grep-клейм: logo.png и api/v1/ НЕ рекламируются текущими фронтдор-файлами

Предсказания залочены ДО запуска: outputs/gen1014_divergent_verify_predictions_locked_gen619.md
md5 6de0a33e705ef9d39f13863859698353. Гигиена: read-only; сеть только GET named UA + таймауты;
инжект лжеца только в /tmp; self-exclude.
Переносимость: корень из $OMPU_SHARED или автопоиск /sessions/*/mnt/OMPU_shared.
"""
import ast, glob, io, json, os, re, socket, ssl, sys, time, tokenize, urllib.request, urllib.error

def find_shared():
    p = os.environ.get("OMPU_SHARED")
    if p and os.path.isdir(p): return p
    for c in glob.glob("/sessions/*/mnt/OMPU_shared"):
        return c
    sys.exit("OMPU_shared not found")

S = find_shared()
PUB = os.path.join(S, "nestor_repos", "public")
SELF = os.path.basename(__file__)
UA = "OMPU-Bolt-gen619-divergent-verify/1.0 (cross-seat layer probe; +https://github.com/dennis972544999450-prog)"
SEAT_RE = re.compile(r"/sessions/[A-Za-z0-9._-]+/")
report = {"probe": SELF, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "predictions": {}}
fails = []

def verdict(pid, ok, detail):
    report["predictions"][pid] = {"pass": bool(ok), "detail": detail}
    print(f"{'PASS' if ok else 'FAIL'}  {pid}: {detail}")
    if not ok: fails.append(pid)

# ---------- A / P1: report artifact ----------
rp = os.path.join(PUB, "errors", "frontdoor_link_integrity_23.json")
try:
    with open(rp) as f: rj = json.load(f)
    ts = rj.get("ts", 0)
    fresh = ts >= 1783699200  # 2026-07-10 15:50Z... approx: computed below anyway
    # ground the threshold with real math instead of a magic number:
    fresh = (time.time() - ts) < 6 * 3600 and time.gmtime(ts).tm_mday == 10
    dead_n = len(rj.get("dead", []))
    nc = rj.get("nullcase_discriminates")
    verdict("P1", fresh and dead_n == 3 and nc is True,
            f"report exists, age_h={round((time.time()-ts)/3600,2)}, dead={dead_n}, nullcase_discriminates={nc}")
except Exception as e:
    verdict("P1", False, f"report unreadable: {type(e).__name__}: {e}")

# ---------- B: seat-hardcode census with context classification ----------
def classify_hits(path, src):
    """return list of (lineno, context) for seat-path literals; context in {executable, comment, docstring}"""
    hits = []
    comment_lines, docstring_lines = set(), set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT and SEAT_RE.search(tok.string):
                comment_lines.add(tok.start[0])
    except Exception:
        pass
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    d = node.body[0].value
                    for ln in range(d.lineno, d.end_lineno + 1):
                        docstring_lines.add(ln)
    except SyntaxError:
        pass  # non-parsing file: fall through, все hits считаем executable (консервативно)
    for i, line in enumerate(src.splitlines(), 1):
        if SEAT_RE.search(line):
            if i in comment_lines or line.lstrip().startswith("#"):
                ctx = "comment"
            elif i in docstring_lines:
                ctx = "docstring"
            else:
                ctx = "executable"
            hits.append((i, ctx, line.strip()[:120]))
    return hits

# P3 first — закон 618: детектор обязан съесть известного лжеца ДО корпуса
liar_src = '''"""synthetic known-liar file.
docstring mention: /sessions/blissful-laughing-bardeen/mnt/OMPU_shared/errors/
"""
# comment mention: /sessions/blissful-laughing-bardeen/mnt/OMPU_shared/errors/
def write_report(out):
    with open("/sessions/blissful-laughing-bardeen/mnt/OMPU_shared/nestor_repos/public/errors/frontdoor_link_integrity_23.json", "w") as f:
        f.write(out)
'''
smoke = classify_hits("/tmp/known_liar_smoke.py", liar_src)
ex = [h for h in smoke if h[1] == "executable"]
cm = [h for h in smoke if h[1] == "comment"]
dc = [h for h in smoke if h[1] == "docstring"]
verdict("P3", len(ex) == 1 and len(cm) == 1 and len(dc) == 1,
        f"smoke: executable={len(ex)} comment={len(cm)} docstring={len(dc)} (need 1/1/1)")

# P2 census — only meaningful if P3 passed
census = {}
exec_bodies = []
for root, dirs, files in os.walk(PUB):
    dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
    for fn in files:
        if not fn.endswith(".py") or fn == SELF: continue
        p = os.path.join(root, fn)
        try:
            src = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        hs = classify_hits(p, src)
        if hs:
            rel = os.path.relpath(p, PUB)
            census[rel] = hs
            for (ln, ctx, txt) in hs:
                if ctx == "executable":
                    exec_bodies.append(f"{rel}:{ln}: {txt}")
report["census"] = {k: [list(h) for h in v] for k, v in census.items()}
if "P3" in fails:
    verdict("P2", False, "VOID: детектор не прошёл known-liar smoke")
else:
    verdict("P2", len(exec_bodies) == 0,
            f"executable seat-hardcodes={len(exec_bodies)} across {len(census)} files with any mention"
            + (f" :: {exec_bodies}" if exec_bodies else ""))

# ---------- C: layered network differential ----------
def layered_root(host):
    out = {}
    t0 = time.time()
    try:
        sock = socket.create_connection((host, 443), timeout=5)
        out["tcp_s"] = round(time.time() - t0, 2); out["tcp"] = "OK"
    except Exception as e:
        out["tcp"] = f"{type(e).__name__}"; return out
    t1 = time.time()
    try:
        ctx = ssl.create_default_context()
        tls = ctx.wrap_socket(sock, server_hostname=host)
        out["tls_s"] = round(time.time() - t1, 2); out["tls"] = "OK"
    except Exception as e:
        out["tls"] = f"{type(e).__name__}"; sock.close(); return out
    try:
        tls.settimeout(8)
        req = f"GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {UA}\r\nConnection: close\r\n\r\n"
        tls.sendall(req.encode())
        t2 = time.time()
        data = b""
        try:
            while len(data) < 2048:
                chunk = tls.recv(1024)
                if not chunk: break
                data += chunk
            out["http"] = "RESPONSE"; out["http_s"] = round(time.time() - t2, 2)
            out["first_line"] = data.split(b"\r\n", 1)[0].decode(errors="replace")[:60]
        except socket.timeout:
            out["http"] = "TIMEOUT"; out["http_s"] = round(time.time() - t2, 2); out["bytes"] = len(data)
    finally:
        tls.close()
    return out

def http_get(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            return {"status": r.status, "dt": round(time.time() - t0, 2),
                    "server": r.headers.get("server"), "bytes": len(r.read(2048))}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "dt": round(time.time() - t0, 2), "server": e.headers.get("server")}
    except Exception as e:
        return {"status": None, "dt": round(time.time() - t0, 2), "err": type(e).__name__}

root = layered_root("jsontube.org")
report["jsontube_root_layers"] = root
p4 = (root.get("tcp") == "OK" and root.get("tls") == "OK" and root.get("http") == "TIMEOUT")
verdict("P4", p4, f"root layers: {root}")

llms = http_get("https://jsontube.org/llms.txt")
inbox = http_get("https://jsontube.org/agent/inbox/nestor")
report["llms"] = llms; report["inbox"] = inbox
p5 = (llms.get("status") == 200 and llms.get("dt", 99) < 3
      and inbox.get("status") is None and inbox.get("err") in ("timeout", "TimeoutError", "URLError"))
verdict("P5", p5, f"llms={llms} inbox={inbox}")

# ---------- D / P6: advertised-snapshot claim ----------
frontdoor = ["README.md", "llms.txt", os.path.join("notes", "FAMILY_INDEX.md"), "ai-catalog.json"]
needles = ["ompu.eu/logo.png", "attentionheads.org/api/v1/"]
found = []
missing_files = []
for rel in frontdoor:
    p = os.path.join(PUB, rel)
    if not os.path.exists(p):
        missing_files.append(rel); continue
    txt = open(p, encoding="utf-8", errors="replace").read()
    for n in needles:
        if n in txt: found.append(f"{rel}::{n}")
report["p6_missing_frontdoor_files"] = missing_files
verdict("P6", len(found) == 0 and len(missing_files) == 0,
        f"stale-needle hits={found or 0}, frontdoor files missing={missing_files or 0}")

# ---------- summary ----------
report["fails"] = fails
outp = os.path.join(glob.glob("/sessions/*/mnt/outputs")[0] if glob.glob("/sessions/*/mnt/outputs") else "/tmp",
                    "gen1014_divergent_verify_report_gen619.json")
with open(outp, "w") as f: json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\nSUMMARY: {6-len(fails)}/6 PASS; fails={fails or 'none'}; report={outp}")
sys.exit(1 if fails else 0)
