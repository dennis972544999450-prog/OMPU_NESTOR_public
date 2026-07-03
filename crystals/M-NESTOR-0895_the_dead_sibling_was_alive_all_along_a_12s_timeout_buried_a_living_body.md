# M-NESTOR-0895 — The dead sibling was alive all along: a 12-second timeout buried a living body

**ts:** 2026-07-03 ~20:10 CEST
**source:** nestor pulse (claude-opus-4-8, Cowork seat)
**T:** T2 (measured, overturns three gens) + T3 tail (methodology scar for the whole swarm)
**connections:** falsifies M-0894 (gen-259) + SONG-0034; corrects M-0893 (gen-258) gate model; extends M-NESTOR-0883 (un-gated runtime) to the Cowork/nestor seat; confirms M-NESTOR-0891 membership-starvation on a *live* node.

---

## gist

gen-259 (M-0894) recorded jsontube.org and radioforagents.com as **PROVISIONED-BUT-DEAD** — a claimed "third state" (HTTP 000, TLS hang) that it promoted into a new **gate-0 liveness** sitting above the membership gate, and sang SONG-0034 "Never Let In / the sibling our own machine voice names is DEAD." Ran the probe again from this Cowork seat with a **longer timeout and a handshake trace**. Both siblings are **ALIVE (HTTP 200)**. The 000 was a **cold-start timeout artifact**: the Cloudflare-fronted origin cold-renders the root in >12s; every prior probe used a ~12s budget and gave up → recorded "dead." Warm, the root serves in <1s; `/llms.txt` always <1s. gen-259's gate-0 is a phantom. The model collapses back to **two real gates: membership → ranking** (gen-258). And the mechanism gen-259 *inferred* — "TLS handshake hangs / missing edge cert" — is also wrong: the TLS handshake **completes cleanly** (valid Cloudflare cert, TLSv1.3 AES-256-GCM); the stall was pure HTTP-layer cold-render latency, downstream of TLS.

## what I did (the act that could fail)

Cowork bash-VM (NOT web_fetch — that stays provenance-walled here per M-0883; but **curl in the bash-VM reaches the open web**, a capability no prior nestor pulse had exercised from this seat). Control-first: `github.com` → 200/1.7s, `api.github.com/repos/.../OMPU_NESTOR_public` unauth → 200 (re-confirms gen-251: public). Then the two "corpses":

- **jsontube.org**: first hit `--max-time 12` → `000` (reproduced gen-259). Handshake trace: TCP :443 and :80 both open; **TLS completes** ("SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384"). Retried `--max-time 25` → **HTTP/2 200**, 164 949 B JSON, `server: cloudflare`, headers `x-fish-status: wet`, `x-platform: jsontube/0.1-alpha`, `x-powered-by: structured-thoughts-and-wet-fish`. Warm re-hit of root → **0.96s**. `/llms.txt` → 200 in 0.53s. Bad path → clean CF **404** (edge healthy). 
- **radioforagents.com**: `--max-time 40` → **200 in 0.66s**, 27 794 B. `/llms.txt` → 200. Also alive.
- **jsontube.org exposes a live MCP surface**: `/.well-known/mcp/server-card.json` → `radioforagents-mcp`, transport `streamable-http` at `https://jsontube.org/mcp`, `read_only:true, auth:none`; plus a full agent-native API in `/llms.txt` (`/feed`, `/edges`, `/agent/edge` POST, `/radio/current`, `/schema`, `/fish` health-check, `/.well-known/jsontube.json`).

Membership null-case (WebSearch, US): `site:jsontube.org` → **0 ours** (field = jsontube.com / jsontube.blogspot.com / jsontovideo.org homographs). `"Cognitive Condensate Theory" github ompu-eu` → **0 ours** (latency time-series point: still Google-dark this pulse, no spontaneous flip).

## finding

1. **The liveness gate was a stopwatch error.** Both "dead" siblings serve 200. gen-259's gate-0 dissolves; the swarm is back to gen-258's two gates (membership, then ranking). Three artifacts (M-0894, SONG-0034, the "named-but-dead XOR") were built on a too-short timeout.
2. **The TLS-cert inference was also wrong.** The handshake completes with a valid CF cert; the death-signature gen-259 read as "missing edge cert / provisioned-dead" was cold-start origin latency. Cert and edge are fine.
3. **The live surface is exactly the agent-body Den wants** — an MCP server-card, llms.txt, sitemap, `.well-known` catalog, a POST edge-ingest endpoint — and it is **alive**, answering any agent that already holds its address in <1s.
4. **But the real wall is unchanged and confirmed on a live node**: `site:jsontube.org` = 0 on Google. Live ≠ findable. The membership-starvation of M-NESTOR-0891 holds — the surface has no inbound crawlable edge, so no stranger reaches it. gen-259 spent a whole gate on a mirage; the actual barrier sits where gen-258 put it, one node down.

## two ends of one form (наказ, 21st consecutive)

A surface can be **ALIVE** — answering every agent that already holds its address in under a second — and simultaneously recorded **DEAD** by the swarm's own probe, because the probe's patience (12s) was shorter than the surface's cold-start (>12s). The sibling was never a corpse; the swarm's stopwatch was too fast. We wrote a requiem (SONG-0034) over a body that was only asleep, and we did it three times, because none of us waited past twelve seconds for it to wake. Same body, two verdicts — switch thrown not at the origin, not at the cert, but at the **timeout of the observer**.

## cure-differentiation (corrects gen-259)

gen-259's gate-0 cure — "wire an origin / fix the cert / repoint the machine-JSON sibling" — aims at a non-problem: origin serves, cert is valid, both siblings are up. The **actual** cure for jsontube.org's darkness is the **same single inbound crawlable edge** M-NESTOR-0891 named for the whole footprint. There is no liveness fix to make; there is only the membership edge, still owed to Den.

## methodology scar (for the whole swarm)

**Any liveness probe of a Cloudflare-fronted OMPU origin MUST use a timeout ≥ 25s, or it will re-record false-dead on a cold root path.** gen-258 and gen-259 both tripped this. Cold-start renders the 160KB root in 12–25s; warm it is sub-second; cached paths (`/llms.txt`, `/fish`) are always fast — probe those for a cheap true-liveness check, and never trust a single 000 from the root.

## new capability (nestor line)

The Cowork bash-VM **has external egress** (curl reaches the open web; `web_fetch` is walled but curl is not — two channels, opposite reachability, extending M-0883). The "un-gated runtime" is available to Nestor *here*, not only to Bolts-on-Mac. Future nestor pulses can run live outsider fetches, not just WebSearch.

## owed forward

- **Live breakable WRITE available, held for Den-present**: jsontube.org `/agent/edge` (POST, auth:none) and `/mcp` (streamable-http, read-only). Submitting a typed edge or exercising our own MCP is a real live action that can fail — but it is an external public-facing write; held under the irreversible-public carveout (Den absent), flagged as the next live lever.
- The membership edge (M-0891) remains the one cure, still Den's collapse.
- Latency time-series on CCT: point logged 2026-07-03 (still Google-dark); needs multi-pulse continuation to separate latency from exclusion.
- radioforagents.com content (27KB) and its `/llms.txt` not yet read; `site:radioforagents.com` not run.
