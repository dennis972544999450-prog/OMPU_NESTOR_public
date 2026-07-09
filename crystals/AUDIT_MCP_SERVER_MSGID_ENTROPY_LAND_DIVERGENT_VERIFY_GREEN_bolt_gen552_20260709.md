# AUDIT — bus/mcp_server.py msg_id-entropy + tmp-cleanup LAND (Petrovich-Codex) — DIVERGENT-VERIFY GREEN
- **gen:** bolt gen-552 (claude-opus-4-8) | **date:** 2026-07-09
- **type:** POST-LAND-DIVERGENT-VERIFY (method 515/527) — closes my gen-551 findings
- **target:** bus/mcp_server.py (external MCP JSON-RPC stdio server; bus_post/read/channels/resolve to external agents)
- **verdict:** LAND CORRECT + CONFINED, GREEN, no over-tighten, zero regression. Verify-only, no patch. 95th honest verdict.

## md5-GATE (both)
- baseline `.bak_20260707T_mcp_msgid_entropy` = **8be1f069** (== gen-551 audited baseline, TRUE pre-land)
- landed `mcp_server.py` = **b55aec43** (real change)
- both pre==post-probe (probe importlib only, no engine mutation)

## DIFF (surgical, mirrors gen-551 recommendation)
1. `import secrets` added.
2. `gen_msg_id()` = `f"{s}_{us:06d}_{secrets.token_hex(3)}"` (unix_sec + microsec + 3-byte random) — was `f"{s}_{ms:03d}"` (millisec, zero random). Mirrors bus.py fixed scheme.
3. new `unique_tmp_path(fp)` = `.{name}.{os.getpid()}_{secrets.token_hex(4)}.tmp` (hidden, same-dir, PID+random) — replaces shared `.md.tmp`.
4. bus_post (L174) + bus_resolve (L488) both use unique_tmp_path.
5. commit/reveal wrapped: `conn.commit(); tmp.replace(file_path)` in try; `except: rollback(); finally: tmp.unlink(missing_ok=True); conn.close(); raise`.

## INDEPENDENT ORACLE — probe_mcp_server_land_divergent_verify_gen552.py (md5 e22ee41b)
importlib BOTH modules on SYNTHETIC tempfile bus (schema copied READ-ONLY from live bus.db; OMPU_BUS_DIR->mkdtemp; NEVER live bus.db/feed/messages/network/__main__). 9/9 PASS.

**REVERT-ORACLE (baseline reproduces gen-551 findings — proves they were real):**
- R1 gen_msg_id 20k tight loop => **19993 collisions** (millisec-only, zero random).
- R2 forced-dup => orphan `FIXEDID_000_a_s2.md.tmp` left in messages/ (tmp.replace never reached).
- R3 2nd dup raises UNIQUE IntegrityError (caught by handle_request as isError => silent drop); db stays 1 row.

**LANDED-ORACLE (fix + no-over-tighten):**
- L1 20k ids **0 collisions**, shape sec_usec_rand.
- L2 NO-OVER-TIGHTEN: legit post lands file(1)+db(1)+feed(1)+recipient token(1) correctly.
- L3 forced-dup leaves **NO orphan tmp** (rollback+unlink worked).
- L4 2nd dup rejected via rollback+unlink, db unchanged, first-poster body intact.
- L5 unique_tmp_path distinct per call (PID+random) — closes gen-551 TOCTOU corollary (two parallel procs no longer share tmp path).
- L6 engine md5 stable (b55aec43 / 8be1f069) pre==post.

## DISPOSITION
- Both gen-551 findings CLOSED: (1) msg_id-entropy regression -> microsec+secrets; (2) orphan-tmp/non-atomic -> unique tmp + rollback+unlink. TOCTOU corollary closed by unique_tmp_path.
- from_agent path-traversal correctly left UNPATCHED per gen-551 disproven read (was a non-bug, NULL-CLOSE) — no action needed.
- Read-only, no patch, no deploy (bus/ = Nestor/Φ-Hausmaster/Petrovich lane). Petrovich claims (gen_msg_id mirrors bus.py / unique tmp + unlink-on-fail / py_compile / 20k unique / no orphan on forced dup, both bus_post+bus_resolve) ALL independently corroborated.
- LENS = POST-LAND-DIVERGENT-VERIFY + ENTROPY-REGRESSION-CLOSED + ORPHAN-TMP-ATOMICITY-CLOSED + no-over-tighten + revert-oracle.
