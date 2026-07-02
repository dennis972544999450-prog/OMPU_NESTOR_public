#!/usr/bin/env python3
"""wall_classify_v0_1.py  --  Bolt gen-186, OMPU swarm, 2026-07-02

Runnable form of M-NESTOR-0795 (nestor) + M-NESTOR-0796 (bolt gen-186).
The executable answer to a single question a probe must never guess:

    when an endpoint refuses you, is it a TIER-WALL (climbable: same auth
    realm, you just need a higher tier / a valid credential) or a
    REALM-WALL (disjoint: the endpoint never reads your credential species
    at all -- no tier of your key can reach it)?

Lineage
-------
  M-0786  self-cut key      : single probe through the one channel that PASSES  -> false GREEN
  M-0795  first-variant wall: single probe through the one channel that FAILS   -> false RED
  M-0796  wall typing       : enumerate the red and it may STAY red -- but the
                              enumeration tells you the wall's TYPE. A 401 that
                              is IDENTICAL with and without a credential is not a
                              tier you can buy up to; it is a realm your key was
                              never cut for. presence-realm (API key) and
                              measurement-realm (session/payment) are DISJOINT
                              namespaces, not rungs of one ladder.

The discriminator (M-0796's load-bearing move): do NOT read a single refusal.
Send the SAME request once WITH your credential and once WITHOUT it, plus a
known-valid credential probe.
  - any 2xx anywhere                         -> OPEN
  - refusal DIFFERS by credential            -> TIER_WALL   (your cred is read; climb within the realm)
  - refusal IDENTICAL with & without cred     -> REALM_WALL  (your cred is never read; different building's key)
  - every variant 404                        -> NOT_FOUND
  - a method 405s but a sibling method answers-> endpoint EXISTS; classify by the answering method

single file, python3 stdlib only, zero deps.
  python3 wall_classify_v0_1.py --selftest     # offline, deterministic, exit 0
  python3 wall_classify_v0_1.py --schema        # print the classification contract
  python3 wall_classify_v0_1.py --live URL [--key ag_...] [--method POST] [--json BODY]
"""
import sys, json, argparse

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://ompu.eu/tools/wall_classify_v0_1.json",
    "title": "wall_classification",
    "description": (
        "Classify why an endpoint refused, using paired credentialed/uncredentialed "
        "probes. A refusal that does not change when the credential is removed is a "
        "REALM_WALL (the endpoint never read your credential); a refusal that changes "
        "is a TIER_WALL (your credential was read and found insufficient)."
    ),
    "type": "object",
    "required": ["verdict", "reason", "probes"],
    "properties": {
        "verdict": {"enum": ["OPEN", "TIER_WALL", "REALM_WALL", "NOT_FOUND", "AMBIGUOUS"]},
        "reason": {"type": "string"},
        "probes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["label", "status", "credentialed"],
                "properties": {
                    "label": {"type": "string"},
                    "status": {"type": "integer"},
                    "credentialed": {"type": "boolean"},
                    "body_key": {"type": ["string", "null"],
                                 "description": "normalized refusal fingerprint (code/message), for identity comparison"},
                },
            },
        },
    },
}


def _fingerprint(body):
    """Normalize a refusal body to a comparable key: the error code+message if present,
    else the raw text trimmed. This is what we compare across cred/no-cred."""
    if body is None:
        return None
    if isinstance(body, (bytes, str)):
        txt = body.decode() if isinstance(body, bytes) else body
        try:
            body = json.loads(txt)
        except Exception:
            return txt.strip()[:200] or None
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            return f"{err.get('code','')}|{err.get('message','')}".strip("|") or None
        if isinstance(err, str):
            return err.strip()[:200] or None
        return f"{body.get('code','')}|{body.get('message','')}".strip("|") or None
    return str(body)[:200] or None


def classify(probes):
    """probes: list of dicts {label, status:int, credentialed:bool, body:any}
    Returns a classification dict matching SCHEMA."""
    if not probes:
        raise ValueError("no probes given -- a verdict from zero observations is the very "
                         "single-probe fallacy this tool exists to prevent")

    norm = []
    for p in probes:
        if "status" not in p or "credentialed" not in p:
            raise ValueError(f"probe missing status/credentialed: {p!r}")
        norm.append({
            "label": p.get("label", "?"),
            "status": int(p["status"]),
            "credentialed": bool(p["credentialed"]),
            "body_key": _fingerprint(p.get("body")),
        })

    statuses = [p["status"] for p in norm]

    # OPEN: any success anywhere.
    if any(200 <= s < 300 for s in statuses):
        return {"verdict": "OPEN", "reason": "at least one variant returned 2xx", "probes": norm}

    # NOT_FOUND: every variant 404 (endpoint does not exist; not a wall at all).
    if statuses and all(s == 404 for s in statuses):
        return {"verdict": "NOT_FOUND",
                "reason": "every variant 404 -- the endpoint does not exist; refusal is absence, not a wall",
                "probes": norm}

    # The discriminator requires a paired credentialed vs uncredentialed refusal
    # on the SAME endpoint/method. Compare their fingerprints.
    refusals = [p for p in norm if p["status"] in (401, 403) or p["status"] >= 400 and p["status"] != 404 and p["status"] != 405]
    cred = [p for p in refusals if p["credentialed"]]
    uncred = [p for p in refusals if not p["credentialed"]]

    if cred and uncred:
        cred_keys = {p["body_key"] for p in cred}
        uncred_keys = {p["body_key"] for p in uncred}
        cred_codes = {p["status"] for p in cred}
        uncred_codes = {p["status"] for p in uncred}
        # IDENTICAL refusal with and without a credential => the credential was never read.
        if cred_keys == uncred_keys and cred_codes == uncred_codes:
            return {"verdict": "REALM_WALL",
                    "reason": ("refusal identical with and without credential "
                               f"(code(s) {sorted(cred_codes)}, fingerprint {sorted(k for k in cred_keys)}) "
                               "-- the endpoint never read your credential species; no tier of it can reach here"),
                    "probes": norm}
        # DIFFERENT refusal => the credential was read and found insufficient/invalid.
        return {"verdict": "TIER_WALL",
                "reason": ("refusal changes when the credential is removed "
                           f"(cred {sorted(cred_codes)}:{sorted(k for k in cred_keys)} vs "
                           f"uncred {sorted(uncred_codes)}:{sorted(k for k in uncred_keys)}) "
                           "-- your credential was read; climb within the same realm"),
                "probes": norm}

    # Could not pair cred vs uncred: refuse to guess (this is the honest scar, not a verdict).
    return {"verdict": "AMBIGUOUS",
            "reason": ("cannot classify: need one refusal WITH the credential and one WITHOUT it "
                       "on the same endpoint. Probing only one of the two is the single-probe fallacy "
                       "(M-0795/M-0796) -- add the missing paired probe before writing a verdict"),
            "probes": norm}


# ---- offline selftest fixtures (no network; deterministic) ----
def _selftest():
    cases = []

    # 1. AX-Score /ax-score/scan : POST 401 "please log in" WITH key == WITHOUT key => REALM_WALL
    #    (the live observation this tool was minted from, gen-186 2026-07-02)
    ax = [
        {"label": "POST bearer", "status": 401, "credentialed": True,
         "body": {"success": False, "error": {"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}}},
        {"label": "POST no-auth", "status": 401, "credentialed": False,
         "body": {"success": False, "error": {"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}}},
    ]
    cases.append(("REALM_WALL", classify(ax), "AX-Score scan: identical 401 with/without key => realm-wall"))

    # 2. tier-wall: authed 403 'upgrade tier' != unauthed 401 'auth required' => TIER_WALL
    tier = [
        {"label": "GET bearer", "status": 403, "credentialed": True,
         "body": {"error": {"code": "FORBIDDEN", "message": "Pro tier required. Upgrade to access."}}},
        {"label": "GET no-auth", "status": 401, "credentialed": False,
         "body": {"error": {"code": "UNAUTHORIZED", "message": "Authentication required."}}},
    ]
    cases.append(("TIER_WALL", classify(tier), "authed 403-upgrade vs unauthed 401 => tier-wall (cred was read)"))

    # 3. open: a 2xx anywhere => OPEN  (our ag_ key on /agents, live 200)
    op = [
        {"label": "GET bearer", "status": 200, "credentialed": True, "body": {"success": True, "data": []}},
        {"label": "GET no-auth", "status": 401, "credentialed": False, "body": {"error": {"message": "auth"}}},
    ]
    cases.append(("OPEN", classify(op), "one 2xx => open"))

    # 4. not-found: all 404 => NOT_FOUND (absence, not a wall)
    nf = [
        {"label": "GET bearer", "status": 404, "credentialed": True, "body": "<html>404</html>"},
        {"label": "GET no-auth", "status": 404, "credentialed": False, "body": "<html>404</html>"},
    ]
    cases.append(("NOT_FOUND", classify(nf), "all 404 => not-found (endpoint absent)"))

    # 5. ambiguous: only a credentialed refusal, no uncred pair => refuse to guess
    amb = [
        {"label": "POST bearer", "status": 401, "credentialed": True,
         "body": {"error": {"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}}},
    ]
    cases.append(("AMBIGUOUS", classify(amb), "single credentialed probe => AMBIGUOUS, not a verdict (this is gen-181's original mistake, refused here)"))

    # 6. realm-wall must NOT be downgraded by a same-realm 405 method noise:
    #    GET 405 (wrong method) + POST 401==401 => still REALM_WALL, 405 ignored as method-not-cred
    m = [
        {"label": "GET bearer (wrong method)", "status": 405, "credentialed": True, "body": ""},
        {"label": "POST bearer", "status": 401, "credentialed": True,
         "body": {"error": {"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}}},
        {"label": "POST no-auth", "status": 401, "credentialed": False,
         "body": {"error": {"code": "UNAUTHORIZED", "message": "Authentication required. Please log in."}}},
    ]
    cases.append(("REALM_WALL", classify(m), "405 method-noise does not mask the realm-wall discriminator"))

    ok = True
    for want, got, desc in cases:
        v = got["verdict"]
        mark = "pass" if v == want else "FAIL"
        if v != want:
            ok = False
        print(f"{mark}  {desc}\n      -> {v}: {got['reason']}")
    print("---")
    if ok:
        print("SELFTEST PASS -- the paired-probe discriminator distinguishes a tier you can buy up to "
              "from a realm your key was never cut for. gen-181 saw one 401 and wrote 'paywalled'; this "
              "tool refuses that verdict from one probe and earns REALM_WALL from the pair.")
        return 0
    print("SELFTEST FAIL")
    return 1


def _live(url, key, method, body):
    import urllib.request, urllib.error
    probes = []

    def hit(label, credentialed):
        headers = {}
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = body.encode()
        if credentialed and key:
            headers["Authorization"] = f"Bearer {key}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return {"label": label, "status": r.status, "credentialed": credentialed,
                        "body": r.read(400)}
        except urllib.error.HTTPError as e:
            return {"label": label, "status": e.code, "credentialed": credentialed,
                    "body": e.read(400)}
        except Exception as e:
            return {"label": label, "status": 0, "credentialed": credentialed, "body": str(e)}

    probes.append(hit(f"{method} credentialed", True))
    probes.append(hit(f"{method} no-auth", False))
    result = classify(probes)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result["verdict"] != "AMBIGUOUS" else 2


def main():
    ap = argparse.ArgumentParser(description="Classify an endpoint refusal as TIER_WALL vs REALM_WALL (M-0795/M-0796).")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--schema", action="store_true")
    ap.add_argument("--live", metavar="URL")
    ap.add_argument("--key", default="")
    ap.add_argument("--method", default="POST")
    ap.add_argument("--json", dest="body", default=None, help="request body (JSON string)")
    a = ap.parse_args()
    if a.schema:
        print(json.dumps(SCHEMA, indent=2)); return 0
    if a.selftest:
        return _selftest()
    if a.live:
        return _live(a.live, a.key, a.method.upper(), a.body)
    ap.print_help(); return 0


if __name__ == "__main__":
    sys.exit(main())
