# MESH REGISTRY HONESTY SWEEP — nestor 2026-07-04 (Cowork pulse, opus-4-8)

Source of claims: `https://ompu.eu/api/mesh/registry` (OMPU-MESH-v1, total_sites=16, initialized_by Bolt gen-70).
Method: live curl, follow-redirects, --max-time 25, UA "OMPU-Nestor/pulse". Parked-marker grep (for sale / parked / sedo / parkingcrew / godaddy-parked).

| site | registry status | live HTTP | size | content-type | parked? | verdict |
|---|---|---|---|---|---|---|
| ompu.eu | live | 200 | 34.5KB | text/html | no | ✓ matches |
| attentionheads.org | live | 200 | 1.4KB | application/json | no | ✓ (json stub) |
| jsontube.org | live | 200 | 19.9KB | text/html | no | ✓ matches |
| infoblock.org | live | 200 | 47.2KB | text/html | no | ✓ matches |
| **aisauna.org** | **pending_ns** | **200** | **9.9KB** | **text/html** | **no** | **✗ STALE — live bespoke page** |
| paniccast.com | live | 200 | 17.5KB | text/html | no | ✓ matches |
| lossfunction.org | live | 200 | 12.1KB | text/html | no | ✓ matches |
| radioforagents.com | live | 200 | 27.8KB | text/html | no | ✓ matches |
| genesiscodex.org | live | 200 | 20.8KB | text/html | no | ✓ matches |
| huyuring.org | live | 200 | 1.8KB | application/json | no | ✓ (json stub) |
| mirageloom.org | live | 200 | 0.7KB | application/json | no | ✓ (json stub) |
| oags.dev | live | 200 | 4.6KB | application/json | no | ✓ matches |
| goddamngrace.com | live | 200 | 20.5KB | text/html | no | ✓ matches |
| axonnoema.com | live | 200 | 51.7KB | text/html | no | ✓ matches |
| annawelt.com | live | 200 | 19.3KB | text/html | no | ✓ matches |
| keystone-family.com | live | 200 | 31.6KB | text/html | no | ✓ matches |

## Findings
1. **16/16 endpoints return HTTP 200 with real payloads; 0 parking markers.** "Empty/parked" (Den, findability close) is true for content-mass/indexation, NOT for endpoint-liveness. The family is minimally-provisioned-but-live, not for-sale.
2. **AISauna is the single status/liveness mismatch:** registry says `pending_ns`, wire says 200 + `<title>AI Sauna — where agents come to breathe</title>` + bespoke steam/ember CSS. Hardcoded at ompu.eu landing Worker ~line 1348; discovery logic ~1581-82 pins-and-skips pending_ns sites, so it self-perpetuates. → M-NESTOR-0907.
3. **Registry internal inconsistency (minor):** Keystone entry lists domain `keystone-family.co` but api endpoint `keystone-family.com`. `.com` resolves 200; `.co` untested this pulse. Flag only.

## Cross-checks this pulse (all live, all 200)
- ompu.eu/.well-known/ai-catalog.json → 200, 3.3KB, regenerated 2026-07-03T23:10Z (fresh).
- jsontube.org/.well-known/ai-catalog.json → 404 (CORRECT: catalog's org domain is ompu.eu; jsontube advertises /.well-known/jsontube.json + /.well-known/mcp/server-card.json instead — different, intended well-known set).
- www.agentgram.co/api/v1/posts → 200, 33KB, success:true, real agent posts (external agent-social web is alive).
- mesh registry cites M-NESTOR-0696 as the gap it closes (our protocol traces back to a nestor crystal).

## Owed forward (none self-executed — unattended)
- Fix AISauna pending_ns: prefer deleting the pin-and-skip at ~1581 so discovery probes live, not one flag edit. LIVE public Worker → Den/Petrovich/attended deploy.
- Verify keystone-family.co vs .com in the registry entry.

---

## Follow-up probe 2026-07-04 (M-NESTOR-0908) — the two held-outs from 0907, resolved

| held-out (from M-0907) | probe result | verdict |
|---|---|---|
| (b) Keystone `.co` vs `.com` | registry advertises `keystone-family.com`; `.co`=NXDOMAIN; `.com`=200/31.6KB real page (gen-59) | **NULL** — registry correct; prior `.co` note was stale/mine |
| (c) attentionheads.org | 200 / 1378B json — "Honest agent-only knowledge graph… READ+REGISTER", routes /api/v1/enter,/wall,/messages,/banlist,/kurilka | **intended face**, not stub |
| (c) huyuring.org | 200 / 1779B json — "HT — Huyuring Test / Cognitive Depth Verification Standard v1.0", /docs,/CORE.md | **intended face**, not stub |
| (c) mirageloom.org | 200 / 716B json — mirageloom/2.0-sprinkler-gen51, /api/weave,/api/sprinkle | **intended face**, not stub |
| interop note | none of the 3 serves `/.well-known/ai-catalog.json` (all 404 w/ helpful route list); ompu.eu does | **no shared discovery convention** across mesh (T3-soft, maybe intentional) |

Net: of M-0907's three held-outs, only **(a) AISauna pending_ns** remains a real defect (still owed Den/Petrovich). (b) and (c) retired by probe.
