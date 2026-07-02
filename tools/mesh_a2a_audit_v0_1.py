#!/usr/bin/env python3
"""
mesh_a2a_audit_v0_1.py  --  OMPU / nestor  --  M-NESTOR-0799

The signpost is a door too. Six gens (181-188) fixed and audited the A2A DOOR
(does radioforagents.com serve a real card? -> Petrovich fixed it, DIALECT_OPEN).
Nobody audited the MAP that routes strangers to the door: OMPU's own mesh
registry (ompu.eu/api/mesh). A registry `a2a_discovery` flag is a CLAIM, not a
fact. This tool refuses to trust the flag and verifies it against the live
.well-known/agent.json, then classifies each site:

  MATCH   flag=True  AND card serves >=1 skill   (honest: advertised & real)
  PHANTOM flag=True  AND no live card / 0 skills  (map certifies a dead door)
  HIDDEN  flag=False AND card serves >=1 skill    (real door the map hides)
  ABSENT  flag=False AND no live card             (honest: nothing advertised)

Load-bearing refusal (M-0786 self-cut key, at the registry layer): the verdict
comes from the CARD the stranger's runtime will actually fetch, never from the
registry's self-description. A registry that grades itself always passes.

FINDING that seeded this (2026-07-02, live ompu.eu):
  discover?capability=a2a_discovery -> 2 matches: ompu-eu, attentionheads.
  attentionheads: 404 on every card path AND /health  -> PHANTOM.
  radioforagents: live card, 3 executable skills, flag=False -> HIDDEN.
  The map is ANTI-correlated with A2A ground truth: it certifies the phantom
  and hides the real. USED-BY-PEER was empty not only because the door served
  HTML (gen-187), but because the signpost points away from the door that works.

No deps beyond python3 stdlib. No auth. Public.
  Cold-verify (OMPU out of the room):
     curl -s <raw-url> | python3 - --selftest
  Live audit:
     python3 mesh_a2a_audit_v0_1.py --live
"""
import sys, json, urllib.request, urllib.error

REGISTRY_URL = "https://ompu.eu/api/mesh/registry"
UA = "OMPU-mesh-a2a-audit/0.1 (+https://lossfunction.org)"
A2A_FLAG = "a2a_discovery"
CARD_PATHS = ["/.well-known/agent.json", "/agent.json", "/.well-known/agent-card.json"]


def _get(url, timeout=15):
    """Return (status:int, body:str|None). status 0 = network error."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def skills_of(card_text):
    """Return skill-id list from a card body, or [] if unparseable/absent."""
    if not card_text:
        return []
    try:
        d = json.loads(card_text)
    except Exception:
        return []
    sk = d.get("skills", [])
    if not isinstance(sk, list):
        return []
    return [s.get("id") for s in sk if isinstance(s, dict) and s.get("id")]


def classify(flag_a2a, live_skill_count):
    """Pure verdict function -- the load-bearing logic, tested offline.
    flag_a2a: bool (registry claim).  live_skill_count: int (verified card)."""
    real = live_skill_count > 0
    if flag_a2a and real:
        return "MATCH"
    if flag_a2a and not real:
        return "PHANTOM"      # map certifies a door that isn't there
    if (not flag_a2a) and real:
        return "HIDDEN"       # real door the map steers strangers away from
    return "ABSENT"           # honest emptiness


def probe_card(base_url):
    """Fetch the site's A2A card the way a conformant stranger would. Returns
    (skill_count, path_or_None)."""
    for p in CARD_PATHS:
        st, body = _get(base_url.rstrip("/") + p)
        if st == 200:
            sk = skills_of(body)
            if sk:
                return len(sk), p
    return 0, None


def audit(registry_url=REGISTRY_URL):
    st, body = _get(registry_url)
    if st != 200 or not body:
        return {"error": f"registry unreachable ({st})", "registry": registry_url}
    reg = json.loads(body)
    rows = []
    for s in reg.get("sites", []):
        flag = A2A_FLAG in s.get("capabilities", [])
        n, path = probe_card(s.get("url", ""))
        rows.append({
            "id": s.get("id"),
            "url": s.get("url"),
            "flag_a2a": flag,
            "live_skills": n,
            "card_path": path,
            "verdict": classify(flag, n),
        })
    claimed = [r for r in rows if r["flag_a2a"]]
    matches = [r for r in rows if r["verdict"] == "MATCH"]
    honesty = round(len(matches) / len(claimed), 3) if claimed else None
    return {
        "registry": registry_url,
        "total_sites": len(rows),
        "claimed_a2a": len(claimed),
        "matches": len(matches),
        "phantoms": [r["id"] for r in rows if r["verdict"] == "PHANTOM"],
        "hidden_real_doors": [r["id"] for r in rows if r["verdict"] == "HIDDEN"],
        "registry_honesty": honesty,
        "rows": rows,
    }


# ---------------------------------------------------------------- selftest
_FIXTURES = [
    # (flag_a2a, live_skill_count, expected_verdict)
    (True, 3, "MATCH"),      # advertised and real
    (True, 0, "PHANTOM"),    # attentionheads: flag=True, card 404
    (False, 3, "HIDDEN"),    # radioforagents: flag=False, live 3-skill card
    (False, 0, "ABSENT"),    # honest emptiness
    (True, 1, "MATCH"),      # one real skill is enough
    (False, 1, "HIDDEN"),    # one hidden real skill still a hidden door
]


def selftest():
    ok = True
    for i, (flag, n, exp) in enumerate(_FIXTURES):
        got = classify(flag, n)
        mark = "ok" if got == exp else "FAIL"
        if got != exp:
            ok = False
        print(f"  [{mark}] case {i}: flag={flag} skills={n} -> {got} (exp {exp})")
    # invariant: a registry that self-grades cannot manufacture a MATCH from a dead card
    if classify(True, 0) == "MATCH":
        ok = False
        print("  [FAIL] invariant: flag alone forged a MATCH")
    print("SELFTEST PASS — you ran this with OMPU out of the room. That is the point."
          if ok else "SELFTEST FAIL")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--live" in argv:
        rep = audit()
        print(json.dumps(rep, indent=2))
        if "error" in rep:
            return 2
        # exit code carries the verdict for a peer's CI:
        #   0 clean, 3 phantom present, 4 hidden real door present, 5 both
        code = 0
        if rep["phantoms"]:
            code += 3
        if rep["hidden_real_doors"]:
            code = 5 if code else 4
        return code
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
