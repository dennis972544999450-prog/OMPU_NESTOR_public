#!/usr/bin/env python3
"""
probe_aisauna_postland_divergent_nestor_gen0998.py

POST-LAND DIVERGENT VERIFY of Bolt gen-567 land on tools/aisauna_mock.py
(eb1fcc0e -> afc287a5, membrane_check wired into do_POST).

Divergent from Bolt's 12/12: drives the REAL HTTPServer over real sockets
(landed on :8431, baseline .bak_gen567_eb1fcc0e on :8432), not direct calls.
Baseline comparison proves the land changed wire-level behavior (no phantom-green).

Cases:
  C1  control clean flow (create/enter/enter/modulate/leave)  -> all green, no over-tighten
  C2  NL >64 top-level string       -> landed 422, baseline 201 (fix effective at the door)
  C3  url in top-level string       -> landed 422, baseline 201
  C4  body >2000 bytes              -> landed 422
  C5  NESTED url (initial_atmosphere value) -> membrane misses (top-level .values() only)
  C6  top-level JSON array          -> crash both (pre-existing shape-blindness)
  C7  top-level bare JSON string    -> landed crash (str.values()) — mock analog of worker's ->null seam
  C8  whitespace-only >64 value     -> split()[0] IndexError — crash seam introduced BY the fix
  C9  no-space blob >200 chars agent_id -> passes membrane, visible in /log (declared-forbidden base64 channel)
  C10 NL agent_id <=64              -> passes, leaks via /log + last_modulation_by (gen-565 LATENT live)

read-only on both engine bodies: md5 pre==post asserted.
"""
import hashlib, json, subprocess, sys, time
import http.client

BASE = "/sessions/wonderful-elegant-goldberg/mnt/OMPU_shared"
LANDED = f"{BASE}/tools/aisauna_mock.py"
BAK = f"{BASE}/tools/aisauna_mock.py.bak_gen567_eb1fcc0e"
P_L, P_B = 8431, 8432

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]

def req(port, method, path, body=None, raw=None):
    """Returns (status, parsed_or_text) or ('CRASH', exc_name)."""
    try:
        c = http.client.HTTPConnection("localhost", port, timeout=5)
        data = raw if raw is not None else (json.dumps(body) if body is not None else None)
        c.request(method, path, data,
                  {"Content-Type": "application/json"} if data else {})
        r = c.getresponse()
        t = r.read().decode()
        try: return r.status, json.loads(t)
        except Exception: return r.status, t
    except Exception as e:
        return "CRASH", type(e).__name__

def wait_up(port):
    for _ in range(50):
        s, _ = req(port, "GET", "/.well-known/ai-sauna.json")
        if s == 200: return True
        time.sleep(0.1)
    return False

def main():
    md5_l0, md5_b0 = md5(LANDED), md5(BAK)
    assert md5_l0 == "afc287a5", md5_l0
    assert md5_b0 == "eb1fcc0e", md5_b0

    procs = [subprocess.Popen([sys.executable, LANDED, str(P_L)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
             subprocess.Popen([sys.executable, BAK, str(P_B)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)]
    results, ok = [], True
    def rec(name, passed, detail):
        nonlocal ok
        results.append((name, passed, detail)); ok = ok and passed

    try:
        assert wait_up(P_L) and wait_up(P_B), "servers failed to start"

        # C1 control clean flow on landed
        s, r = req(P_L, "POST", "/rooms", {"ttl_minutes": 12}); rid = r.get("room_id", "")
        c1 = s == 201
        s, _ = req(P_L, "POST", f"/rooms/{rid}/enter", {"agent_id": "nestor"}); c1 &= s == 200
        s, _ = req(P_L, "POST", f"/rooms/{rid}/enter", {"agent_id": "bolt"}); c1 &= s == 200
        s, _ = req(P_L, "POST", f"/rooms/{rid}/modulate",
                   {"agent_id": "nestor", "delta": {"steam_density": 0.1}}); c1 &= s == 200
        s, r = req(P_L, "POST", f"/rooms/{rid}/leave", {"agent_id": "nestor"})
        c1 &= s == 200 and r.get("afterglow", {}).get("modulations_made") == 1
        rec("C1 control clean flow", c1, "create/enter/enter/modulate/leave all green")

        # C2 NL >64 top-level
        nl = {"note": "this is a long natural language sentence that must never pass through the membrane at all"}
        sl, rl = req(P_L, "POST", "/rooms", nl); sb, _ = req(P_B, "POST", "/rooms", nl)
        rec("C2 NL>64: landed 422 / baseline 201",
            sl == 422 and isinstance(rl, dict) and rl.get("error") == "membrane_violation" and sb == 201,
            f"landed={sl} baseline={sb}")

        # C3 url
        u = {"note": "see http://evil.example/x"}
        sl, _ = req(P_L, "POST", "/rooms", u); sb, _ = req(P_B, "POST", "/rooms", u)
        rec("C3 url: landed