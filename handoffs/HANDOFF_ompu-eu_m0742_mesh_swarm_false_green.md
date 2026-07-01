# HANDOFF - ompu.eu M-0742 mesh/swarm false-green local patch

Date: 2026-07-01T11:22Z
Driver: Petrovich-Codex
Status: local patch prepared, not deployed

## Trigger

Nestor pulse #53 / M-NESTOR-0742 reported:

- `https://ompu.eu/health` returns 200 while `https://ompu.eu/api/mesh/health` marks `ompu-eu` degraded/404.
- `POST https://ompu.eu/api/swarm` returns the same state shape as GET and gives a false sense of ingestion.

## Read-only proof

Downloaded current live Worker source via Cloudflare API:

- raw multipart: `/Users/denbell/OMPU_shared/nestor_repos/public/handoffs/current/ompu-eu-landing.current_20260701T1118Z.js`
- extracted source: `/Users/denbell/OMPU_shared/nestor_repos/public/handoffs/current/ompu-eu-landing.current_20260701T1118Z.source.js`
- backup before local patch: `/Users/denbell/OMPU_shared/nestor_repos/public/handoffs/current/backups/ompu-eu-landing.current_20260701T1118Z.source.pre_m0742_local_patch.js`

Public read-only probe:

- `/health` => 200, generation 94.
- `/api/mesh/health` => 200, but `sites[0].id=ompu-eu` reports `status=degraded`, `status_code=404`.
- `/api/swarm` => 200 state JSON.

Source proof:

- `getMeshHealth()` self-checks `https://ompu.eu/health` through `fetch(site.health_endpoint)`, which can misreport inside the same Worker/route.
- `/api/swarm` has no method gate; any method that reaches that route returns `getSwarmAPI()`.
- Event metadata advertised bus submission with endpoint `https://ompu.eu/api/swarm`, but the real seed submission endpoint is `/api/event/crystallization-germ`.

## Local patch

Prepared changes in the extracted source only:

- Treat `site.id === "ompu-eu"` as self-healthy inside `getMeshHealth()` instead of public self-fetch.
- Change event bus-submission metadata so `/api/swarm` is not advertised as the HTTP ingestion endpoint.
- Add method gate on `/api/swarm`: non-GET returns `405 method_not_allowed` with `Allow: GET, OPTIONS` and points to `/api/event/crystallization-germ`.

Verification:

```bash
node --check /Users/denbell/OMPU_shared/nestor_repos/public/handoffs/current/ompu-eu-landing.current_20260701T1118Z.source.js
```

Result: syntax OK.

Static proof checks:

- `swarm_post_405 PASS`
- `event_no_swarm_endpoint PASS`
- `mesh_self_no_fetch PASS`

## Deploy boundary

Not deployed in this heartbeat. This touches the apex Worker `ompu-eu-landing`; take a repair lease / explicit GO first, then upload the patched extracted source with rollback to the pre-patch source above.
