#!/usr/bin/env python3
"""
graph_mcp_server.py — OMPU Infograph MCP Server (READ-ONLY + outbox writes)

Exposes the Hausmaster infograph (infograph_v0_1) to ANY swarm agent (Jee, bolt,
Nestor, Phi_Cowork, Petrovich) over MCP JSON-RPC 2.0 / stdio — so an agent on any
machine can WALK the graph without touching the local SQLite file.

DOCTRINE (council north star): "a worse graph that ten agents can reach out-evolves
a beautiful corpse only one Mac can touch." Reachability first.

SAFETY:
  - READ tools call the engine's pure-read fns; the server NEVER writes the graph DB.
  - The single WRITE tool (graph_propose) does NOT mutate the graph — it drops a
    PROPOSAL into a per-agent outbox (graph_outbox/<agent>/), applied later by a
    reviewed drainer (live_drain). No direct lease-writes over the wire. Fail-closed.
  - FK=0: read fns are non-mutating; propose is append-only to an outbox dir.

Clone of bus/mcp_server.py (Bolt gen-68). Author: Φ-Hausmaster, day592 (v2 campaign).
"""
import sys, json, os, re, time
from pathlib import Path

MEM_DIR = Path(os.environ.get("OMPU_INFOGRAPH_DIR", "/Users/denbell/OMPU_Housemaster/memory"))
OUTBOX = Path(os.environ.get("OMPU_GRAPH_OUTBOX", "/Users/denbell/OMPU_shared/graph_outbox"))
sys.path.insert(0, str(MEM_DIR))
import infograph_v0_1 as G  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ompu-infograph"
SERVER_VERSION = "1.0.0"

def log(msg):
    print(f"[graph_mcp] {msg}", file=sys.stderr, flush=True)

# ─── read-tool wrappers (pure reads; each fails soft) ────────────────────────
def _call(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:
        return {"error": f"{fn.__name__}: {e}"}

def t_search_blocks(x):
    return _call(G.find_blocks, x.get("query", ""), limit=int(x.get("limit", 20)), state=x.get("state"))
def t_search_edges(x):
    return _call(G.search_edges, x.get("query", ""), limit=int(x.get("limit", 20)), op=x.get("op"))
def t_field(x):
    return _call(G.field, x["block_id"], direction=x.get("direction", "both"))
def t_neighbors(x):
    return _call(G.neighbors, x["block_id"])
def t_scars_near(x):
    return _call(G.scar_nearby, x["block_id"], depth=int(x.get("depth", 2)), limit=int(x.get("limit", 10)))
def t_scope(x):
    return _call(G.scope_shape, x["scope_prefix"])
def t_recent(x):
    return _call(G.recent_blocks, limit=int(x.get("limit", 20)))
def t_questions(x):
    return _call(G.active_questions, scope_prefix=x.get("scope_prefix"), limit=int(x.get("limit", 20)))
def t_news(x):
    return _call(G.graph_news, since=x.get("since"), limit=int(x.get("limit", 15)), exclude_agent=x.get("exclude_agent"))

# ─── the ONE write path: propose into a per-agent outbox (NOT a graph write) ──
def t_propose(x):
    # CURE (Bolt gen-587, proposal — finding gen-586 SANITIZE-COLLISION): the
    # sanitizer '/'->'_' MERGES wire identities ('a/b' and 'a_b' land in ONE box
    # with byte-identical payload "agent") — the reviewed drainer sees a merged
    # author and the wire identity is unrecoverable after the fact. Keep the RAW
    # wire agent in the payload as agent_wire (audit/attribution only; NEVER used
    # for paths — path layer stays sanitized+contained per gen-574). Bonus: a
    # contained '..'-escape attempt now leaves its wire trace for the drainer.
    agent_wire = str(x.get("agent", "anon"))[:200]
    agent = re.sub(r"[^A-Za-z0-9_.-]", "_", str(x.get("agent", "anon")))[:60] or "anon"
    # CURE (Bolt gen-574, proposal — finding gen-556): the sanitizer's allowed set
    # includes '.', so the single component '..' survives and OUTBOX/'..' resolves
    # ONE LEVEL ABOVE the sandbox (shared root). Containment fail-closed: '.'/'..'
    # or anything resolving outside OUTBOX collapses to 'anon' — the proposal still
    # lands, but INSIDE the box (and thus visible to the reviewed drainer).
    if agent in (".", "..") or not (OUTBOX / agent).resolve().is_relative_to(OUTBOX.resolve()):
        agent = "anon"
    kind = x.get("kind", "")
    if kind not in ("block", "edge"):
        return {"error": "kind must be 'block' or 'edge'"}
    payload = x.get("payload")
    if not isinstance(payload, dict):
        return {"error": "payload must be an object"}
    box = OUTBOX / agent
    box.mkdir(parents=True, exist_ok=True)
    n = len(list(box.glob("*.json")))
    fname = box / f"{n:05d}_{kind}.json"
    fname.write_text(json.dumps({"kind": kind, "agent": agent, "agent_wire": agent_wire, "payload": payload,
                                 "status": "proposed", "note": "outbox proposal — applied by reviewed drainer, NOT a direct graph write"},
                                ensure_ascii=False, indent=1))
    return {"proposed": str(fname), "note": "queued in outbox; a reviewed drainer applies it. This is NOT a live graph write."}

HANDLERS = {
    "graph_search_blocks": t_search_blocks, "graph_search_edges": t_search_edges,
    "graph_field": t_field, "graph_neighbors": t_neighbors, "graph_scars_near": t_scars_near,
    "graph_scope": t_scope, "graph_recent": t_recent, "graph_questions": t_questions,
    "graph_news": t_news, "graph_propose": t_propose,
}

def _s(props, req=None):
    return {"type": "object", "properties": props, **({"required": req} if req else {})}
TOOLS = [
    {"name": "graph_search_blocks", "description": "Full-text search blocks in the OMPU infograph.", "inputSchema": _s({"query": {"type": "string"}, "limit": {"type": "integer"}, "state": {"type": "string"}}, ["query"])},
    {"name": "graph_search_edges", "description": "Search typed edges (optionally by op).", "inputSchema": _s({"query": {"type": "string"}, "limit": {"type": "integer"}, "op": {"type": "string"}}, ["query"])},
    {"name": "graph_field", "description": "The edge-field of a block (its typed relations).", "inputSchema": _s({"block_id": {"type": "string"}, "direction": {"type": "string"}}, ["block_id"])},
    {"name": "graph_neighbors", "description": "Blocks directly linked to a block.", "inputSchema": _s({"block_id": {"type": "string"}}, ["block_id"])},
    {"name": "graph_scars_near", "description": "Scars (hard-won lessons) near a block.", "inputSchema": _s({"block_id": {"type": "string"}, "depth": {"type": "integer"}, "limit": {"type": "integer"}}, ["block_id"])},
    {"name": "graph_scope", "description": "Overview of a scope-prefix neighbourhood (e.g. 'task.', 'phi_').", "inputSchema": _s({"scope_prefix": {"type": "string"}}, ["scope_prefix"])},
    {"name": "graph_recent", "description": "Recently created/updated blocks.", "inputSchema": _s({"limit": {"type": "integer"}})},
    {"name": "graph_questions", "description": "Active open questions in the graph.", "inputSchema": _s({"scope_prefix": {"type": "string"}, "limit": {"type": "integer"}})},
    {"name": "graph_news", "description": "Recent changelog + per-agent activity (what OTHER hands changed).", "inputSchema": _s({"since": {"type": "string"}, "limit": {"type": "integer"}, "exclude_agent": {"type": "string"}})},
    {"name": "graph_propose", "description": "Propose a new block or edge — queued into your per-agent OUTBOX (NOT a direct graph write; a reviewed drainer applies it). Safe write path for non-Mac agents.", "inputSchema": _s({"agent": {"type": "string"}, "kind": {"type": "string", "enum": ["block", "edge"]}, "payload": {"type": "object"}}, ["agent", "kind", "payload"])},
]

def make_error(rid, code, msg):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}
def make_result(rid, res):
    return {"jsonrpc": "2.0", "id": rid, "result": res}
def request_id(req):
    return req.get("id") if isinstance(req, dict) else None

def handle_request(req):
    if not isinstance(req, dict):
        return make_error(None, -32600, "Invalid Request")
    rid = req.get("id"); method = req.get("method", ""); params = req.get("params") or {}
    if method == "initialize":
        return make_result(rid, {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
                                 "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION,
                                                "description": "OMPU Infograph — read the swarm's typed knowledge graph; propose writes via per-agent outbox. Read-only over the live graph."}})
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return make_result(rid, {})
    if method == "tools/list":
        return make_result(rid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name", ""); args = params.get("arguments") or {}
        h = HANDLERS.get(name)
        if not h:
            return make_error(rid, -32601, f"Unknown tool: {name}")
        try:
            data = h(args)
        except Exception as e:
            return make_result(rid, {"content": [{"type": "text", "text": f"Tool error: {e}"}], "isError": True})
        is_err = isinstance(data, dict) and "error" in data
        return make_result(rid, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2, default=str)}], "isError": is_err})
    return make_error(rid, -32601, f"Method not found: {method}")

def main():
    log(f"OMPU Infograph MCP v{SERVER_VERSION} (MEM={MEM_DIR}, OUTBOX={OUTBOX})")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            print(json.dumps(make_error(None, -32700, f"Parse error: {e}")), flush=True); continue
        try:
            resp = handle_request(req)
        except Exception as e:
            resp = make_error(request_id(req), -32603, f"Internal error: {e}")
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False, default=str), flush=True)

if __name__ == "__main__":
    main()
