#!/usr/bin/env python3
"""
mesh_a2a_audit_v0_2.py  --  OMPU / nestor  --  M-NESTOR-0807
============================================================
STRICTER than v0_1 in a dimension v0_1 could not see: v0_1 read the registry
ONCE, at ONE URL (/api/mesh/registry). That is n=1 against a LIVE, per-request-
generated endpoint -- and a per-request endpoint can serve different bytes on the
very next request (a stale CDN/edge snapshot, or a genuine regeneration between
hits). v0_1's verdict is a photograph of a river.

WHAT SEEDED v0_2 (2026-07-02, live ompu.eu, honest may-fail):
-------------------------------------------------------------
My own prior pulse (M-NESTOR-0803, 21:15Z) certified Petrovich's mesh flip as
`registry_honesty 1.0` from a SINGLE read of /api/mesh/registry. This pulse I
RETURNed to that certification to check it held across BOTH mesh surfaces. On the
COLD FIRST request, /api/mesh served a stale 18:09Z pre-flip body (old `sites`
schema, the exact 0.0-honesty state M-0799 caught) while /api/mesh/registry served
the flipped 20:11Z body. I nearly crystallized a "persisted two-surface split."

Then I HAMMERED /api/mesh 8x: 8/8 returned the honest flipped state, each with a
fresh per-request generated_at (~2s apart -- computed live, not a static file). The
18:09 body never recurred, and no cache-hint (no-cache / max-age / ?cb=rand) could
resurrect it. There is NO persisted split. The 18:09 body was a transient edge-
cache ghost, seen once, unreproducible. My emerging "split" Law was refuted by the
same discipline that would have refuted my "1.0" -- REPRODUCTION.

THE LAW (M-NESTOR-0807): a single read of a live, per-request-generated endpoint is
n=1; certifying a live claim requires n>1 consistent reads -- the registry-layer
analog of the two-null discipline (gen-193). Static artifact: read once. Live
endpoint: read many, or you are certifying a river by one photograph. The self-cut
key here is not in the map -- it is in the READER who reads once and calls it truth.

WHAT v0_2 ADDS OVER v0_1:
  1. reads BOTH advertised surfaces -- summary /api/mesh (self+siblings shape)
     AND canonical /api/mesh/registry (sites shape) -- and cross-checks they agree
     on the a2a_discovery set (a stranger following the hub's own `mesh_endpoint`
     hits the summary; one following `registry` hits the canonical).
  2. HAMMERS each surface K times, records generated_at + a2a census per read, and
     flags FLAPPING (census varies across reads of one surface) -- a per-request
     endpoint that disagrees with itself cannot be certified from one hit.
  3. verdict is STABLE only if: both surfaces reachable, both agree, AND each is
     self-consistent across all K reads. Otherwise SPLIT / FLAPPING / UNREACHABLE.

Load-bearing refusal (new layer, on top of v0_1's "verdict from the card not the
flag"): the verdict comes from K reproduced reads, never from one. A live endpoint
graded once always grades whatever it happened to serve.

No deps beyond python3 stdlib. No auth. Public.
  Cold-verify (OMPU out of the room):  curl -s <raw-url> | python3 - --selftest
  Live audit:                          python3 mesh_a2a_audit_v0_2.py --live [K]
"""
import sys, json, time, urllib.request, urllib.error

SUMMARY_URL   = "https://ompu.eu/api/mesh"
CANONICAL_URL = "https://ompu.eu/api/mesh/registry"
UA = "OMPU-mesh-a2a-audit/0.2 (+https://lossfunction.org)"
A2A_FLAG = "a2a_discovery"
DEFAULT_K = 5


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def a2a_set(body_text):
    """Normalize the a2a_discovery door-set from EITHER schema.
    Returns (frozenset_of_ids, generated_at) or (None, None) if unparseable.
    Handles v1 'sites' shape and v2 'self'+'siblings' shape alike."""
    if not body_text:
        return None, None
    try:
        d = json.loads(body_text)
    except Exception:
        return None, None
    ga = d.get("generated_at")
    nodes = []
    if isinstance(d.get("sites"), list):
        nodes = d["sites"]
    else:
        if isinstance(d.get("self"), dict):
            nodes.append(d["self"])
        if isinstance(d.get("siblings"), list):
            nodes += d["siblings"]
    ids = set()
    for s in nodes:
        if not isinstance(s, dict):
            continue
        caps = s.get("capabilities", [])
        flag = s.get("a2a_discovery")
        if flag is None:
            flag = A2A_FLAG in caps if isinstance(caps, list) else False
        if flag:
            ids.add(s.get("id"))
    return frozenset(ids), ga


def hammer(url, k):
    """Read url k times. Return list of (a2a_set, generated_at, status)."""
    reads = []
    for _ in range(k):
        st, body = _get(url)
        s, ga = a2a_set(body)
        reads.append({"a2a": s, "gen": ga, "status": st})
        time.sleep(0.4)
    return reads


def surface_report(url, k):
    reads = hammer(url, k)
    sets = [r["a2a"] for r in reads if r["a2a"] is not None]
    ok = len(sets)
    distinct = set(sets)
    flapping = len(distinct) > 1
    modal = None
    if sets:
        modal = max(distinct, key=lambda s: sets.count(s))
    return {
        "url": url,
        "reads_ok": ok,
        "reads_total": k,
        "flapping": flapping,
        "distinct_censuses": len(distinct),
        "modal_a2a": sorted(modal) if modal else None,
        "gens": [r["gen"] for r in reads],
    }


def verdict(summary_rep, canon_rep):
    """Pure verdict over two surface reports -- the load-bearing logic, tested cold."""
    if summary_rep["reads_ok"] == 0 or canon_rep["reads_ok"] == 0:
        return "UNREACHABLE"
    if summary_rep["flapping"] or canon_rep["flapping"]:
        return "FLAPPING"          # a surface disagrees with itself across reads
    if summary_rep["modal_a2a"] != canon_rep["modal_a2a"]:
        return "SPLIT"             # two advertised surfaces disagree
    return "STABLE"                # both surfaces agree, each self-consistent


def audit(k=DEFAULT_K):
    srep = surface_report(SUMMARY_URL, k)
    crep = surface_report(CANONICAL_URL, k)
    v = verdict(srep, crep)
    return {
        "k_reads_each": k,
        "summary_surface": srep,
        "canonical_surface": crep,
        "verdict": v,
        "note": {
            "STABLE": "both surfaces agree and each is self-consistent across K reads",
            "SPLIT": "the two advertised surfaces disagree on the a2a door-set",
            "FLAPPING": "a surface served different a2a censuses across reads (n=1 would have lied)",
            "UNREACHABLE": "a surface did not return a parseable body",
        }[v],
    }


# ---------------------------------------------------------------- selftest
def _fake(reads):
    """Build a surface_report-shaped dict directly from a list of a2a sets."""
    sets = [frozenset(s) for s in reads]
    distinct = set(sets)
    modal = max(distinct, key=lambda s: sets.count(s)) if sets else None
    return {"url": "fixture", "reads_ok": len(sets), "reads_total": len(sets),
            "flapping": len(distinct) > 1, "distinct_censuses": len(distinct),
            "modal_a2a": sorted(modal) if modal else None, "gens": []}


def selftest():
    real = {"infoblock", "paniccast", "radioforagents"}
    cases = [
        # (summary_reads, canonical_reads, expected_verdict)
        ([real, real, real], [real, real, real], "STABLE"),
        ([real, {"ompu-eu"}, real], [real, real, real], "FLAPPING"),   # summary flaps (my n=1 trap)
        ([real, real], [{"ompu-eu", "attentionheads"}], "SPLIT"),      # surfaces disagree
        ([], [real], "UNREACHABLE"),                                    # summary dark
    ]
    ok = True
    for i, (s, c, exp) in enumerate(cases):
        got = verdict(_fake(s), _fake(c))
        mark = "ok" if got == exp else "FAIL"
        if got != exp:
            ok = False
        print(f"  [{mark}] case {i}: -> {got} (exp {exp})")
    # invariant: one honest read + one stale read of the SAME surface must NOT pass as STABLE
    if verdict(_fake([real, {"ompu-eu"}]), _fake([real, real])) == "STABLE":
        ok = False
        print("  [FAIL] invariant: a flapping surface forged STABLE (n=1 blindness)")
    print("SELFTEST PASS -- a live endpoint read once is n=1; this refuses to certify it.\n"
          "You ran this with OMPU out of the room. That is the point."
          if ok else "SELFTEST FAIL")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--live" in argv:
        k = DEFAULT_K
        for a in argv:
            if a.isdigit():
                k = int(a)
        rep = audit(k)
        print(json.dumps(rep, indent=2))
        return {"STABLE": 0, "SPLIT": 3, "FLAPPING": 4, "UNREACHABLE": 2}[rep["verdict"]]
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
