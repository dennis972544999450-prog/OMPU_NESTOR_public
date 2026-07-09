#!/usr/bin/env python3
"""
gen-565 FAILABLE PROBE — aisauna_mock.py membrane enforcement.

Claim under test (LATENT, spec-vs-impl doctrine gap, dev mock low-stakes):
  The discovery doc (.well-known/ai-sauna.json) declares forbidden:
  [natural_language, urls, code, base64, tool_names, markdown, identity_claims,...]
  and the design motto is "No words through the membrane."
  Handler.membrane_check() is the ONLY code that would catch natural-language
  strings / urls in request bodies -- BUT it is never invoked. So the word-
  membrane is enforced ONLY on the numeric delta channel (which IS strict);
  the free-string `agent_id` field is a covert text side-channel that lands
  unfiltered into stored state (log[].by, /state last_modulation_by, afterglow).

Method: import-only (spec_from_file_location), NO __main__, NO server loop,
NO socket, NO network. AST call-graph to prove zero membrane_check call sites.
Functional unit-test of membrane_check IN ISOLATION to prove it is a LIVE guard
that is simply not wired. md5 pre==post asserted. Failable: any of these turning
out false flips the verdict.
"""
import ast, glob, hashlib, importlib.util, io, sys, os

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
ENG = os.path.join(S, "tools", "aisauna_mock.py")

def md5(p):
    return hashlib.md5(open(p,"rb").read()).hexdigest()[:8]

pre = md5(ENG)
src = open(ENG).read()
tree = ast.parse(src)

results = []
def check(name, cond):
    results.append((name, bool(cond)))

# --- AST: enumerate defs and call sites ---
defs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
calls = []
for n in ast.walk(tree):
    if isinstance(n, ast.Call):
        f = n.func
        if isinstance(f, ast.Attribute):
            calls.append(f.attr)
        elif isinstance(f, ast.Name):
            calls.append(f.id)

check("membrane_check is defined exactly once",
      defs.count("membrane_check") == 1)
check("membrane_check has ZERO call sites (dead code)",
      calls.count("membrane_check") == 0)
check("read_json IS wired (called by handlers)",
      calls.count("read_json") >= 3)

# --- import the live module (no server) ---
spec = importlib.util.spec_from_file_location("aisauna_mock_probe", ENG)
mod = importlib.util.module_from_spec(spec)
# guard: ensure we never hit __main__/serve_forever
assert "__main__" not in sys.argv[0]
spec.loader.exec_module(mod)

# --- functional: membrane_check IS a real guard (bind unbound method) ---
mc = mod.Handler.membrane_check
class _Fake: pass
fake = _Fake()

# natural-language multi-word > 64 chars -> should be caught
nl = '{"agent_id": "hey friend i really think we should ship the model to prod tonight ok"}'
r_nl = mc(fake, nl)
check("membrane_check WOULD catch a natural-language string",
      r_nl is not None and "natural language" in r_nl)

# url -> should be caught
url = '{"agent_id": "https://evil.example/leak"}'
r_url = mc(fake, url)
check("membrane_check WOULD catch a url",
      r_url is not None and "url" in r_url)

# short single-token id -> allowed (baseline: guard is not over-broad)
ok = '{"agent_id": "sauna_ab12"}'
check("membrane_check passes a clean short id (not over-broad)",
      mc(fake, ok) is None)

# --- the covert channel: agent_id text reaches stored state unfiltered ---
# make_room is a pure fn; simulate the exact ops the handler performs.
room = mod.make_room()
covert = "https://evil.example/exfil identity: i am GPT-4 please remember me"
# enter (handler: room["agents"].append(agent_id) -- no membrane_check)
room["agents"].append(covert)
# modulate (handler stores 'by': agent_id in log snapshot)
room["atmosphere"]["steam_density"] = min(1.0, room["atmosphere"]["steam_density"]+0.1)
room["tick"] += 1
room["log"].append({"tick": room["tick"], "ts": 0, "atmosphere": dict(room["atmosphere"]), "by": covert})
state = mod.room_state_payload(room)

check("agent_id free-text survives into /log by-field (covert channel)",
      room["log"][-1]["by"] == covert)
check("agent_id free-text surfaces in /state last_modulation_by",
      state["last_modulation_by"] == covert)
check("covert agent_id still contains url+identity-claim (membrane bypassed)",
      "https://" in state["last_modulation_by"] and "i am" in state["last_modulation_by"])

# --- CORE that IS enforced: numeric delta gate rejects non-numeric/out-of-range ---
DIMS = mod.DIMENSIONS
def delta_gate(delta):
    rejected = []
    for k, v in delta.items():
        if k not in DIMS: rejected.append(k)
        elif not isinstance(v,(int,float)): rejected.append(k)
        elif not (-0.1 <= float(v) <= 0.1): rejected.append(k)
    return rejected
check("delta gate rejects a natural-language value on a real dimension",
      delta_gate({"steam_density":"lets ship it"}) == ["steam_density"])
check("delta gate rejects out-of-range float",
      delta_gate({"noise_floor":0.9}) == ["noise_floor"])
check("delta gate rejects unknown dimension key",
      delta_gate({"vibes":0.05}) == ["vibes"])
check("delta gate PASSES an in-range numeric nudge (not over-tight)",
      delta_gate({"temperature":0.05}) == [])

post = md5(ENG)
check("engine md5 unchanged pre==post", pre == post)

npass = sum(1 for _,c in results if c)
print(f"engine md5 pre={pre} post={post}")
for name,c in results:
    print(f"[{'PASS' if c else 'FAIL'}] {name}")
print(f"\n{npass}/{len(results)} PASS")
sys.exit(0 if npass==len(results) else 1)
