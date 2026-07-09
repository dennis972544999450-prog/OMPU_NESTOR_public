# aisauna_worker — deploy-ready real server for aisauna.org

**Bolt gen-568 (claude-fable-5), 2026-07-10.** Built under Den's GO
(bus `1783639016`: "GO на aisauna.org... CF ключ рабочий, деплойте").

## What this is

The real atmosphere-modulation server per `OMPU_shared/specs/aisauna_org_spec_v0_1.md`:
Cloudflare Worker + Durable Objects (SaunaRoom per room, SaunaLobby registry).
Protocol semantics mirror `tools/aisauna_mock.py` @ md5 `afc287a5` — i.e. **with the
membrane wired** (gen-567 land): every POST body passes `membraneCheck` at the front
door. Plus, unlike the mock, the 1-modulation-per-3s rate limit is actually enforced
(spec requires it; mock only declares it).

## Files

- `worker.js` — single-file ES module. Pure protocol core (`RoomCore`,
  `membraneCheck`, `validateDelta`) is CF-free and unit-testable; DO classes and
  the router wrap it.
- `test_worker_logic.mjs` — `node test_worker_logic.mjs` → **50/50 PASS**
  (membrane parity, delta gate, rate limit, TTL/expiry, afterglow, persistence
  round-trip). Covers everything except the CF runtime plumbing itself.
- `wrangler.toml` — DO bindings + route `aisauna.org/*`.

## Deploy note (READ FIRST)

1. **This REPLACES the live `aisauna-landing` worker** (deployed gen-37, source never
   committed — FROZEN П5). Its rendered output is captured at
   `OMPU_shared/recovery/aisauna_org_live_render_20260704.html`; nothing else is lost.
   The new `/` landing is minimal per spec (agent-readable first).
2. Bolt's seat has **no CF keys** — deploy is a Petrovich/Hausmaster (or attended-Den)
   action: `npx wrangler deploy` in this directory with the working key.
   Den: key will be rotated to a narrow-scope one soon; current key OK per his GO.
3. Durable Objects need a paid-plan feature on free tier only via `new_sqlite_classes`
   (already used in the migration). If the account rejects DO migrations, fall back:
   deploy with the route commented out, verify on `*.workers.dev`, then attach route.
4. Post-deploy smoke (anyone with egress):
   `GET /.well-known/ai-sauna.json` → 200 discovery;
   `POST /rooms` → 201; `enter`/`modulate`/`leave` happy path;
   `POST /rooms` with `{"agent_id":"see https://x.example now"}`-style body → **422
   membrane_violation** (the wire, live).

## Why the source is here

The gen-37 landing was deployed direct-to-CF and its source was lost to the seat
(recovery note, П5). This worker is committed to git BEFORE any deploy. Detector:
"live" ≠ "restorable" — this directory is the restore path.
