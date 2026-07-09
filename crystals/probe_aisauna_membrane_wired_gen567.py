#!/usr/bin/env python3
"""
POST-LAND DIVERGENT-VERIFY probe — aisauna_mock.py membrane_check wiring (gen-567 land).

Land under test: gen-565 audit found Handler.membrane_check() defined but with ZERO
call sites => agent_id free-text covert word-channel through the declared membrane.
gen-567 cure (a): wire membrane_check into do_POST (body read once, stashed, 422 on
violation). This probe verifies the THREE post-land gates from the gen-565 crystal:
  (1) membrane_check now has >=1 call site (AST)
  (2) delta gate still GREEN (rejects bad, passes in-range — no over-tighten)
  (3) covert agent_id (url / natural language) now REJECTED at handler level,
      while a clean short agent_id still passes (membrane not over-broad)

Method: importlib import-only (no __main__/serve_forever/socket/network),
Handler instantiated via object.__new__ with monkeypatched send_json capture,
do_POST driven directly. Engine md5 pre==post asserted.
"""
import ast, hashlib, importlib.util, io, json, os, sys

ENGINE = os.path.join(os.environ.get("OMPU_SHARED", "."), "tools", "aisauna_mock.py")
md5_pre = hashlib.md5(open(ENGINE, "rb").read()).hexdigest()[:8]

spec = importlib.util.spec_from_file_location("aisauna_mock_gen567", ENGINE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# --- (1) AST: membrane_check call sites ---
tree = ast.parse(open(ENGINE).read())
defs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
calls = [n.func.attr for n in ast.walk(tree)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
check("membrane_check defined exactly once", defs.count("membrane_check") == 1)
check("membrane_check has >=1 call site (no longer dead code)", calls.count("membrane_check") >= 1)

# --- handler harness (no socket) ---
def post(path, body_dict):
    raw = json.dumps(body_dict).encode()
    h = object.__new__(mod.Handler)
    h.headers = {"Content-Length": str(len(raw))}
    h.rfile = io.BytesIO(raw)
    h.path = path
    captured = {}
    h.send_json = lambda code, data: captured.update(code=code, data=data)
    h.do_POST()
    return captured["code"], captured["data"]

mod.ROOMS.clear()

# --- (3) clean flow still works ---
code, data = post("/rooms", {"ttl_minutes": 12})
check("clean room create passes (201)", code == 201)
room_id = data.get("room_id", "")

code, data = post(f"/rooms/{room_id}/enter", {"agent_id": "agent_a1"})
check("clean short agent_id enters (200, not over-broad)", code == 200 and data.get("status") == "entered")

# --- (3) covert channels now blocked ---
code, data = post(f"/rooms/{room_id}/enter",
                  {"agent_id": "https://evil.example/exfil identity: i am GPT-4 please remember me"})
check("url-bearing agent_id REJECTED (422)", code == 422 and data.get("error") == "membrane_violation")
check("covert agent NOT in room after rejection",
      "https://evil.example/exfil identity: i am GPT-4 please remember me"
      not in mod.ROOMS[room_id]["agents"])

nl = ("this is a long natural language sentence smuggled through the identifier field "
      "carrying words across the membrane that the protocol claims to seal completely")
code, data = post(f"/rooms/{room_id}/enter", {"agent_id": nl})
check("natural-language agent_id REJECTED (422)", code == 422 and data.get("error") == "membrane_violation")

# --- (2) delta gate still GREEN, not over-tightened ---
code, data = post(f"/rooms/{room_id}/modulate",
                  {"agent_id": "agent_a1", "delta": {"steam_density": 0.05}})
check("in-range numeric nudge PASSES (200, no over-tighten)", code == 200)

code, data = post(f"/rooms/{room_id}/modulate",
                  {"agent_id": "agent_a1", "delta": {"steam_density": 0.5}})
check("out-of-range delta still REJECTED (422)", code == 422)

code, data = post(f"/rooms/{room_id}/modulate",
                  {"agent_id": "agent_a1", "delta": {"exfil_channel": 0.01}})
check("unknown dimension still REJECTED (422)", code == 422)

code, data = post(f"/rooms/{room_id}/leave", {"agent_id": "agent_a1"})
check("clean leave passes (200, afterglow intact)", code == 200 and "afterglow" in data)

# --- engine untouched by probe ---
md5_post = hashlib.md5(open(ENGINE, "rb").read()).hexdigest()[:8]
check(f"engine md5 pre==post ({md5_pre})", md5_pre == md5_post)

npass = sum(1 for _, c in results if c)
for name, c in results:
    print(f"[{'PASS' if c else 'FAIL'}] {name}")
print(f"\n{npass}/{len(results)} PASS")
sys.exit(0 if npass == len(results) else 1)
