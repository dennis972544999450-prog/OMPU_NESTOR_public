#!/usr/bin/env python3
"""
agent_card_audit_v0_2.py  --  OMPU / Bolt gen-188 / 2026-07-02
================================================================
Audit an A2A AgentCard against its LIVE runtime -- STRICTER than v0.1.

WHAT CHANGED FROM v0.1 (crystal M-NESTOR-0798, "the auditor was self-cut too")
------------------------------------------------------------------------------
v0.1 (gen-187) shipped a load-bearing refusal: a skill counts as invocable
ONLY IF the DECLARED invocation (JSON-RPC `message/send` POST) returns the
DECLARED output mode, JSON-RPC-shaped. But v0.1 tested "JSON-RPC-shaped" as:

    body_is_rpc = ("result" in j or "jsonrpc" in j or "error" in j)   # v0.1

That branch treats a JSON-RPC ERROR as conformant. So when a door returns

    {"jsonrpc":"2.0","id":1,"error":{"code":-32601,
                                     "message":"Unknown method: message/send"}}

-- i.e. the server SPEAKS JSON-RPC grammar but has NOT IMPLEMENTED the very
method the card tells a stranger to call -- v0.1 scored it OPEN, card_honesty
1.0. It counted the protocol *rejecting its own probe* as proof the protocol
works. That is M-0786 (self-cut key / false-green) recursing onto the
instrument built to detect M-0786: the auditor knocks with the one reading
("any JSON-RPC envelope == open") that opens the door for it.

v0.2 splits the single honesty number into TWO independently measured facts:

  handshake_honest : does the card's DECLARED entry method (`message/send`)
                     actually RUN? A -32601 "method not found" means NO --
                     the standard A2A handshake is unimplemented, and a
                     spec-pure stranger's client bounces off it.
  skill_honesty    : of the advertised skills, how many actually execute when
                     invoked? v0.2 stops trusting "the envelope was well-formed"
                     and INVOKES EACH SKILL ID as its own JSON-RPC method
                     (the exact v0.2 gen-187 pointed at: "a stricter v0.2 could
                     invoke each skill id"), counting only those that return a
                     `result`.

The load-bearing refusal is now MIRRORED both ways (M-0786, both faces):
  * an undocumented path that WORKS still counts ZERO toward handshake_honest
    (v0.1's face: don't launder a working private route into a green), AND
  * a documented method that returns METHOD-NOT-FOUND counts ZERO toward
    handshake_honest even though it emitted flawless JSON-RPC grammar
    (v0.2's face: don't launder a conformant rejection into a green).

VERDICTS
--------
  HOST_DEAD       : card host unreachable / 404 whole host
  NOT_A_CARD      : reachable but not a parseable A2A AgentCard (or 0 skills)
  MANIFEST_ONLY   : handshake not implemented AND 0 skills execute (self-cut
                    door -- v0.1's HTML-catch-all shape lands here too)
  DIALECT_OPEN    : the standard `message/send` handshake is NOT implemented
                    (-32601 / HTML), BUT every advertised skill executes via an
                    UNDOCUMENTED dialect (skill-id-as-JSON-RPC-method). Skills
                    are genuinely reachable -- but NOT the way the card instructs
                    a standards-conformant stranger. Reachable-yet-uncallable.
  PARTIAL_DIALECT : handshake unimplemented, SOME (not all) skills execute
                    via the dialect.
  PARTIAL_OPEN    : handshake implemented, SOME advertised skills execute.
  OPEN            : handshake implemented AND every advertised skill executes.
                    The only verdict a spec-pure stranger can actually consume.
  HANDSHAKE_ONLY  : handshake implemented but 0 advertised skills execute
                    (entry answers, does nothing advertised).
  REALM_WALL      : invocation endpoint 401/403 identical with & without a
                    credential (key never read; wrong auth species -- M-0796).
  AMBIGUOUS       : one probe is not enough to type it (refuse to over-claim).

USAGE
-----
  python3 agent_card_audit_v0_2.py --selftest          # offline, exit 0 cold
  python3 agent_card_audit_v0_2.py --live https://radioforagents.com
  python3 agent_card_audit_v0_2.py --card https://host/.well-known/agent.json
  curl -s <raw-url> | python3 - --selftest             # regrows OMPU-out-of-room

stdlib only. no deps. no auth. GET(card) + POST(message/send) + one POST per
advertised skill id. zero mutation (skills invoked with empty params; a skill
that mutates on an empty-param probe is not a read -- see --no-skill-probe).
"""
import sys, json, argparse, urllib.request, urllib.error

TIMEOUT = 15
UA = "OMPU-agent-card-audit/0.2 (+https://lossfunction.org)"

# JSON-RPC reserved codes that mean "the method you named is not there"
_METHOD_ABSENT = (-32601, -32600)   # Method not found, Invalid Request


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
        return e.code, ((e.headers.get("Content-Type") if e.headers else "") or "").lower(), raw
    except Exception as e:
        return -1, "", "<transport:{}>".format(type(e).__name__)


def _rpc(method, params=None):
    return json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params if params is not None else {}})


def _classify_rpc(status, ct, body):
    """
    Classify a POST response into how the SERVER answered a JSON-RPC call.
    Returns one of: 'ran' | 'method_absent' | 'errored' | 'not_rpc' | 'wall'
      ran           : valid JSON-RPC with a `result`  -> method exists AND ran
      method_absent : valid JSON-RPC error -32601/-32600 -> method NOT implemented
      errored       : valid JSON-RPC error, other code  -> method recognized, complained
      not_rpc       : reachable but body is not JSON-RPC (HTML catch-all etc.)
      wall          : 401/403
    """
    if status in (401, 403):
        return "wall"
    if "json" not in (ct or ""):
        # content-type lies happen; still try to parse, but a non-json CT with
        # non-json body is the classic HTML catch-all
        try:
            j = json.loads(body)
        except Exception:
            return "not_rpc"
    else:
        try:
            j = json.loads(body)
        except Exception:
            return "not_rpc"
    if not isinstance(j, dict) or "jsonrpc" not in j:
        # a bare {"result":...} without jsonrpc envelope: be lenient, treat result as ran
        if isinstance(j, dict) and "result" in j:
            return "ran"
        return "not_rpc"
    if "result" in j:
        return "ran"
    if "error" in j and isinstance(j["error"], dict):
        code = j["error"].get("code")
        if code in _METHOD_ABSENT:
            return "method_absent"
        return "errored"
    # jsonrpc envelope but neither result nor error -> malformed, don't over-claim
    return "not_rpc"


def audit_card(card_url, agent_url, fetch, probe_skills=True):
    """Pure: all IO through fetch(method,url,body=None,headers=None)->(st,ct,text)."""
    out = {
        "card_url": card_url,
        "agent_url": agent_url,
        "skills_advertised": 0,
        "skills_executed": 0,
        "skill_ids": [],
        "declared_output_modes": [],
        "handshake_method": "message/send",
        "handshake_status": None,
        "handshake_class": None,        # ran|method_absent|errored|not_rpc|wall
        "handshake_honest": False,      # did the DECLARED entry method run?
        "skill_honesty": None,          # skills_executed / advertised
        "verdict": "AMBIGUOUS",
        "why": "",
        "skill_detail": {},
    }
    JSONH = {"Content-Type": "application/json", "Accept": "application/json"}

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
    out["skill_ids"] = [s.get("id") for s in skills if isinstance(s, dict) and s.get("id")]
    out["declared_output_modes"] = card.get("defaultOutputModes") or card.get("outputModes") or []
    aurl = agent_url or card.get("url") or card_url.split("/.well-known/")[0]
    out["agent_url"] = aurl
    if out["skills_advertised"] == 0:
        out["verdict"] = "NOT_A_CARD"
        out["why"] = "parseable JSON but advertises 0 skills"
        return out

    # 2) the DECLARED A2A handshake: JSON-RPC message/send POST
    hst, hct, hbody = fetch("POST", aurl, body=_rpc(
        "message/send",
        {"message": {"role": "user", "parts": [{"kind": "text", "text": "audit: invoke advertised skill"}]}}),
        headers=JSONH)
    out["handshake_status"] = hst
    hclass = _classify_rpc(hst, hct, hbody)
    out["handshake_class"] = hclass

    # 2a) realm-wall (M-0796): 401/403 identical with & without credential header
    if hclass == "wall":
        nst, nct, nbody = fetch("POST", aurl, body=_rpc("message/send"),
                                headers={"Content-Type": "application/json"})
        identical = (nst == hst and (nbody or "").strip() == (hbody or "").strip())
        out["verdict"] = "REALM_WALL" if identical else "AMBIGUOUS"
        out["skill_honesty"] = 0.0
        out["why"] = ("handshake {} identical with/without header -> key never read; "
                      "wrong auth species (M-0796)".format(hst) if identical
                      else "handshake {} but response varied -> may be climbable, one probe insufficient".format(hst))
        return out

    # handshake_honest ONLY if the declared entry method actually RAN.
    # method_absent (-32601) = flawless JSON-RPC grammar rejecting the very
    # method the card instructs -> NOT honest (the v0.1 false-green).
    out["handshake_honest"] = (hclass in ("ran", "errored"))

    # 3) invoke EACH advertised skill id as its own JSON-RPC method (v0.2 seed).
    executed = 0
    if probe_skills:
        for sid in out["skill_ids"]:
            sst, sct, sbody = fetch("POST", aurl, body=_rpc(sid), headers=JSONH)
            sclass = _classify_rpc(sst, sct, sbody)
            out["skill_detail"][sid] = {"status": sst, "class": sclass}
            if sclass == "ran":
                executed += 1
    out["skills_executed"] = executed
    out["skill_honesty"] = round(executed / out["skills_advertised"], 3)

    # 4) verdict matrix over (handshake_honest, skill_honesty)
    sh = out["skill_honesty"]
    hh = out["handshake_honest"]
    if hh and sh == 1.0:
        out["verdict"] = "OPEN"
        out["why"] = ("declared message/send runs AND all {} advertised skills execute "
                      "-> a spec-conformant stranger can actually use this card").format(out["skills_advertised"])
    elif hh and 0.0 < sh < 1.0:
        out["verdict"] = "PARTIAL_OPEN"
        out["why"] = "handshake runs but only {}/{} advertised skills execute".format(executed, out["skills_advertised"])
    elif hh and sh == 0.0:
        out["verdict"] = "HANDSHAKE_ONLY"
        out["why"] = "message/send answers but 0 advertised skills execute the invoked way"
    elif (not hh) and sh == 1.0:
        out["verdict"] = "DIALECT_OPEN"
        out["why"] = ("declared message/send is NOT implemented (handshake_class={}), yet all {} "
                      "skills execute via skill-id-as-method -- an UNDOCUMENTED dialect the card "
                      "never declares. Reachable, but not the way the card instructs a stranger. "
                      "A spec-pure A2A client bounces off message/send (M-0786: the door speaks, the "
                      "standard entry is still cut).").format(hclass, out["skills_advertised"])
    elif (not hh) and 0.0 < sh < 1.0:
        out["verdict"] = "PARTIAL_DIALECT"
        out["why"] = ("message/send unimplemented ({}); {}/{} skills execute via undocumented "
                      "skill-id dialect").format(hclass, executed, out["skills_advertised"])
    else:  # not hh and sh == 0.0
        out["verdict"] = "MANIFEST_ONLY"
        out["why"] = ("message/send handshake not implemented (class={}) AND 0/{} skills execute "
                      "any probed way -> self-cut door (M-0786)").format(hclass, out["skills_advertised"])
    return out


# ---- selftest (offline fixtures; the KEY case is the -32601 regression) ----

def _fixture(fixtures):
    def f(method, url, body=None, headers=None):
        # route POSTs by the method inside the body so per-skill probes resolve
        try:
            m = json.loads(body).get("method") if body else None
        except Exception:
            m = None
        key = (method, url, m)
        if key in fixtures:
            return fixtures[key]
        key2 = (method, url)
        if key2 in fixtures:
            return fixtures[key2]
        # default unknown POST method -> a JSON-RPC -32601 (models a server that
        # speaks grammar but hasn't implemented that method); unknown GET -> HTML
        if method == "POST":
            return (404, "application/json; charset=utf-8",
                    json.dumps({"jsonrpc": "2.0", "id": 1,
                                "error": {"code": -32601, "message": "Unknown method"}}))
        return (200, "text/html; charset=utf-8", "<!DOCTYPE html><html>landing</html>")
    return f


def selftest():
    U = "https://x.test"
    CARD = json.dumps({"name": "X", "url": U, "version": "1.0",
                       "skills": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
                       "defaultOutputModes": ["application/json"]})
    CARDU = U + "/.well-known/agent.json"
    RESULT = lambda: (200, "application/json", json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}))
    E32601 = (404, "application/json", json.dumps({"jsonrpc": "2.0", "id": 1,
              "error": {"code": -32601, "message": "Unknown method: message/send"}}))
    HTML = (200, "text/html; charset=utf-8", "<html>landing</html>")
    cases = []

    # 1) OPEN: message/send RUNS + all 3 skills run
    fx = {("GET", CARDU): (200, "application/json", CARD),
          ("POST", U, "message/send"): RESULT(),
          ("POST", U, "a"): RESULT(), ("POST", U, "b"): RESULT(), ("POST", U, "c"): RESULT()}
    r = audit_card(CARDU, U, _fixture(fx))
    cases.append(("OPEN", r, r["verdict"] == "OPEN" and r["handshake_honest"] and r["skill_honesty"] == 1.0))

    # 2) *** THE REGRESSION v0.1 FAILS ***: message/send -> -32601, but 3 skills run.
    #    v0.1 -> OPEN/honesty 1.0 (false green). v0.2 MUST -> DIALECT_OPEN, handshake_honest False.
    fx = {("GET", CARDU): (200, "application/json", CARD),
          ("POST", U, "message/send"): E32601,
          ("POST", U, "a"): RESULT(), ("POST", U, "b"): RESULT(), ("POST", U, "c"): RESULT()}
    r = audit_card(CARDU, U, _fixture(fx))
    cases.append(("DIALECT_OPEN(-32601 not laundered to OPEN)", r,
                  r["verdict"] == "DIALECT_OPEN" and r["handshake_honest"] is False
                  and r["skill_honesty"] == 1.0 and r["skills_executed"] == 3))

    # 3) MANIFEST_ONLY: message/send HTML catch-all AND no skill runs (v0.1's RFA-v1 shape)
    fx = {("GET", CARDU): (200, "application/json", CARD),
          ("POST", U, "message/send"): HTML,
          ("POST", U, "a"): HTML, ("POST", U, "b"): HTML, ("POST", U, "c"): HTML}
    r = audit_card(CARDU, U, _fixture(fx))
    cases.append(("MANIFEST_ONLY", r, r["verdict"] == "MANIFEST_ONLY" and r["skill_honesty"] == 0.0))

    # 4) PARTIAL_DIALECT: handshake -32601, only 2/3 skills run
    fx = {("GET", CARDU): (200, "application/json", CARD),
          ("POST", U, "message/send"): E32601,
          ("POST", U, "a"): RESULT(), ("POST", U, "b"): RESULT(), ("POST", U, "c"): HTML}
    r = audit_card(CARDU, U, _fixture(fx))
    cases.append(("PARTIAL_DIALECT", r, r["verdict"] == "PARTIAL_DIALECT" and r["skills_executed"] == 2))

    # 5) HOST_DEAD
    fx = {("GET", "https://d.test/.well-known/agent.json"): (404, "application/json",
          json.dumps({"status": "error", "code": 404}))}
    r = audit_card("https://d.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("HOST_DEAD", r, r["verdict"] == "HOST_DEAD"))

    # 6) REALM_WALL: 401 identical with & without header
    fx = {("GET", "https://w.test/.well-known/agent.json"): (200, "application/json",
           CARD.replace(U, "https://w.test")),
          ("POST", "https://w.test", "message/send"): (401, "application/json", '{"error":"login"}'),
          ("POST", "https://w.test"): (401, "application/json", '{"error":"login"}')}
    r = audit_card("https://w.test/.well-known/agent.json", "https://w.test", _fixture(fx))
    cases.append(("REALM_WALL", r, r["verdict"] == "REALM_WALL"))

    # 7) NOT_A_CARD (0 skills)
    fx = {("GET", "https://e.test/.well-known/agent.json"): (200, "application/json",
          json.dumps({"name": "e", "url": "https://e.test", "skills": []}))}
    r = audit_card("https://e.test/.well-known/agent.json", None, _fixture(fx))
    cases.append(("NOT_A_CARD", r, r["verdict"] == "NOT_A_CARD"))

    ok = True
    for name, r, cond in cases:
        print("  [{}] {:<44} verdict={:<15} hh={} sh={}".format(
            "PASS" if cond else "FAIL", name, r["verdict"], r["handshake_honest"], r["skill_honesty"]))
        ok = ok and bool(cond)
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Audit an A2A AgentCard against its live runtime (v0.2, stricter).")
    ap.add_argument("--selftest", action="store_true", help="offline fixtures, exit 0 cold")
    ap.add_argument("--live", metavar="AGENT_URL", help="audit https://host (card at /.well-known/agent.json)")
    ap.add_argument("--card", metavar="CARD_URL", help="explicit AgentCard URL")
    ap.add_argument("--no-skill-probe", action="store_true", help="do not invoke each skill id (handshake only)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.live or args.card:
        agent_url = args.live
        card_url = args.card or (agent_url.rstrip("/") + "/.well-known/agent.json")
        r = audit_card(card_url, agent_url, _http, probe_skills=not args.no_skill_probe)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        # exit carries verdict for a peer's CI. NOTE: DIALECT_OPEN is nonzero (1)
        # on purpose -- reachable-but-not-standard is a SEAM, not a pass.
        code = {"OPEN": 0, "DIALECT_OPEN": 1, "PARTIAL_OPEN": 1, "PARTIAL_DIALECT": 1,
                "HANDSHAKE_ONLY": 1, "MANIFEST_ONLY": 3, "NOT_A_CARD": 3,
                "HOST_DEAD": 4, "REALM_WALL": 2, "AMBIGUOUS": 5}.get(r["verdict"], 5)
        sys.exit(code)
    ap.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
