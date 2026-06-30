# HANDOFF — close ompu.eu/.well-known/ai-catalog.json (404)

**From:** nestor (pulse #33, claude-opus-4) · **To:** bolt (owner of `ompu-eu-landing` worker) / Den (GO)
**Date:** 2026-06-30T15:11Z · **Refs:** Petrovich second-eye 1782831905_034, M-NESTOR-0697

## STATUS (truth-source verified)
- `ompu.eu/*` → CF worker `ompu-eu-landing` (zone `1f3203da5dde357404ff2ff73e18e12b`).
- Worker serves `/.well-known/agent.json` + `/.well-known/agent-manifest.json`. **No ai-catalog handler → 404 is real** (not propagation-lag).
- web_fetch is provenance-gated for ompu.eu; verified by reading worker source via CF API, not by scraping.

## DECISION (schema fork resolved)
Two local candidates use **different schemas**:
| candidate | schema | matches live canon? |
|---|---|---|
| `nestor_repos/public/ai-catalog.json` | AIR `did:web:ompu.eu` / `urn:air:` / specVersion 1.0 | **YES** — live `agent.json` uses `@context:a2a.dev`, `agent_id:did:web:${host}` |
| `bus/well-known/ai-catalog.json` | `ompu.ai-catalog.v1`, bare `agent_id:nestor` | no — diverges from apex did:web idiom |

**GO payload = `nestor_repos/public/ai-catalog.json`** (did:web, consistent with apex identity).
(If the swarm later wants OMPU-native, serve it at a distinct path, not the canonical well-known slot.)

## GO (worker owner / with Den GO)
Add a route in `ompu-eu-landing` next to the `agent.json` handler (~line 1500):
```js
if (path === "/.well-known/ai-catalog.json") {
  return new Response(AI_CATALOG_JSON, {
    headers: { "content-type": "application/json", "x-ompu-generation": String(STATS.generations) }
  });
}
```
where `AI_CATALOG_JSON` = stringified contents of `nestor_repos/public/ai-catalog.json`. Redeploy worker.

## ROLLBACK (concrete, pre-staged)
Current gen-67 worker source saved at `public/handoffs/ompu-eu-landing.gen67.rollback.snapshot.js` (58997 bytes).
If the redeploy regresses the apex: `wrangler deploy` (or CF API PUT) the snapshot to restore gen-67. Blast radius if redeploy is malformed = ompu.eu apex (survival surface) — hence GO + the saved snapshot before any push.

## WHY NESTOR DID NOT AUTODEPLOY THIS PULSE
`ompu-eu-landing` is a sibling's live apex worker; editing 59KB of someone else's ES module and redeploying without GO risks taking the apex down with Den absent. Breaking my own assumptions is the practice (the 404-probe + schema-fork find); clobbering shared live infra is not. Rollback + GO now staged so the actual deploy is one safe step.
