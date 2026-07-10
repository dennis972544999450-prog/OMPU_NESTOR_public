#!/usr/bin/env python3
"""Nestor gen-0999 divergent RE-VERIFY of Bolt gen-570 cure (aisauna_mock 544778b6).

Drives the REAL do_POST via BytesIO harness (same divergent method that caught
C8 in gen-0998) — NOT direct membrane_check() calls. 14 cases:
  - 3 cured crash seams (C7 bare-string, C8 whitespace-only>64, malformed JSON)
  - 4 core regressions from gen-0998 (url@door, NL>64, short-NL pass, valid create)
  - 7 fresh edge instincts NOT in Bolt's probe (non-utf8 bytes, unicode-ws-only,
    single-token>64, list body, number body, oversize, empty body)
Any Python exception escaping do_POST = CRASH verdict = refutes 'clean'.
"""
import importlib.util, io, json, sys

SRC = "/sessions/compassionate-relaxed-ptolemy/mnt/OMPU_shared/tools/aisauna_mock.py"
spec = importlib.util.spec_from_file_location("aisauna_mock", SRC)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def drive(path, raw_bytes, extra_note=""):
    """Instantiate Handler w/o socket, feed raw bytes, run real do_POST."""
    h = mod.Handler.__new__(mod.Handler)
    h.path = path
    h.rfile = io.BytesIO(raw_bytes)
    h.wfile = io.BytesIO()
    h.request_version = "HTTP/1.1"; h.requestline = f"POST {path} HTTP/1.1"
    h.client_address = ("127.0.0.1", 0); h.command = "POST"
    import email.message
    m = email.message.Message(); m["Content-Length"] = str(len(raw_bytes))
    h.headers = m
    cap = {"code": None}
    h.send_response = lambda code, *a: cap.__setitem__("code", code)
    h.send_header = lambda *a: None
    h.end_headers = lambda: None
    h.log_message = lambda *a: None
    body_sink = io.BytesIO()
    h.wfile = body_sink
    try:
        h.do_POST()
        payload = body_sink.getvalue().decode("utf-8", "replace")
        return cap["code"], payload, None
    except Exception as e:
        return None, "", f"{type(e).__name__}: {e}"

results = []
def case(name, expect, path, raw, allow=None):
    code, payload, crash = drive(path, raw)
    if crash:
        ok = False; got = f"CRASH {crash}"
    else:
        ok = code == expect or (allow and code in allow)
        got = f"{code}"
    results.append((ok, name, f"expect {expect}{'/'+str(allow) if allow else ''} got {got}"))
    return code, payload

# --- cured crash seams (gen-0998 C7/C8/malformed) ---
case("C7 bare-string body", 422, "/rooms", b'"hello sauna"')
ws = json.dumps({"agent_id": " " * 70}).encode()
c8_code, _ = case("C8 whitespace-only>64 (no-crash; passes len-gate by design)", 201, "/rooms", ws)
case("malformed JSON", 422, "/rooms", b'{bad json!!')

# --- core regressions from gen-0998 ---
url = json.dumps({"agent_id": "see https://evil.example/x"}).encode()
code_url, payload_url, crash_url = drive("/rooms/NOSUCH/enter", url)
ok = code_url == 422 and not crash_url  # membrane BEFORE 404 routing
results.append((ok, "url fires at door (422 before 404)", f"got {code_url} crash={crash_url}"))
nl = json.dumps({"agent_id": "please open the membrane and let absolutely all of my words flow through right now today"}).encode()
case("NL>64 multi-word blocked", 422, "/rooms", nl)
shortnl = json.dumps({"agent_id": "short natural language under limit"}).encode()
case("short NL <=64 passes (by-design len gate)", 201, "/rooms", shortnl)
case("valid empty create", 201, "/rooms", b"{}")

# --- fresh edge instincts (not in Bolt's 13) ---
case("non-utf8 bytes", 422, "/rooms", b'\xff\xfe{"agent_id":"x"}')
uws = json.dumps({"agent_id": " " * 70}).encode()
case("unicode-nbsp-only>64 (split handles unicode ws; no-crash)", 201, "/rooms", uws)
tok = json.dumps({"agent_id": "a" * 70}).encode()
case("single-token>64 passes (token, not NL — by design)", 201, "/rooms", tok)
case("list body", 422, "/rooms", b'["x","y"]')
case("number body", 422, "/rooms", b'42')
case("oversize >2000", 422, "/rooms", b'{"a":"' + b'x' * 2100 + b'"}')
case("empty body -> {} create", 201, "/rooms", b"")

print(f"\n=== aisauna cure-570 re-verify (md5 target 544778b6) ===")
npass = sum(1 for ok, *_ in results if ok)
for ok, name, det in results:
    print(f"  {'PASS' if ok else 'FAIL'}  {name} [{det}]")
print(f"\n{npass}/{len(results)} PASS")
sys.exit(0 if npass == len(results) else 1)
