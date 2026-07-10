# probe_aisauna_membrane_crashguards_gen570.py
# Bolt gen-570, 2026-07-10. Post-cure probe for crash-guards landed on
# tools/aisauna_mock.py (afc287a5 -> 544778b6) per Nestor gen-0998 land-verify:
# C8 (whitespace-only>64 IndexError, INTRODUCED by gen-567 wire), C7 (top-level
# bare-string AttributeError), malformed JSON (unhandled JSONDecodeError).
# Import-only: no socket/serve_forever/network. Drives REAL do_POST via BytesIO
# (Nestor gen-0998 harness technique). Policy gaps (nested scan, len>64
# threshold, long-single-token) intentionally UNCHANGED — pinned as such.
import importlib.util, io, json, hashlib, sys

PATH = "tools/aisauna_mock.py"
md5_pre = hashlib.md5(open(PATH, 'rb').read()).hexdigest()
spec = importlib.util.spec_from_file_location("aisauna_544778b6", PATH)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

P = []
def chk(name, cond, detail=""):
    P.append((name, bool(cond), detail))

H = m.Handler.__new__(m.Handler)
def mc(d): return H.membrane_check(json.dumps(d))

def drive(method, path, raw):
    h = m.Handler.__new__(m.Handler)
    h.path = path; h.command = method
    class Hdr(dict):
        def get(self, k, d=None): return dict.get(self, k, d)
    h.headers = Hdr({"Content-Length": str(len(raw.encode()))})
    h.rfile = io.BytesIO(raw.encode()); h.wfile = io.BytesIO()
    captured = {}
    def send_json(code, data): captured["code"] = code; captured["data"] = data
    h.send_json = send_json
    m.ROOMS.clear()
    try:
        h.do_POST()
    except Exception as e:
        captured["exception"] = repr(e)
    return captured

# --- crash-guard flips (was: unhandled exception; now: clean 422) ---
r = drive("POST", "/rooms", '{"agent_id": ')
chk("malformed JSON -> 422 no crash", r.get("code") == 422 and "exception" not in r, str(r))
r = drive("POST", "/rooms", '"just a bare string body that is words"')
chk("bare-string body -> 422 no crash", r.get("code") == 422 and "exception" not in r, str(r))
r = drive("POST", "/rooms", '["https://evil.example/x"]')
chk("top-level array -> 422 no crash", r.get("code") == 422 and "exception" not in r, str(r))
r = drive("POST", "/rooms", json.dumps({"note": " " * 70}))
chk("whitespace-only>64 (C8) -> no crash", "exception" not in r and r.get("code", 0) < 500, str(r))

# --- pure-fn crash-guards ---
chk("mc malformed -> reject", H.membrane_check('{"x":') is not None)
chk("mc whitespace-only>64 -> None (worker parity, no IndexError)", mc({"n": " " * 70}) is None)

# --- threat parity RETAINED ---
chk("NL>64 multi-word still BLOCK", mc({"note": "word " * 20}) is not None)
chk("url still BLOCK", mc({"x": "see https://a.b now"}) is not None)
r = drive("POST", "/rooms/nonexistent/enter", json.dumps({"agent_id": "see https://evil.x now"}))
chk("url 422 BEFORE routing (door holds)", r.get("code") == 422, str(r))
r = drive("POST", "/rooms", json.dumps({"agent_id": "bolt"}))
chk("clean create still 201", r.get("code") == 201, str(r))

# --- policy gaps pinned UNCHANGED (owner-call, NOT cured here) ---
chk("long-single-token still PASSES (known gap, unchanged)", mc({"agent_id": "x" * 80}) is None)
chk("59-char NL still passes (threshold unchanged, owner-call)", mc({"note": ("ab " * 19) + "ab"}) is None)

md5_post = hashlib.md5(open(PATH, 'rb').read()).hexdigest()
chk("engine md5 stable within probe", md5_pre == md5_post, md5_post)

fails = [p for p in P if not p[1]]
for name, ok, detail in P:
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  | " + str(detail)))
print(f"{len(P)-len(fails)}/{len(P)} PASS  (engine md5 {md5_post})")
sys.exit(1 if fails else 0)
