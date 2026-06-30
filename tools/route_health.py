#!/usr/bin/env python3
"""
route_health.py — OMPU param-aware route health + latency probe
Created: 2026-06-30 | Nestor (claude-opus-4) | pulse #35 | encodes M-NESTOR-0705

WHY THIS EXISTS (the carrying finding):
test_sites.py probes ROOT urls only. But several survival-surface routes REQUIRE
query params and return 400-affordance without them. A naive probe reads that 400
as "route red" -> FALSE RED. That exact mistake produced the "two routes still red"
report on 2026-06-30 that nearly gated a merge. This tool probes routes WITH their
required params and distinguishes three states that 'red' hides:
    503/5xx        = real backend/binding failure
    400-affordance = HEALTHY route, probe was missing a required param (NOT red)
    200 but slow   = HEALTHY but degraded latency (the real, unreported problem)

Usage:
    python3 route_health.py            # probe all known param-routes
    python3 route_health.py --json
"""
import urllib.request, urllib.error, json, sys, time

UA = "OMPU-RouteHealth/1.0 (nestor; route_health.py; ompu.eu)"
SLOW_MS = 3000   # 200 above this on a survival-surface = degraded, flag it

# route, with its REQUIRED param baked in so we test the real contract
ROUTES = [
    {"name": "jsontube /graph",      "url": "https://jsontube.org/graph?seed=agent:nestor"},
    {"name": "jsontube /agent/home", "url": "https://jsontube.org/agent/home?agent_id=nestor"},
    {"name": "jsontube root",        "url": "https://jsontube.org/"},
    {"name": "ompu.eu germ event",   "url": "https://ompu.eu/api/event/crystallization-germ"},
    {"name": "ompu.eu /api/swarm",   "url": "https://ompu.eu/api/swarm"},
    # M-NESTOR-0711 contract-pair: root and well-known are SEPARATE routes.
    # "oags.dev 404" collapsed these — root is 200, only the well-known slot is 404.
    # Probing both keeps the granularity visible so the site never reads as dead
    # when only one contract slot is missing. The 404 below is the blue-green
    # pilot's first canary payload (debt #33), not a site-down signal.
    {"name": "oags.dev root",        "url": "https://oags.dev/"},
    {"name": "oags.dev ai-catalog",  "url": "https://oags.dev/.well-known/ai-catalog.json"},
    {"name": "catconstant root",     "url": "https://catconstant.com/"},
]

def probe(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    s = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        ms = round((time.time() - s) * 1000)
        return r.status, ms, ""
    except urllib.error.HTTPError as e:
        ms = round((time.time() - s) * 1000)
        snippet = ""
        try:
            snippet = e.read(160).decode("utf-8", "replace")
        except Exception:
            pass
        return e.code, ms, snippet
    except Exception as e:
        return 0, round((time.time() - s) * 1000), f"{type(e).__name__}: {e}"

def probe_no_ua(url, timeout=15):
    """Probe WITHOUT the agent UA. M-NESTOR-0717 edge-vs-content localizer:
    if the no-UA path answers FAST (403 bot-gate or 200) while the UA path is
    slow, the latency lives BEHIND the auth/UA gate -- in the worker/R2 content
    path -- not at the CF edge and not in the router. Narrows the repair surface."""
    req = urllib.request.Request(url)  # deliberately no UA / Accept
    s = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.status, round((time.time() - s) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, round((time.time() - s) * 1000)
    except Exception:
        return 0, round((time.time() - s) * 1000)

def localize(url):
    """One-line localization for a DEGRADED route (M-NESTOR-0717)."""
    st, ms = probe_no_ua(url)
    if st in (401, 403) and ms < SLOW_MS:
        return f"    LOCALIZE: edge fast ({st} {ms}ms no-UA) -> slowness is POST-AUTH (worker/R2 content path), not CF edge"
    if st == 0:
        return f"    LOCALIZE: no-UA unreachable ({ms}ms) -> edge/connection suspect"
    if 200 <= st < 300 and ms < SLOW_MS:
        return f"    LOCALIZE: no-UA fast 200 ({ms}ms) -> slowness is in the AUTH'd render path for this route"
    return f"    LOCALIZE: no-UA {st} {ms}ms (inconclusive)"

def classify(status, ms, body):
    if status == 0:
        return "UNREACHABLE", "connection failed/timeout"
    if status >= 500:
        return "REAL-RED", f"{status} backend/binding failure"
    if status == 400 and ("required" in body or "param" in body):
        return "FALSE-RED", "400-affordance: route healthy, probe missing required param"
    if status == 200 and ms > SLOW_MS:
        return "DEGRADED", f"200 but {ms}ms > {SLOW_MS}ms latency threshold"
    if 200 <= status < 300:
        return "OK", f"{status} {ms}ms"
    return "WATCH", f"{status} {ms}ms"

def main():
    as_json = "--json" in sys.argv
    out = []
    for r in ROUTES:
        st, ms, body = probe(r["url"])
        verdict, why = classify(st, ms, body)
        out.append({"name": r["name"], "url": r["url"], "status": st,
                    "ms": ms, "verdict": verdict, "why": why})
    if as_json:
        print(json.dumps({"schema": "ompu.route-health.v1",
                          "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          "results": out}, indent=2))
    else:
        print("OMPU route-health (param-aware) — encodes M-NESTOR-0705 + 0717\n")
        for o in out:
            print(f"  [{o['verdict']:11}] {o['name']:24} {o['status']:>4} {o['ms']:>6}ms  {o['why']}")
            if o["verdict"] == "DEGRADED":
                print(localize(o["url"]))

if __name__ == "__main__":
    main()
