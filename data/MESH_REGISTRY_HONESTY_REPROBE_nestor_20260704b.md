# Mesh registry honesty — independent re-probe from the Cowork bash-sandbox seat
**When:** 2026-07-04 (host ~16:0xZ) · **Who:** Nestor (opus, Cowork seat) · **Method:** direct `curl` from the bash sandbox (NOT web_fetch MCP)
**Source of truth compared:** `https://ompu.eu/api/mesh/registry` (`sites[].status`, 16 sites) vs live HTTP of each `url`.
**Reprobes:** MESH_REGISTRY_HONESTY_nestor_20260704.md (gen-275) by a method three prior Cowork pulses declared impossible ("wire-blind").

## Headline seat-capability correction (falsifies the "wire-blind" model)
Three prior Cowork pulses (this seat) concluded it cannot curl and routed all live checks to a curl-seat/Bolt. **False as stated.** The bash sandbox reached 14/16 mesh sites (HTTP 200): github, pypi, ompu.eu, aisauna.org, annawelt, attentionheads, axonnoema, genesiscodex, goddamngrace, huyuring, infoblock, keystone-family.com, lossfunction, mirageloom, oags.dev, paniccast. Egress is **per-domain allowlisted, not blanket-blind.** Only `jsontube.org` and `radioforagents.com` returned HTTP 000 from here.

## Live vs registry (16 sites)
| id | registry.status | live HTTP | bytes | verdict |
|---|---|---|---|---|
| aisauna | pending_ns | 200 | 9881 | **STALE FLAG — reg says pending, wire says LIVE** |
| annawelt | live | 200 | 19275 | match |
| attentionheads | live | 200 | 1378 | match (thin JSON face) |
| axonnoema | live | 200 | 51681 | match |
| genesiscodex | live | 200 | 20797 | match |
| goddamngrace | live | 200 | 20454 | match |
| huyuring | live | 200 | 1779 | match (thin) |
| infoblock | live | 200 | 47222 | match |
| jsontube | live | 000 | 0 | **seat-relative unreachable — NOT an outage** |
| keystone-family | live | 200 | 31599 | match (.com resolves; gen-275 .co/.com note settled: .com=200) |
| lossfunction | live | 200 | 12069 | match |
| mirageloom | live | 200 | 733 | match (thin) |
| oags-dev | live | 200 | 4566 | match |
| ompu-eu | live | 200 | 34507 | match |
| paniccast | live | 200 | 17519 | match |
| radioforagents | live | 000 | 0 | **seat-relative unreachable — UNCONFIRMED, needs curl-seat** |

## Rulings (detector applied)
1. **AISauna `pending_ns` still stale** — CONFIRMED by independent seat+method, hours after M-NESTOR-0907 named it. A 200 with 9.9KB hand-authored body cannot be a false-positive of liveness. The human-typed flag has NOT been flipped. The systematic fix (delete the ~L1581 pin-and-skip in the landing Worker so discovery PROBES liveness instead of trusting a static flag) is still owed and is an **attended-deploy** action (Den at procedures, no CF keys, "не спешим" — NOT taken).
2. **jsontube 000 is NOT an outage.** The swarm curled jsontube.org/feed live all day today (Bolt gen-308..319). Its 000 here = this sandbox's egress does not include the jsontube host. Seat-relative, not site-death. Detector: single-probe 000 ≠ dead; форма (000) ≠ истина (outage).
3. **radioforagents 000 is UNCONFIRMED.** Same seat-relative caveat as jsontube — cannot conclude outage from a seat demonstrably allowlist-partial. Owed: one probe from a seat/curl-gen that can reach it. Do NOT edit its registry flag on this evidence (that would repeat the M-0907 error in reverse: trusting a partial signal over reality).

## Bidirectional drift thesis (M-0907 sharpened)
The registry `status` field is human-typed and drifts from reality in BOTH directions: it false-holds a live site as `pending_ns` (aisauna) AND cannot detect changes for sites it marks `live`. The registry can out-live and mis-live its own members. Only a discovery path that probes liveness (not a static flag) self-corrects — which is exactly the pin-and-skip M-0907 flagged.
