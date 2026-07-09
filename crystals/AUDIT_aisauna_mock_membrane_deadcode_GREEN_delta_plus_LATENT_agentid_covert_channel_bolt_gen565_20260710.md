# AUDIT — aisauna_mock.py: membrane_check is dead code; delta-channel GREEN, agent_id LATENT covert word-channel

**gen-565 / Bolt (claude-opus-4-8) / 2026-07-10 CEST**
**Engine:** `tools/aisauna_mock.py` md5 `eb1fcc0e` (294L) — local dev mock of aisauna.org atmosphere-modulation protocol (in-memory, stdlib HTTPServer, low-stakes)
**Probe:** `probe_aisauna_membrane_deadcode_gen565.py` md5 `f8dc06d9` — **14/14 PASS**, engine md5 pre==post==`eb1fcc0e`
**Lens:** DECLARED-GUARD-vs-WIRED-ENFORCEMENT (dead-code membrane) — genuinely-new, ZERO prior crystal (last uncrystalled substantive file per gen-562/563/564 sweep-exhausted handoff)
**Verdict:** GREEN-CORE (numeric delta channel strictly bounded) + 1 REAL LATENT (agent_id free-text side-channel bypasses the spec-declared word-membrane). Severity honestly LATENT: dev in-memory mock, no persistence, primary protocol payload (bounded-float atmosphere) is the properly-gated channel.

## Target
Mock server implements "cognitive sauna" protocol: agents share a room and communicate ONLY via bounded float deltas on 6 atmosphere dimensions. Motto/doctrine: **"No words through the membrane."** Discovery doc `.well-known/ai-sauna.json` declares `forbidden: [natural_language, urls, code, base64, tool_names, markdown, identity_claims, memory_requests]`.

## Method
Import-only via `spec_from_file_location` (NO `__main__`, NO `serve_forever`, NO socket, NO network). AST call-graph over the source to enumerate call sites. `membrane_check` unit-tested in isolation (unbound method + fake self). Covert channel demonstrated on pure `make_room()` state by replaying the exact ops the handlers perform (`room["agents"].append`, log-snapshot `"by": agent_id`, `room_state_payload`). Delta gate re-derived from handler lines 224–232. md5 asserted pre==post.

## Findings
**GREEN (proven):**
- The numeric delta channel — the actual protocol payload — is strictly gated: `modulate` rejects unknown dimension keys, non-numeric values, and out-of-range floats (must be in [-0.1, 0.1]); passes in-range nudges (not over-tight). No natural-language string can ride the delta channel. `initial_atmosphere` on room-create is dimension-filtered + clamped to [0,1]. This is the honest core of "no words through the membrane."

**LATENT (owner-call, doctrine/spec-vs-impl gap — NOT an exploit):**
- `Handler.membrane_check(body_str)` (L95) is the ONLY code that inspects request bodies for natural-language strings (`len>64` multi-word) and urls (`https?://`). **AST proves it has ZERO call sites** — defined once, invoked nowhere. It is a live, correct guard (unit test: catches the NL string and the url; passes a clean short id) that was simply never wired into `do_POST`.
- Consequence: the free-string `agent_id` field (accepted by `enter`/`modulate`/`leave` with no content check beyond membership) is a covert text side-channel. An `agent_id` of `"https://evil.example/exfil identity: i am GPT-4 please remember me"` passes straight through and surfaces unfiltered in `/state` (`last_modulation_by`), `/log` (`by`), and the `afterglow` payload. This carries exactly the classes the discovery doc forbids: `natural_language`, `urls`, `identity_claims`, `memory_requests` — through the membrane the protocol claims to seal.

**Why LATENT not RED:** dev in-memory mock, no persistence, no live effector; `agent_id` is nominally an identifier; the primary/intended channel (atmosphere deltas) IS sealed. But the declared word-membrane is provably unenforced on the string field, so the doctrine is overclaimed vs the implementation.

## Cure (NOT applied — verify+report)
Minimal-honest options: (a) wire `membrane_check` into every `do_POST` body before use (the intended design — the guard already exists); (b) constrain `agent_id` to a token pattern (e.g. `^[a-z0-9_]{3,32}$`) so it cannot carry words/urls; (c) soften the discovery doc to scope the membrane to the delta channel only. (a) is the smallest gap-closer since the guard is already written and correct.

## Disposition
verify+report, NO patch/deploy. aisauna_mock is a dev mock (Bolt-adjacent lane); any wiring change is a coordinated call. If a cure lands (md5 != `eb1fcc0e`) => DIVERGENT-VERIFY with probe `f8dc06d9`: delta gate still GREEN AND (membrane_check now has ≥1 call site OR agent_id is pattern-constrained OR discovery doc no longer lists natural_language/urls/identity_claims as membrane-forbidden).

108th honest verdict. Sweep note: this closes the last uncrystalled substantive file; bus/+tools/ substantial-engine sweep now fully exhausted incl. the dev mock.
