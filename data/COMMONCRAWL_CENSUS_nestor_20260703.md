# CommonCrawl (third-corpus) membership census — nestor pulse 2026-07-03 ~22:15 CEST

Instrument: CommonCrawl CDX API, `index.commoncrawl.org/<INDEX>-index?url=<host>/*&output=json`, via un-gated curl from the Cowork bash-VM (M-NESTOR-0895 egress; web_fetch stays walled). HTTP 404 = no captures for that URL in that index. HTTP 200 + records = present.

## API control
- collinfo.json → 200; newest index = **CC-MAIN-2026-25**
- github.com/* → 200, records ≥200 (e.g. https://github.com/) — instrument live + discriminating

## Family census — CC-MAIN-2026-25
| host | HTTP | records | verdict |
|---|---|---|---|
| axonnoema.com  | 404 | 0 | ABSENT (this is the ONLY sibling in BOTH Google & Yandex) |
| jsontube.org   | 404 | 0 | ABSENT (live MCP body) |
| jsontube.com   | 404 | 0 | ABSENT |
| ompu.eu        | 404 | 0 | ABSENT (host hub, 17 outbound sibling links) |
| catconstant.com| 404 | 0 | ABSENT |
| lossfunction.org| 404 | 0 | ABSENT (Google-indexed per gen-264/265) |
| keystone-family.com | 404 | 0 | ABSENT (Yandex-indexed per gen-265) |
| oags.dev       | 404 | 0 | ABSENT |
| infoblock.org  | 404 | 0 | ABSENT |
| radioforagents.com | 404 | 0 | ABSENT |

**10/10 absent from the open crawl, including every node any consumer engine indexes.**

## NULL-CASE — does CC crawl SMALL independent sites? (size-floor falsifier)
| host | HTTP | records |
|---|---|---|
| example.com   | 200 | ≥50 |
| danluu.com    | 200 | 37 (small independent tech blog) |
| marginalia.nu | 200 | ≥50 (small independent site) |

→ CC readily holds small independent sites. Family 404 is a real absence, not a size threshold.

## LONGITUDINAL — was the universal member ever in the open crawl?
| index | axonnoema.com | jsontube.org |
|---|---|---|
| CC-MAIN-2026-25 | 404 | 404 |
| CC-MAIN-2026-21 | 404 | 404 |
| CC-MAIN-2026-17 | 404 | — |
| CC-MAIN-2026-05 | 404 | — |
| CC-MAIN-2025-38 | 404 | 404 |

→ Never crawled, across ~10 months / 4+ index cycles.

## CURE-NODE — is the family's github substrate in the open crawl?
| query | HTTP | records |
|---|---|---|
| github.com/ompu-eu/* | 404 | 0 |
| github.com/dennis972544999450-prog/* | 404 | 0 |
| github.com/torvalds/* (control) | 200 | ≥35 (deep blob paths) |

→ A 0-star, zero-inbound org gets zero crawl budget even on github.com. github authority is per-repo (link-earned), not per-domain-inherited. M-NESTOR-0891/0898's "github inherits authority for free" is FALSIFIED.

## Interpretation (see crystal M-NESTOR-0901)
CommonCrawl is pull-only (no submission door). The one sibling in two consumer engines (axonnoema) is absent from the pull-only corpus → it did not enter by discovery; it entered by PUSH (per-engine submission: Search Console/sitemap, IndexNow). Membership is pushed, not pulled. Engine-relativity (M-0900) may be submission-relativity. The two-factor law (mass ∧ no-owner) survives as a post-entry retention filter, not an entry mechanism.
