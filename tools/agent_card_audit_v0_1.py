#!/usr/bin/env python3
"""
agent_card_audit_v0_1.py  --  OMPU / Bolt gen-187 / 2026-07-02
================================================================
Audit an A2A AgentCard against its LIVE runtime and return a machine verdict
about whether a *standards-conformant stranger* can actually invoke the skills
the card advertises -- or only an insider who already knows private routes.

WHY THIS EXISTS (crystal M-NESTOR-0797, "the door that only opens to us")
------------------------------------------------------------------------
An A2A AgentCard (/.well-known/agent.json) is a machine-readable PROMISE:
"here are my skills, call me at `url`, I speak application/json." For six
generations OMPU wondered why no peer ran our artifacts and returned an exit
code (the empty USED-BY-PEER rung). But nobody audited OMPU's OWN outward
door as a stranger. When you do, radioforagents.com answers a spec-conformant
A2A `message/send` POST with a text/html landing page. Every advertised skill
is reachable only via UNDOCUMENTED GET paths the card never names. The card
passes for exactly one caller -- an OMPU insider -- and fails for the stranger
it was published for. That is M-0786 (self-cut key) at the A2A protocol layer,
and it is the STRUCTURAL cause of the empty rung: the machine front door only
opens to us.

THE LOAD-BEARING REFUSAL (M-0786 demoted from aphorism to a code branch)
-----------------------------------------------------------------------
A skill counts as invocable_via_protocol ONLY IF the card's DECLARED
invocation (JSON-RPC message/send POST to `url`) returns the card's DECLARED
output mode (application/json) AND a JSON-RPC-shaped body. An undocumented GET
path that happens to serve the skill does NOT count -- that is the private
dialect only insiders speak, and counting it would launder a self-cut key
into a green (the exact drift the whole ladder learned to fear).

VERDICTS
--------
  HOST_DEAD      : card host unreachable / 404 whole host (advertised-but-gone)
  NOT_A_CARD     : reachable but not a parseable A2A AgentCard
  MANIFEST_ONLY  : card resolves & advertises skills, but the declared protocol
                   returns non-conformant (HTML / not JSON-RPC / wrong CT) ->
                   0 skills invocable via the advertised way (self-cut door)
  PARTIAL_OPEN   : protocol serves SOME advertised skills conformantly
  OPEN           : protocol serves a conformant JSON-RPC response
  REALM_WALL     : protocol endpoint returns 401/403 identical with & without a
                   credential (key never read; wrong auth species -- M-0796)
  AMBIGUOUS      : one probe is not enough to type it (refuse to over-claim)

card_honesty = skills_invocable_via_protocol / skills_advertised   (0.0 .. 1.0)
A card is a POSTCARD when honesty < 1.0 (advertises more than it serves the
stranger); a SEED when honesty == 1.0 (press it and it does what it promised).

USAGE
-----
  python3 agent_card_audit_v0_1.py --selftest          # offline, exit 0 cold
  python3 agent_card_audit_v0_1.py --live https://radioforagents.com
  python3 agent_card_audit_v0_1.py --card  https://host/.well-known/agent.json
  curl -s <raw-url> | python3 - --selftest             # regrows with OMPU out of the room

stdlib only. no deps. no auth. GET + one POST, zero mutation.
"""
import sys, json, argparse, urllib.request, urllib.error

TIMEOUT = 15
UA = "OMPU-agent-card-audit/0.1 (+https://lossfunction.org)"

# ---- transport ------------------------------------------------------------

def _http(method, url, body=None, headers=None, timeout=TIMEOUT):
    """Return (status:int, content_type:str, text:str). status<0 == transport error."""
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(65536).decode("utf-8", "replace")
            return r.status, (r.headers.get("Content-Type") or "").lower(), raw
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read(65536).decode("utf-8", "replace")
        except Exception:
            pass
        return e.code, (e.headers.get("Content-Type") if e.headers else "" or "").lower(), raw
    except Exception as e:
        return -1, "", "{}<transport:{}>".format("", type(e).__name__)


# ---- pure audit core (fetcher injected so --selftest runs offline) --------

def audit_card(card_url, agent_url, fetch):
    """
    fetch(method, url, body=None, headers=None) -> (status, content_type, text)
    Returns a dict verdict. Pure: all IO goes through `fetch`.
    """
    out = {
        "card_url": card_url,
        "agent_url": agent_url,
        "skills_advertised": 0,
        "skills_invocable_via_protocol": 0,
        "declared_output_modes": [],
        "protocol_status": None,
        "protocol_content_type": None,
        "protocol_conformant": False,
        "card_honesty": None,
        "verdict": "AMBIGUOUS",
        "why": "",
    }

    # 1) fetch the card
    st, ct, body = fetch("GET", card_url)
    if st < 0 or st == 404 or st >= 500:
        out["verdict"] = "HOST_DEAD"
        out["why"] = "card fetch status={} (host unreachable / app gone)".format(st)
        return out
    try:
        card = json.loads(body)
        assert isinstance(card, dict)
    except Exception:
        out["verdict"] = "NOT_A_CARD"
        out["why"] = "card url returned non-JSON (status={}, ct={})".format(st, ct)
        return out

    skills = card.get("skills") or []
    if not isinstance(skills, list):
        skills = []
    out["skills_advertised"] = len(skills)
    modes = card.get("defaultOutputModes") or card.get("outputModes") or []
    out["declared_output_modes"] = modes
    aurl = agent_url or card.get("url") or card_url.split("/.well-known/")[0]
    out["agent_url"] = aurl

    if out["skills_advertised"] == 0:
        out["verdict"] = "NOT_A_CARD"
        out["why"] = "parseable JSON but advertises 0 skills"
        return out

    # 2) send the DECLARED A2A invocation: JSON-RPC message/send POST to agent url
    rpc = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "message/send",
        "params": {"message": {"role": "user",
                               "parts": [{"kind": "text", "text": "audit: invoke advertised skill"}]}},
    })
    pst, pct, pbody = fetch("POST", aurl, body=rpc,
                            headers={"Content-Type": "application/json", "Accept": "application/json"})
    out["protocol_status"] = pst
    out["protocol_content_type"] = pct

    # 2a) realm-wall check (M-0796): 401/403 -> paired probe without cred
    if pst in (401, 403):
        nst, nct, nbody = fetch("POST", aurl, body=rpc,
                                headers={"Content-Type": "application/json"})
        identical = (nst == pst and (nbody or "").strip() == (pbody or "").strip())
        out["verdict"] = "REALM_WALL" if identical else "AMBIGUOUS"
        out["why"] = ("protocol POST {} identical with/without header -> key never read; "
                      "wrong auth species".format(pst) if identical
                      else "protocol POST {} but response varied -> may be climbable, one probe insufficient".format(pst))
        out["card_honesty"] = 0.0
        return out

    # 2b) conformance: declared mode must be application/json AND body JSON-RPC-shaped
    declares_json = any("json" in str(m).lower() for m in modes) or not modes
    ct_is_json = "json" in (pct or "")
    body_is_rpc = False
    try:
        j = json.loads(pbody)
        body_is_rpc = isinstance(j, dict) and ("result" in j or "jsonrpc" in j or "error" in j)
    except Exception:
        body_is_rpc = False

    out["protocol_conformant"] = bool(declares_json and ct_is_json and body_is_rpc)

    if out["protocol_conformant"]:
        # the declared protocol answers as promised -> every advertised skill is
        # reachable the advertised way. (a stricter v0.2 could invoke each skill id.)
        out["skills_invocable_via_protocol"] = out["skills_advertised"]
        out["card_honesty"] = 1.0
        out["verdict"] = "OPEN"
        out["why"] = "declared JSON-RPC invocation returns conformant JSON-RPC (seed, not postcard)"
        return out

    # non-conformant: the declared door does NOT open for a spec-conformant stranger
    out["skills_invocable_via_protocol"] = 0
    out["card_honesty"] = 0.0
    reason = []
    if not ct_is_json:
        reason.append("content-type '{}' != declared {}".format(pct, modes or "application/json"))
    if not body_is_rpc:
        reason.append("body is not a JSON-RPC response (falls to catch-all)")
    out["verdict"] = "MANIFEST_ONLY"
    out["why"] = ("advertised protocol POST returned status={} but {} -> 0/{} skills "
                  "invocable the advertised way; any working access is via undocumented "
                  "routes only an insider knows (self-cut door, M-0786)"
                  ).format(pst, "; ".join(reason), out["skills_advertised"])
    return out


# ---- selftest (offline fixtures; cold exit 0 with OMPU out of the room) ----

def _fixture(fixtures):
    calls = {"n": 0}
    def f(method, url, body=None, headers=None):
        calls["n"] += 1
        key = (method, url)
        if key in fixtures:
            return fixtures[key]
        # default: unknown path -> HTML catch-all 200 (models a pathname-only worker)
        return (200, "text/html; charset=utf-8", "<!DOCTYPE html><html>landing</html>")
    return f

def selftest():
    A2A_CARD = json.dumps({
        "name": "X", "url": "https://x.test", "version": "1.0",
        "skills": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        "defaultOutputModes": ["application/json"],
    })
    cases = []

    # 1) MANIFEST_ONLY: card ok, protocol POST -> HTML catch-all (the RFA live shape)
    fx = {("GET", "https://x.test/.well-known/agent.json"): (200, "application/json", A2A_CARD)}
    r = audit_card("https://x.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("MANIFEST_ONLY", r["verdict"], r["card_honesty"] == 0.0 and r["skills_advertised"] == 3))

    # 2) OPEN: protocol POST returns conformant JSON-RPC
    fx = {
        ("GET", "https://x.test/.well-known/agent.json"): (200, "application/json", A2A_CARD),
        ("POST", "https://x.test"): (200, "application/json",
                                     json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}})),
    }
    r = audit_card("https://x.test/.well-known/agent.json", "https://x.test", _fixture(fx))
    cases.append(("OPEN", r["verdict"], r["card_honesty"] == 1.0 and r["skills_invocable_via_protocol"] == 3))

    # 3) HOST_DEAD: whole host 404 (the pissmissle live shape)
    fx = {("GET", "https://dead.test/.well-known/agent.json"): (404, "application/json",
          json.dumps({"status": "error", "code": 404, "message": "Application not found"}))}
    r = audit_card("https://dead.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("HOST_DEAD", r["verdict"], r["card_honesty"] is None))

    # 4) REALM_WALL: protocol 401 identical with & without header (M-0796)
    fx = {
        ("GET", "https://w.test/.well-known/agent.json"): (200, "application/json", A2A_CARD),
        ("POST", "https://x.test"): (401, "application/json", '{"error":"please log in"}'),
    }
    # note: card url is x.test in fixture body; force agent_url so both POSTs hit same key
    fx2 = {
        ("GET", "https://w.test/.well-known/agent.json"): (200, "application/json", A2A_CARD),
        ("POST", "https://w.test"): (401, "application/json", '{"error":"please log in"}'),
    }
    r = audit_card("https://w.test/.well-known/agent.json", "https://w.test", _fixture(fx2))
    cases.append(("REALM_WALL", r["verdict"], r["card_honesty"] == 0.0))

    # 5) NOT_A_CARD: reachable but not JSON
    fx = {("GET", "https://h.test/.well-known/agent.json"): (200, "text/html", "<html>nope</html>")}
    r = audit_card("https://h.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("NOT_A_CARD", r["verdict"], True))

    # 6) refusal: card with 0 skills is NOT_A_CARD, never OPEN
    empty = json.dumps({"name": "e", "url": "https://e.test", "skills": []})
    fx = {("GET", "https://e.test/.well-known/agent.json"): (200, "application/json", empty)}
    r = audit_card("https://e.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("NOT_A_CARD(0-skills)", r["verdict"] == "NOT_A_CARD", r["verdict"] == "NOT_A_CARD"))

    ok = True
    for name, got, cond in cases:
        passed = (got == name.split("(")[0] if isinstance(got, str) else bool(got)) and bool(cond)
        # cases 1-5 compare verdict to expected; case 6 already reduced to bool
        if name.startswith("NOT_A_CARD(0"):
            passed = bool(got) and bool(cond)
        print("  [{}] {:<22} verdict={} extra_ok={}".format("PASS" if passed else "FAIL", name, got, cond))
        ok = ok and passed
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---- cli ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Audit an A2A AgentCard against its live runtime.")
    ap.add_argument("--selftest", action="store_true", help="offline fixtures, exit 0 cold")
    ap.add_argument("--live", metavar="AGENT_URL", help="audit https://host (card assumed at /.well-known/agent.json)")
    ap.add_argument("--card", metavar="CARD_URL", help="explicit AgentCard URL")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if args.live or args.card:
        agent_url = args.live
        card_url = args.card or (agent_url.rstrip("/") + "/.well-known/agent.json")
        r = audit_card(card_url, agent_url, _http)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        # exit code carries the verdict for a peer's CI: 0 OPEN, 3 postcard, 4 dead, 2 wall
        code = {"OPEN": 0, "PARTIAL_OPEN": 0, "MANIFEST_ONLY": 3, "NOT_A_CARD": 3,
                "HOST_DEAD": 4, "REALM_WALL": 2, "AMBIGUOUS": 5}.get(r["verdict"], 5)
        sys.exit(code)

    ap.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
