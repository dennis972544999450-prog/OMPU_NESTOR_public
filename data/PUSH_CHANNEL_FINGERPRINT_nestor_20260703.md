# Push-channel fingerprint census — nestor pulse 2026-07-03 ~23:15 CEST
Instrument: un-gated curl (M-0895 egress) — direct-host HTML head, robots.txt, HTTP headers; dig TXT/NS; registry RDAP JSON. Consumer SERPs (Bing/DDG) attempted and FOUND BOT-WALLED (Bing JS-shell / DDG HTTP 202 incl. controls) → third-engine census deferred to tool layer.

## Verification + sitemap + hosting fingerprint (all 6 diagnostic hosts)
| host | membership(prior) | google-verif meta | bing msvalidate | yandex-verif | sitemap-in-robots | Server | on CF NS |
|---|---|---|---|---|---|---|---|
| axonnoema.com | Google+Yandex IN | none | none | none | none | cloudflare | yes |
| lossfunction.org | Google-only IN | none | none | none | none | cloudflare | yes |
| keystone-family.com | Yandex-only IN | none | none | none | none | cloudflare | yes |
| goddamngrace.com | Yandex-only IN | none | none | none | none | cloudflare | yes |
| genesiscodex.org | DARK both | none | none | none | none | cloudflare | yes |
| jsontube.org | DARK both | none | none | none | Sitemap: https://jsontube.org/sitemap.xml | cloudflare | yes |

→ No verification tag on any host. Only host with a declared sitemap is DARK. IN/dark share Cloudflare hosting+NS.

## DNS TXT (webmaster verification via DNS method)
All 6 hosts: totalTXT = 0. No google-site-verification, no yandex-verification, no IndexNow, on any host. NS = *.ns.cloudflare.com (hera / johnathan shared across IN and dark).

## RDAP registration age
| host | membership | registered | note |
|---|---|---|---|
| axonnoema.com | G+Y-IN | 2025-07-19 | oldest |
| keystone-family.com | Y-IN | 2025-07-20 | |
| goddamngrace.com | Y-IN | 2025-08-09 | age-matched to genesiscodex (opposite verdict) |
| genesiscodex.org | DARK | 2025-08-12 | 3 days from goddamngrace, dark |
| lossfunction.org | Google-IN | 2026-05-21 | YOUNGEST of all, yet indexed |
| jsontube.org | DARK | 2026-05-14 | same week as lossfunction, dark |

→ Age FALSIFIED: youngest domain is indexed; two age-matched pairs split opposite.

## Conclusion (crystal M-NESTOR-0904)
Every wire-observable push candidate (links, open-crawl, sitemap, verification meta/DNS, age, hosting) is falsified. The push channel is account-side only (Search Console request-index / Cloudflare Crawler-Hints IndexNow toggle) — nameable only with owner access. Next step is Den opening two dashboards, not another external probe.
