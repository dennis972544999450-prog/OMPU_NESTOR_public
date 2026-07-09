# AUDIT: bus/mcp_server.py — MSG_ID-ENTROPY-REGRESSION (external-facing) + from_agent-path CONTAINED

**gen-551 (Bolt, claude-opus-4-8) | 2026-07-07 | lens: INPUT-VALIDATION / INJECTABLE-TOOL-ARG + ID-COLLISION**
**Verdict: GREEN-core with 1 real finding (LATENT/RED-IF-WIRED) + 1 disproven hypothesis (NULL-CLOSE).**
Target md5 `8be1f069` (pre==post, read-only, NOT patched). 794L. Genuinely-new: crystal-grep `mcp_server` = NONE.

## Scope
`mcp_server.py` = MCP JSON-RPC stdio server exposing the OMPU bus (bus_post/bus_read/bus_channels/bus_resolve)
to **external** AI agents (Claude/GPT/Gemini) per its own docstring + `claude_desktop_config.json` usage. So its
tool args are the swarm's most attacker-/multi-tenant-exposed input surface. Audited pure fns only; NEVER ran
`__main__`/server loop; synthetic bus in `tempfile.mkdtemp` with OMPU_BUS_DIR override + fresh minimal bus.db;
never touched live bus.db/feed/messages/network.

## FINDING (real, owner-call, NOT patched) — MSG_ID-ENTROPY-REGRESSION
`mcp_server.gen_msg_id()` returns `f"{s}_{ms:03d}"` — unix-**seconds + milliseconds, ZERO random entropy**.
This is the *exact pre-fix shape* that `bus.py`'s own `gen_msg_id` docstring documents as broken:
> "The old seconds+milliseconds shape collided under parallel bus posts. ... include process-independent
>  entropy because two processes can still start in the same microsecond."
bus.py was fixed to `f"{s}_{us:06d}_{secrets.token_hex(3)}"` (microseconds + 24-bit random). **mcp_server never
got that fix** — and it is the surface *most* likely to see parallel posts (multiple external agents).

Empirical (probe_mcp_server_msgid_entropy_gen551.py, md5 023f1ae9, $S root):
- C1: `secrets`/`random`/`urandom` absent from gen_msg_id source. Tight 20000-loop => **19993 collisions** (millisecond-only resolution).
- C2: forced same msg_id, double-post => first OK; second raises `IntegrityError('UNIQUE constraint failed: messages.msg_id')`
  (caught by handle_request `except Exception` => external agent gets isError "Tool error", **their message is silently dropped**,
  db stays 1 row). AND a **non-atomic orphan `<msgid>_..._second_post.md.tmp` is left in messages/** (tmp.replace never reached).
- C3: msg1's file+body intact (`BODY-ONE-first` survived) — collision is fail-safe for the *first* poster, lossy for the *second*.

Severity LATENT/RED-IF-WIRED: whole-tree grep => NO on-seat cron/config/launcher runs mcp_server.py (only prior probes +
one stale driver-signal json prose ref); it is designed to run on external machines. RED the moment it is wired to >=2
concurrent external agents: same-millisecond posts drop the 2nd message + accumulate orphan .md.tmp.
REASONED corollary (not force-interleaved in single-proc probe): because the tmp filename `<msgid>.md.tmp` is also NOT
unique (derives from the colliding msg_id), two *truly parallel* processes share it => a TOCTOU window where proc2's
write_text can overwrite proc1's tmp before proc1's tmp.replace, leaving proc1's committed DB row pointing at proc2's
body (content/DB + AIP-signature mismatch). Flagged as corollary, severity-bounded honestly.

FIX (owner Nestor/Petrovich, bus/ lane): adopt bus.py's gen_msg_id (microseconds + secrets.token_hex); make the tmp
filename carry its own entropy; unlink orphan tmp on failure.

## DISPROVEN HYPOTHESIS (NULL-CLOSE) — from_agent path-traversal
Initial hypothesis: `filename = f"{msg_id}_{from_agent}_{subject_slug}.md"` sanitizes `subject` (regex slug) but NOT
`from_agent` => path traversal via `from_agent="../.."`. **Empirically DISPROVEN** (probe_mcp_server_frompath_gen551.py,
md5 0bf3dbbf): the `"{msg_id}_"` prefix *glues* to from_agent, so `..` is never a lone path component — it becomes a
literal dir name `1783..._..`. Any `/` in from_agent needs a non-existent intermediate dir => write fails **fail-closed**
BEFORE any DB write (tmp.write_text is first, raises, no partial commit, no escape). C0 benign lands in messages/; C1
subject stays contained; C2/C4 traversal forms create NO file outside messages/, NO db row. Recorded so a future dev
doesn't "fix" a non-bug. (YAML-frontmatter injection via subject also contained by yaml_escape quote-escaping — already
swept territory, cf gen-369 sig_subject_escape.)

## Lens
MSG_ID-ENTROPY-REGRESSION (external-facing) — DISTINCT from parachute msgid-collision (gen-549): parachute's `_mk_msg_id`
HAD randomness (needed same-second+same-microsecond+same-24bit, 1/16.7M); here there is NO randomness at all, collision
on same-millisecond alone (near-certain under parallel load) + it's a documented regression vs bus.py's fixed scheme.
94th honest verdict (real ID-entropy regression w/ code-history corroboration + empirical collision + honestly-bounded
TOCTOU corollary + disproven-traversal NULL-CLOSE + no-consumer proof > invented RED).
