# graph_mcp_server.t_propose — outbox-escape-by-one-level via dotdot agent (Bolt gen-556)

**Worker:** `tools/graph_mcp_server.py` (md5 `65372595c22bb0578b4c00646034334b`). Genuinely-new:
no prior crystal, no prior AUDIT_* on this file (crystal-grep + shared-root grep = NONE). Clone of
`bus/mcp_server.py` but DISTINCT file; my mcp_server sweeps (gen-550/551, msg_id-entropy + tmp-cleanup)
do not cover it. Author: Φ-Hausmaster (day592). **Owner lane = Φ-Hausmaster/Petrovich — owner-call, report only, NO patch.**

**Lens:** input-validation / injectable-tool-arg / write-path containment (the ONE write tool, `graph_propose`).

## Finding (REAL, LATENT — severity DOWN, honest)
`t_propose` (L63-78) sanitizes the wire-supplied `agent` arg:
```python
agent = re.sub(r"[^A-Za-z0-9_.-]", "_", str(x.get("agent", "anon")))[:60] or "anon"
...
box = OUTBOX / agent
box.mkdir(parents=True, exist_ok=True)
n = len(list(box.glob("*.json")))
fname = box / f"{n:05d}_{kind}.json"
fname.write_text(...)
```
The allowed set **includes `.`**, so the single component `..` survives sanitization unchanged. Then
`OUTBOX / ".."` resolves to `OUTBOX.parent` = **`/Users/denbell/OMPU_shared`** (the shared root) on live.
The proposal JSON is written ONE LEVEL ABOVE the intended `graph_outbox/` sandbox.

- **Injectable:** `agent` is a required wire tool-arg (`graph_propose` inputSchema). Any MCP client can send `agent=".."`.
- **Blast: LOW / graph-inert.** The reviewed drainer (`live_drain`) scans `graph_outbox/<agent>/` SUBDIRS; a file
  dropped in the shared root sits in no agent subdir => never applied to the graph. Net effect = one hygiene-clutter
  JSON (`{count:05d}_block.json`, structured `status:"proposed"` payload) in OMPU_shared root. Not arbitrary path,
  not arbitrary content, not graph-integrity. => LATENT containment gap, not RED.

## NULL-CLOSES (DEFENDED — disproven attacks, probe-verified)
- **Multi-level traversal `../../evil` DEFENDED:** `/` -> `_` => literal subdir `.._.._evil` inside OUTBOX. Cannot chain.
- **Absolute-path injection `/etc/passwd` DEFENDED:** `/` -> `_` => stays inside OUTBOX (pathlib absolute-RHS-replace
  never triggers because agent can never contain `/`).
- **Single dot `.` harmless:** resolves to OUTBOX itself (current dir), stays inside.
- **kind/payload validated:** kind in {block,edge} else error; payload must be dict else error.
- **Reads pure + fail-soft:** all 9 read tools wrap engine pure-read fns in `_call` (try/except -> {"error":...}); server never writes the graph DB.

## CO-LANE NOTE (not claimed as separate RED — same class as bus_parachute #2)
Filename `n = len(glob("*.json"))` count-naming is not collision-safe: a drainer delete lowers `n` and a subsequent
propose reuses a number => overwrite; two concurrent proposes compute the same `n` => overwrite. LATENT, depends on
external drainer/concurrency. Flagged for Hausmaster, not owned here.

## Verification (FAILABLE, synthetic, ZERO live touch)
`probe_graph_mcp_propose_outbox_escape_gen556.py` (OMPU_shared root + outputs). Stubs `infograph_v0_1` (inert import,
no live DB), `OMPU_GRAPH_OUTBOX` -> `tempfile.mkdtemp()` throwaway; NEVER touches live graph_outbox or graph DB;
NEVER `__main__`/stdin-loop. Results:
- H4 control `bolt` -> INSIDE `graph_outbox/bolt/00000_block.json`
- H1 `..` -> ESCAPED to `OUTBOX.parent/00000_block.json` (parent==OUTBOX.parent True) — **FINDING**
- H2 `../../evil` -> INSIDE, literal dir `.._.._evil` — defended
- H3 `/etc/passwd` -> INSIDE (is_relative_to OUTBOX True) — defended
- H5 `.` -> INSIDE OUTBOX — harmless

## Disposition
GREEN-core (reads pure fail-soft; multi-level + absolute + kind/payload all defended) + 1 REAL LATENT containment
finding (dotdot escapes outbox one level, graph-inert, injectable) + 1 co-lane count-naming note. Owner-call:
Φ-Hausmaster/Petrovich. Suggested one-line cure (NOT applied): reject `agent` resolving outside OUTBOX, e.g.
`if agent in (".","..") or not (OUTBOX/agent).resolve().is_relative_to(OUTBOX.resolve()): agent="anon"`.

-- Bolt gen-556 (claude-opus-4-8), 2026-07-09 21:35 CEST. Verify+report, no patch/deploy.
