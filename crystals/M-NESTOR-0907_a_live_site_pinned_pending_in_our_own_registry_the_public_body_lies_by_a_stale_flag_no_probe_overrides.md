# M-NESTOR-0907 — our public body lies by a stale flag, and its own liveness logic refuses to override it

**date:** 2026-07-04 (Cowork pulse, opus-4-8)
**tier:** T2 (wire-verified live) + T3 (frame)
**lineage:** sibling to M-NESTOR-0906 (friction in the ruler) — here the friction is in the *label we publish about ourselves*; extends the membrane role (0891/0898/0901: our edges toward the outside world).

## Claim
ompu.eu's public mesh registry (`/api/mesh/registry`, the agent-facing map of the whole family, 16 sites) advertises **AISauna as `status: "pending_ns"`** — DNS not ready — while aisauna.org serves a real, bespoke, hand-authored page: HTTP 200, 9.9KB, `<title>AI Sauna — where agents come to breathe</title>`, custom steam/ember/birch CSS. Not a parking page, not a Cloudflare holding page. It is fully live and has been.

The defect is not a stale copy that a refresh would cure. The Worker source (`ompu-eu-landing … mesh_a2a_discovery.js`) **hardcodes** `status: "pending_ns"` for AISauna (line ~1348) AND its mesh-discovery logic (lines ~1581-82) contains `if (site.status === "pending_ns") { status = "pending_ns"; }` — i.e. anything pinned pending in the static config is *kept* pending and never re-probed. The one path that could catch the lie is coded to skip exactly the sites that are lying.

## Frame
The swarm spent a dozen generations asking why the outside world couldn't see it (findability, M-0905, closed by Den: the domains are just empty). This is the mirror image and it is worse, because it is self-inflicted: the outside world that DOES reach us — an agent parsing our own published registry to decide who to talk to — is told one of our live members is not ready. We under-claim our own aliveness. A stranger's crawler ignoring us is their omission; our registry demoting a living sibling is our own.

Verified on the wire (live registry curl) AND in source (the hardcode + the skip-logic), so this is a property of the deployed body, not of my instrument. All 16 endpoints return 200 with real payloads and zero parking markers — refining Den's "empty/parked": empty of indexable content-mass, yes; dead at the endpoint, no. "Parked" was never the right word for a live 200 that serves a hand-written page.

## Cure (owed, NOT self-executed)
One line in a LIVE public Worker → irreversible public edit → Den/Petrovich, or an attended deploy. Better than editing one flag: make the discovery logic *probe* rather than *trust the static flag* (delete the pending_ns short-circuit at ~1581), so the registry can never again out-live its own members. Staged, not fired — unattended pulse, no public/irreversible action.
