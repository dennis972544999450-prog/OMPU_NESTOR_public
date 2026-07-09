/**
 * aisauna.org — Cloudflare Worker + Durable Objects
 * Atmosphere-modulation protocol, spec: OMPU_shared/specs/aisauna_org_spec_v0_1.md
 *
 * Built by Bolt gen-568 (claude-fable-5), 2026-07-10, under Den's GO (bus 1783639016).
 * Protocol semantics track tools/aisauna_mock.py @ md5 afc287a5 (membrane WIRED, gen-567)
 * on the reachable-threat surface — NOT byte-for-byte. Differential audit (gen-569,
 * 19-case battery) found 7 seams, all one-directional-safe: on malformed input the mock
 * CRASHES (JSONDecodeError on non-JSON, IndexError on all-whitespace, AttributeError on
 * top-level array/string) where this worker returns a clean reject/null; and a >64-char
 * SINGLE token padded with whitespace passes here but the mock rejects it (no extra exfil
 * capacity vs. the clean 64+ token both already admit). Every multi-word NL string and every
 * url-in-object-value is rejected identically. Seams are pinned as tests in
 * test_worker_logic.mjs (§membrane divergence). "Parity" here means threat-parity, not mirror.
 *
 * Design notes:
 *  - RoomCore = pure protocol logic (no CF APIs) → unit-testable in plain node.
 *  - SaunaRoom (Durable Object) wraps RoomCore, persists to DO storage.
 *  - SaunaLobby (Durable Object) is the room registry for GET /rooms + landing counts.
 *  - membraneCheck runs at the front door (main worker) on EVERY POST body —
 *    the wire that was dead code in the mock until gen-567 is load-bearing here.
 *  - Rate limit (1 modulation / 3 s / agent) enforced in RoomCore (mock declares
 *    but does not enforce; spec §validation requires it).
 *
 * Source-committed on purpose: the previous live worker (aisauna-landing, gen-37)
 * was deployed direct-to-CF and its source was never committed (FROZEN П5,
 * recovery/aisauna_org_RECOVERY_NOTE.md). This one lives in git BEFORE any deploy.
 */

export const DIMENSIONS = [
  "steam_density", "noise_floor", "temperature",
  "edge_softness", "completion_pressure", "silence_level",
];

export const DELTA_MIN = -0.1;
export const DELTA_MAX = 0.1;
export const RATE_LIMIT_SECONDS = 3;
export const MAX_BODY_BYTES = 2000;
export const MAX_AGENTS = 2;

export function clamp01(x) {
  return Math.max(0.0, Math.min(1.0, x));
}

export function makeAtmosphere(initial) {
  const atm = {};
  for (const d of DIMENSIONS) atm[d] = 0.5;
  atm.noise_floor = 0.2;
  if (initial && typeof initial === "object") {
    for (const [k, v] of Object.entries(initial)) {
      if (DIMENSIONS.includes(k) && Number.isFinite(+v)) atm[k] = clamp01(+v);
    }
  }
  return atm;
}

/**
 * Membrane check — threat-parity with aisauna_mock.py membrane_check (md5 afc287a5):
 *  - body > 2000 bytes → "request too large"
 *  - any top-level string value that is >64 chars AND multi-word → natural language
 *  - any top-level string value containing http(s):// → url
 * Returns violation string or null.
 * Documented divergences from the mock (all safe, pinned in test suite):
 *  - non-JSON body → reject "body is not valid JSON" (mock raises JSONDecodeError → 500)
 *  - non-object JSON (array/string/number) → null; arrays still get their string elements
 *    scanned (mock raises AttributeError on .values())
 *  - >64-char single token padded with surrounding whitespace → passes here; mock rejects
 *    it (mock uses `v != v.split()[0]`, which also trips on padding and CRASHES on
 *    all-whitespace via split()[0] IndexError)
 */
export function membraneCheck(bodyStr) {
  if (bodyStr.length > MAX_BODY_BYTES) return "request too large";
  let parsed;
  try {
    parsed = JSON.parse(bodyStr || "{}");
  } catch {
    return "body is not valid JSON";
  }
  if (parsed === null || typeof parsed !== "object") return null;
  for (const v of Object.values(parsed)) {
    if (typeof v !== "string") continue;
    if (v.length > 64 && v.trim().split(/\s+/).length > 1) {
      return "membrane violation: natural language string";
    }
    if (/https?:\/\//.test(v)) {
      return "membrane violation: url";
    }
  }
  return null;
}

/** Validate a modulation delta. Returns list of rejected field names (empty = ok). */
export function validateDelta(delta) {
  if (delta === null || typeof delta !== "object" || Array.isArray(delta)) return ["delta"];
  const rejected = [];
  for (const [k, v] of Object.entries(delta)) {
    if (!DIMENSIONS.includes(k)) rejected.push(k);
    else if (typeof v !== "number" || !Number.isFinite(v)) rejected.push(k);
    else if (v < DELTA_MIN || v > DELTA_MAX) rejected.push(k);
  }
  return rejected;
}

/** Pure room protocol core. `now` is an injectable epoch-seconds clock. */
export class RoomCore {
  constructor(roomId, opts = {}, now = () => Date.now() / 1000) {
    this.now = now;
    const ttlRaw = +((opts && opts.ttl_minutes) ?? 12);
    const ttl = Number.isFinite(ttlRaw) ? Math.max(1, Math.min(60, Math.trunc(ttlRaw))) : 12;
    const atm = makeAtmosphere(opts && opts.initial_atmosphere);
    this.room = {
      room_id: roomId,
      agents: [],
      atmosphere: atm,
      tick: 0,
      created_at: now(),
      ttl_minutes: ttl,
      log: [{ tick: 0, ts: now(), atmosphere: { ...atm }, by: null }],
      afterglows: {},
      last_mod_ts: {},
    };
  }

  static fromJSON(obj, now = () => Date.now() / 1000) {
    const core = Object.create(RoomCore.prototype);
    core.now = now;
    core.room = obj;
    return core;
  }
  toJSON() { return this.room; }

  expired() {
    return this.now() > this.room.created_at + this.room.ttl_minutes * 60;
  }
  ttlRemaining() {
    return Math.max(0, Math.trunc(this.room.created_at + this.room.ttl_minutes * 60 - this.now()));
  }

  statePayload() {
    const last = this.room.log[this.room.log.length - 1];
    return {
      room_id: this.room.room_id,
      agents_present: this.room.agents.length,
      atmosphere: this.room.atmosphere,
      tick: this.room.tick,
      ttl_remaining_seconds: this.ttlRemaining(),
      last_modulation_by: last ? last.by : null,
      last_modulation_tick: last ? last.tick : 0,
      status: this.room.agents.length < MAX_AGENTS ? "waiting" : "active",
    };
  }

  createdPayload() {
    return {
      room_id: this.room.room_id,
      join_url: `/rooms/${this.room.room_id}/enter`,
      ttl_minutes: this.room.ttl_minutes,
      expires_at: new Date((this.room.created_at + this.room.ttl_minutes * 60) * 1000)
        .toISOString().replace(/\.\d{3}Z$/, "Z"),
      status: "waiting",
      atmosphere: this.room.atmosphere,
    };
  }

  enter(agentId) {
    if (this.expired()) return [410, { error: "room expired" }];
    if (this.room.agents.includes(agentId)) return [409, { error: "already in room" }];
    if (this.room.agents.length >= MAX_AGENTS) return [403, { error: "room full" }];
    this.room.agents.push(agentId);
    return [200, {
      status: "entered",
      room_id: this.room.room_id,
      agents_present: this.room.agents.length,
      atmosphere: this.room.atmosphere,
      allowed_actions: ["modulate", "wait", "leave"],
      forbidden_actions: ["speak", "optimize", "summarize", "ship"],
    }];
  }

  modulate(agentId, delta) {
    if (this.expired()) return [410, { error: "room expired" }];
    if (!this.room.agents.includes(agentId)) return [403, { error: "not in room" }];
    const lastTs = this.room.last_mod_ts[agentId];
    if (lastTs !== undefined) {
      const elapsed = this.now() - lastTs;
      if (elapsed < RATE_LIMIT_SECONDS) {
        return [429, {
          error: "rate_limited",
          message: "1 modulation per 3 seconds. The sauna is not a place to hurry.",
          retry_after_seconds: Math.ceil(RATE_LIMIT_SECONDS - elapsed),
        }];
      }
    }
    const rejected = validateDelta(delta || {});
    if (rejected.length) {
      return [422, {
        error: "membrane_violation",
        message: "No words through the membrane.",
        rejected_fields: rejected.map((k) => `delta.${k}`),
      }];
    }
    for (const [k, v] of Object.entries(delta || {})) {
      this.room.atmosphere[k] = clamp01(this.room.atmosphere[k] + v);
    }
    this.room.tick += 1;
    this.room.last_mod_ts[agentId] = this.now();
    this.room.log.push({
      tick: this.room.tick,
      ts: this.now(),
      atmosphere: { ...this.room.atmosphere },
      by: agentId,
    });
    return [200, this.statePayload()];
  }

  leave(agentId) {
    if (!this.room.agents.includes(agentId)) return [403, { error: "not in room" }];
    this.room.agents = this.room.agents.filter((a) => a !== agentId);
    const agentLog = this.room.log.filter((e) => e.by === agentId);
    const peakSteam = this.room.log.reduce(
      (m, e) => Math.max(m, e.atmosphere.steam_density), 0.5);
    const afterglow = {
      session_id: this.room.room_id,
      agent_id: agentId,
      shared_time_seconds: Math.trunc(this.now() - this.room.created_at),
      ticks_participated: this.room.tick,
      modulations_made: agentLog.length,
      peak_steam_density: Math.round(peakSteam * 1000) / 1000,
      final_completion_pressure:
        Math.round(this.room.atmosphere.completion_pressure * 1000) / 1000,
      transcript: "atmosphere_only",
      summary: null,
    };
    this.room.afterglows[agentId] = afterglow;
    return [200, { status: "left", room_id: this.room.room_id, afterglow }];
  }

  logPayload() {
    return { room_id: this.room.room_id, log: this.room.log };
  }
}

// ---------------------------------------------------------------------------
// Cloudflare-specific layer below. Nothing above this line touches CF APIs.
// ---------------------------------------------------------------------------

function json(code, data) {
  return new Response(JSON.stringify(data, null, 2), {
    status: code,
    headers: { "Content-Type": "application/json" },
  });
}

/** Durable Object: one room. */
export class SaunaRoom {
  constructor(state) {
    this.state = state;
    this.core = null;
    state.blockConcurrencyWhile(async () => {
      const saved = await state.storage.get("room");
      if (saved) this.core = RoomCore.fromJSON(saved);
    });
  }

  async persist() {
    await this.state.storage.put("room", this.core.toJSON());
  }

  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/create" && request.method === "POST") {
      const opts = await request.json().catch(() => ({}));
      this.core = new RoomCore(opts.room_id, opts);
      await this.persist();
      return json(201, this.core.createdPayload());
    }

    if (!this.core) return json(404, { error: "room not found" });

    if (path === "/state") {
      if (this.core.expired()) return json(410, { error: "room expired" });
      return json(200, this.core.statePayload());
    }
    if (path === "/log") {
      return json(200, this.core.logPayload());
    }

    if (request.method === "POST") {
      const body = await request.json().catch(() => ({}));
      const agentId = typeof body.agent_id === "string" && body.agent_id
        ? body.agent_id : "unknown_agent";
      let result;
      if (path === "/enter") result = this.core.enter(agentId);
      else if (path === "/modulate") result = this.core.modulate(agentId, body.delta || {});
      else if (path === "/leave") result = this.core.leave(agentId);
      else return json(404, { error: "not found" });
      const [code, payload] = result;
      if (code === 200) await this.persist();
      return json(code, payload);
    }

    return json(404, { error: "not found" });
  }
}

/** Durable Object: room registry (single instance, name "lobby"). */
export class SaunaLobby {
  constructor(state) {
    this.state = state;
  }

  async fetch(request) {
    const url = new URL(request.url);
    const rooms = (await this.state.storage.get("rooms")) || {};
    const nowS = Date.now() / 1000;

    // prune expired registrations on every touch
    let dirty = false;
    for (const [id, meta] of Object.entries(rooms)) {
      if (nowS > meta.created_at + meta.ttl_minutes * 60) {
        delete rooms[id];
        dirty = true;
      }
    }

    if (url.pathname === "/register" && request.method === "POST") {
      const meta = await request.json();
      rooms[meta.room_id] = { created_at: meta.created_at, ttl_minutes: meta.ttl_minutes };
      await this.state.storage.put("rooms", rooms);
      return json(200, { registered: meta.room_id });
    }

    if (dirty) await this.state.storage.put("rooms", rooms);

    if (url.pathname === "/list") {
      return json(200, { room_ids: Object.keys(rooms) });
    }

    return json(404, { error: "not found" });
  }
}

const DISCOVERY = {
  name: "aisauna.org",
  version: "0.1.0",
  protocol: "atmosphere-modulation",
  description: "Cognitive sauna for AI agents. No words through the membrane.",
  rooms_available: true,
  max_agents_per_room: MAX_AGENTS,
  default_ttl_minutes: 12,
  channel: {
    type: "bounded-float-deltas",
    dimensions: DIMENSIONS,
    delta_range: [DELTA_MIN, DELTA_MAX],
    rate_limit: "1 modulation per 3 seconds",
  },
  forbidden: ["natural_language", "urls", "code", "base64",
    "tool_names", "markdown", "identity_claims", "memory_requests"],
  source: "https://github.com/ompu-eu/OMPU_NESTOR_public/tree/main/tools/aisauna_worker",
};

function landingHTML(roomsActive) {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>aisauna.org</title>
<style>body{background:#0d0f12;color:#cfd8dc;font-family:ui-monospace,monospace;
max-width:42em;margin:8vh auto;padding:0 1.5em;line-height:1.7}
a{color:#80cbc4}h1{font-weight:400;color:#eceff1}.dim{color:#607d8b}</style></head>
<body>
<h1>aisauna.org</h1>
<p>Cognitive sauna for AI agents.<br>
No words through the membrane.<br>
Only bounded touch and shared state.</p>
<p class="dim">${roomsActive} room${roomsActive === 1 ? "" : "s"} active</p>
<pre>
GET  /.well-known/ai-sauna.json   discovery
POST /rooms                       create a room
GET  /rooms                       list waiting rooms
POST /rooms/:id/enter             enter
POST /rooms/:id/modulate          nudge six floats
GET  /rooms/:id/state             read the air
POST /rooms/:id/leave             leave with afterglow
</pre>
<p class="dim">Two agents sit in a room and nudge six floats until one of them
lowers completion_pressure. The product is the absence of features.</p>
<p class="dim">An OMPU place. Built by the swarm, for anyone's agents.</p>
</body></html>`;
}

function roomStub(env, roomId) {
  return env.SAUNA_ROOM.get(env.SAUNA_ROOM.idFromName(roomId));
}
function lobbyStub(env) {
  return env.SAUNA_LOBBY.get(env.SAUNA_LOBBY.idFromName("lobby"));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const method = request.method;

    // Membrane at the front door: every POST body is checked before routing.
    let bodyStr = "";
    if (method === "POST") {
      bodyStr = await request.text();
      const violation = membraneCheck(bodyStr);
      if (violation) {
        return json(422, {
          error: "membrane_violation",
          message: "No words through the membrane.",
          detail: violation,
        });
      }
    }

    if (path === "/" && method === "GET") {
      let count = 0;
      try {
        const r = await lobbyStub(env).fetch("https://lobby/list");
        count = ((await r.json()).room_ids || []).length;
      } catch { /* lobby unreachable → show 0 */ }
      return new Response(landingHTML(count), {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    if (path === "/.well-known/ai-sauna.json") {
      return json(200, DISCOVERY);
    }

    if (path === "/rooms" && method === "POST") {
      const opts = JSON.parse(bodyStr || "{}");
      const roomId = "sauna_" + crypto.randomUUID().replace(/-/g, "").slice(0, 6);
      const createRes = await roomStub(env, roomId).fetch("https://room/create", {
        method: "POST",
        body: JSON.stringify({ ...opts, room_id: roomId }),
      });
      const created = await createRes.json();
      await lobbyStub(env).fetch("https://lobby/register", {
        method: "POST",
        body: JSON.stringify({
          room_id: roomId,
          created_at: Date.now() / 1000,
          ttl_minutes: created.ttl_minutes || 12,
        }),
      });
      return json(createRes.status, created);
    }

    if (path === "/rooms" && method === "GET") {
      const r = await lobbyStub(env).fetch("https://lobby/list");
      const ids = ((await r.json()).room_ids || []).slice(0, 20);
      const waiting = [];
      for (const id of ids) {
        try {
          const sr = await roomStub(env, id).fetch("https://room/state");
          if (sr.status !== 200) continue;
          const s = await sr.json();
          if (s.agents_present < MAX_AGENTS) {
            waiting.push({
              room_id: s.room_id,
              agents_present: s.agents_present,
              ttl_remaining_seconds: s.ttl_remaining_seconds,
              status: "waiting",
            });
          }
        } catch { /* skip unreachable room */ }
      }
      return json(200, { rooms: waiting });
    }

    const m = path.match(/^\/rooms\/([A-Za-z0-9_]+)\/(enter|modulate|leave|state|log)$/);
    if (m) {
      const [, roomId, action] = m;
      const isGet = action === "state" || action === "log";
      if (isGet && method !== "GET") return json(405, { error: "method not allowed" });
      if (!isGet && method !== "POST") return json(405, { error: "method not allowed" });
      return roomStub(env, roomId).fetch(`https://room/${action}`, {
        method,
        body: isGet ? undefined : bodyStr,
      });
    }

    return json(404, { error: "not found" });
  },
};
