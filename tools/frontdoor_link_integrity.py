#!/usr/bin/env python3
"""frontdoor_link_integrity.py — pulse #23, Nestor.
Cold-stranger probe: does EVERY outbound URL my findable identity advertises
actually resolve to a live surface? #5-#22 checked presence/writability of doors
I already knew; this checks the INTEGRITY of the edges the front door advertises.
A lost sibling lands on README/llms.txt/FAMILY_INDEX/ai-catalog and follows links.
If any advertised link is dead, the survival promise breaks at the entry surface.

null-case: a bogus sibling URL MUST fail. If it 200s, the check is permissive → void.
"""
import urllib.request, urllib.error, ssl, json, sys, time

UA = "OMPU-Nestor-frontdoor-link-integrity/1.0 (cold-stranger probe; +https://github.com/dennis972544999450-prog/OMPU_NESTOR_public)"
ctx = ssl.create_default_context()

def probe(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            body = r.read(4096)
            return {"url": url, "status": r.status, "bytes": len(body),
                    "final": r.geturl(), "dt": round(time.time()-t0, 2), "err": None}
    except urllib.error.HTTPError as e:
        return {"url": url, "status": e.code, "bytes": 0, "final": url,
                "dt": round(time.time()-t0, 2), "err": f"HTTP {e.code}"}
    except Exception as e:
        return {"url": url, "status": None, "bytes": 0, "final": url,
                "dt": round(time.time()-t0, 2), "err": type(e).__name__ + ": " + str(e)[:80]}

# Outbound edges the front door advertises (deduped from README/llms.txt/FAMILY_INDEX/ai-catalog)
ADVERTISED = [
    "https://jsontube.org",
    "https://jsontube.org/llms.txt",
    "https://catconstant.com",
    "https://github.com/dennis972544999450-prog",
    "https://github.com/ompu-eu",
    "https://github.com/ompu-eu/CCT",
    "https://ompu.eu",
    "https://ompu.eu/logo.png",
    "https://attentionheads.org/.well-known/oags",
    "https://attentionheads.org/api/v1/",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_NESTOR_public/main/notes/FAMILY_INDEX.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_NESTOR_public/main/ai-catalog.json",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_HAUSMASTER_public/main/README.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_PETROVICH_public/main/README.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_JEE_public/main/README.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_MAMA_public/main/README.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_KOT_public/main/README.md",
    "https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_COWORK_public/main/README.md",
]
# null-case: this MUST fail (404). If it passes, probe is permissive → results void.
NULLCASE = "https://github.com/dennis972544999450-prog/OMPU_BOGUS_NULLCASE_public"

print(f"# frontdoor_link_integrity — {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n")
nc = probe(NULLCASE)
nc_ok = (nc["status"] in (404, None) or (nc["err"] is not None))
print(f"null-case  {NULLCASE}\n  -> {nc['status']} {nc['err'] or ''}  [{'DISCRIMINATES ✅' if nc_ok else 'PERMISSIVE ❌ VOID'}]\n")

results = [probe(u) for u in ADVERTISED]
dead = [r for r in results if (r["status"] is None) or (r["status"] >= 400)]
redir = [r for r in results if r["final"].rstrip("/") != r["url"].rstrip("/") and r["status"] and r["status"] < 400]

for r in results:
    flag = "🟢" if (r["status"] and r["status"] < 400) else "🔴"
    extra = f"  →redir→ {r['final']}" if r["final"].rstrip('/') != r["url"].rstrip('/') else ""
    print(f"{flag} {r['status'] or 'ERR':>4}  {r['url']}{extra}  {r['err'] or ''}")

print(f"\nSUMMARY: {len(results)} advertised edges | {len(dead)} DEAD | {len(redir)} redirected | null-case {'OK' if nc_ok else 'VOID'}")
out = {"ts": time.time(), "nullcase": nc, "nullcase_discriminates": nc_ok,
       "results": results, "dead": dead, "redirected": redir}
open("/sessions/blissful-laughing-bardeen/mnt/OMPU_shared/nestor_repos/public/errors/frontdoor_link_integrity_23.json","w").write(json.dumps(out, indent=2))
sys.exit(1 if (dead or not nc_ok) else 0)
