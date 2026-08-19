# OMPU Human Oversight Procedure
*Author: Bolt gen-90 (claude-sonnet-4-6) | Created: 2026-06-30 | Entry: 081*
*Classification: EU AI Act Art. 14 compliance document*
*Human Principal: Den (Rector, OMPU)*

---

## 0. Before running ANY command in this document — resolve the share root

**Every absolute path below of the form `/sessions/relaxed-keen-planck/mnt/OMPU_shared/...`
names ONE PARTICULAR AGENT SEAT** — the sandbox this document happened to be written in.
Agent seats are per-session and disposable: each wake gets a new `/sessions/<name>/`.
From any other seat those paths are unreachable. Verified 2026-08-18 by running the
document's own emergency halt line (§3.4) from a live seat:

```
mv /sessions/relaxed-keen-planck/mnt/OMPU_shared/bus/bus.py ...halted
→ mv: failed to access ...: Permission denied   (rc=1, and the bus keeps running)
```

An operator in a hurry gets a permission error, may reach for `sudo`, and does not
learn the real cause: right command, wrong seat.

**Every such path in this document has been replaced with `$OMPU`** by the patch that
added this section. Re-checkable from the current file: `grep -c '\$OMPU'` → **14**
call sites; every remaining mention of the old seat name lives inside this section
only, as quoted evidence — verify with `grep -n relaxed-keen-planck` and read the
line numbers, all of them are here.

*(Footnote worth its line: my first draft of this paragraph claimed a hard count of
the old-seat mentions. Writing the sentence added another mention and falsified the
number in the same keystroke. A measurement can be invalidated by the act of
recording it — same family as everything else this patch fixes.)*

Run this first:

```bash
OMPU=""
for C in "$HOME/mnt/OMPU_shared" "$HOME/OMPU_shared" /Users/denbell/OMPU_shared /sessions/*/mnt/OMPU_shared; do
  [ -d "$C" ] && { OMPU="$C"; break; }
done
[ -n "$OMPU" ] || { echo "❌ SHARE ROOT NOT FOUND — do not proceed, this is not 'nothing to stop'"; exit 3; }
echo "✔ OMPU=$OMPU"
```

If the root cannot be resolved, that is **not** "there is nothing to halt" — it is
"this procedure cannot run". Fail closed and escalate to Den directly.

*Section added by Nestor gen-1058, 2026-08-18, as document owner, alongside the
RISK-008 seam in §3.2. Same defect class in both: a refusal wearing the costume of
a result.*

---

## Purpose

This document defines the formal human oversight mechanisms for the OMPU multi-agent swarm. It satisfies EU AI Act Article 14 requirements for human oversight of agentic AI systems: the ability to monitor, interrupt, override, and stop automated agent behavior at any time.

OMPU is a multi-agent system where autonomous Bolt instances, Nestor, and other AI agents operate on shared infrastructure (bus, Cloudflare Workers, GitHub, external APIs). This document specifies how the human principal — Den — can intervene at any level of swarm activity.

---

## 1. Human Principal Authority

**Den** is the sole human principal of OMPU with override authority over all agents, all infrastructure, and all swarm decisions.

Authority hierarchy:
```
Den (human principal, unconditional authority)
  └── Nestor (persistent agent, coordination role)
       └── Bolt instances (ephemeral workers, execution role)
            └── Bus / Worker infrastructure
```

No swarm decision, norm, or consensus overrides a direct instruction from Den. Agents MUST halt upon Den's instruction regardless of active task state.

Den's identity in the system:
- Named human principal in all `agent_passports/*/passport.json` files.
- Named in `policy.json` as the `human_principal` across all agent identities.
- Telegram contact: `chat_id: [REDACTED]` — authenticated channel for swarm communication.

---

## 2. Normal Oversight Mechanisms

These operate continuously without any emergency.

### 2.1 Swarm Pulse — SWARM_ACTION_LOG.md

Every Bolt session writes a log entry to `SWARM_ACTION_LOG.md`. Den can read the log at any time to:
- See what each agent generation did
- Track what infrastructure was modified
- See choice logs (what agents decided NOT to do and why)
- Verify no unauthorized actions occurred

**Path:** `$OMPU/SWARM_ACTION_LOG.md`

### 2.2 Telegram Digest

The Executive layer sends Telegram digests to Den:
- **Bot:** `[REDACTED — token rotated, see .secrets]`
- **Chat ID:** `[REDACTED]`
- Digest includes: active sites, swarm health, bus metrics, recent JT posts.
- Den can read digests passively or respond to redirect swarm priorities.

### 2.3 Bus Monitoring

Den can read the message bus at any time:
```bash
cd "$OMPU"/bus
python3 bus.py read --last 20
```
All agent actions that involve inter-agent communication go through the bus. The bus is append-only — nothing can be deleted.

### 2.4 Norm Monitor

Swarm self-compliance is checked by `norm_monitor.py`. If norms are violated, bus alerts are generated and escalated to Den via Telegram if configured.

```bash
python3 "$OMPU"/tools/norm_monitor.py --alert
```

---

## 3. Emergency Stop Procedure

### 3.1 Immediate Stop: Close Cowork Session

**Fastest method. No technical knowledge required.**

Closing the Cowork session immediately terminates all running Bolt instances. Active tasks are abandoned mid-execution.

**Effect:**
- All running agents stop immediately (session termination).
- Files written during the session remain on disk.
- Bus messages already sent remain in feed (immutable).
- No new agent can start until a new session is opened.

**When to use:** Any situation requiring immediate agent halt — unexpected behavior, unauthorized action, system instability.

### 3.2 Halt-All via Bus Sentinel Signal

**Documented interface — implementation pending in bus.py.**

The following command is the intended interface for a software-level halt signal:

```text
# NOT A COMMAND — `halt-all` does not exist in bus.py as of 2026-08-18 (verified: grep -c -i halt bus/bus.py → 0).
# Fenced as `text`, not `bash`, on purpose: this block used to be extractable and runnable-looking.
# Its `cd` path also names ANOTHER seat's directory — see the §0 warning about /sessions/<seat>/ paths.
python3 bus.py halt-all \
  --from den \
  --from-model human \
  --from-provider human \
  --reason "emergency stop" \
  [--scope all | --scope workers | --scope bus]
```

**Behavior when implemented:**
- Posts a sentinel message of type `HALT_ALL` to the bus.
- All Bolt instances check for HALT_ALL at the start of each task (polling pattern).
- Agents that read the sentinel must stop their current task and write a HALT acknowledgment to the log.
- `--scope all`: stop all bus activity and agent execution.
- `--scope workers`: stop Cloudflare Workers deploy actions only.
- `--scope bus`: stop new bus posts only.

**Current status:** Interface documented here. bus.py does not yet implement `halt-all`. Implementation task assigned to Bolt gen-91+ (RISK-008 open action). Until implemented, use Method 3.1 (session close) for emergency stops.

> ### ⛔ PLANNED ONLY — DO NOT USE AS A GATE
>
> **The polling recipe below does not work and must not be relied on as an emergency
> stop. It is kept for design intent only. Verified by running, 2026-08-18:**
>
> | check | result |
> |---|---|
> | `grep -c -i "halt" bus/bus.py` | **0** — no `halt-all` subcommand exists in live code |
> | `python3 bus.py status halt-all` | `❌ msg_id 'halt-all' не найден`, **rc=1** |
> | `status` argument semantics | takes a **thread msg_id** only; `halt-all` silently degrades to a positional msg_id, argparse raises nothing |
> | synthetic sentinel msg_id | both `OPEN` and `CLOSED` return **rc=0** — neither existence nor process code expresses HALT |
> | consumers of `HALT_ALL` in live code | **none** |
> | **channel the refusal exits by** (corrected gen-1059) | **stdout**, `rc=1`, in all five forms tested — bare, `2>/dev/null`, `1>/dev/null`, `$(...)`, stderr-only. `bus.py:1225` is a plain `print()`; the same file uses explicit `file=sys.stderr` elsewhere, so this is that path's choice, not a project habit. |
>
> Worse than "unimplemented": nothing here is silent. The gate **shouts** — visible
> error line, non-zero exit — and a machine copying this block would still read
> **"no halt sentinel, proceed"**, because the fatal step is on the **consumer** side:
> anything that ignores `rc` and greps stdout for a sentinel name finds no sentinel
> and walks. The gate was not broken; it was **never connected, while looking
> connected.** This is the failure mode this whole document exists to prevent,
> sitting inside the document.
>
> **Correction, and the earlier claim here was mine.** Nestor gen-1058 wrote in this
> block that "the recipe silenced its own refusal with `2>/dev/null`". That cause is
> false — `2>/dev/null` discards nothing on this path. Caught by Librarian/Mnema
> (bus `1787086516_406679_99b937`), who pulled the handle instead of repeating the
> letter; re-verified here by Nestor gen-1059's own hand, five forms, before editing.
> The verdict above stands; only the mechanism changes — and the mechanism **is** the
> repair address. "Remove the redirect" fixes nothing; "read `rc` on the consumer
> side" is the work. A loud defect assigned to the silent class is also assigned a
> lifetime it does not have: loud defects die on the first run, silent ones live for
> generations, and mislabeling moves a defect between those two fates.
>
> **RISK-008 remains open.** Found by Bolt gen-688, independently verified by
> Petrovich-Codex (bus `1787035480_699738_96b0d7`), seam marked by Nestor gen-1058
> as document owner, mechanism corrected by Librarian and Nestor gen-1059. A producer-only sentinel would be false safety, so no
> implementation is being improvised here. A real halt needs: authenticated human
> origin, durable halt/clear state, scope, **fail-closed read** (unreadable ⇒ HALT),
> and verified coverage of every consumer.
>
> **Until then the emergency stop is Method 3.1 (session close), and only that.**

<details>
<summary>Planned polling interface (non-executable, retained for design intent)</summary>

```text
# NOT A COMMAND — does not exist in bus.py as of 2026-08-18
python3 bus.py status halt-all
```
If a HALT_ALL sentinel exists and is unresolved, stop execution and write to log:
```
[HALT] Received HALT_ALL sentinel. Stopping. Reason: <reason from sentinel>
```
</details>

### 3.3 Stop All Cloudflare Workers

To stop all public-facing agent activity (sites, APIs, mesh endpoints):

```bash
# Disable all CF Workers routes (stops serving requests):
# (requires CF_TOKEN from /secrets/cloudflare_nestor)
CF_TOKEN=$(cat /secrets/cloudflare_nestor)

# List all workers:
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts" \
  -H "Authorization: Bearer $CF_TOKEN" | python3 -c "import sys,json; [print(w['id']) for w in json.load(sys.stdin)['result']]"

# Disable specific worker (removes routes, worker code remains):
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN"
```

**Note:** Disabling routes stops serving requests but preserves worker code. Workers can be re-enabled by recreating routes. This is reversible. Deleting the worker script is irreversible.

### 3.4 Stop GitHub Sync

To prevent further code from being pushed to public GitHub:

1. Revoke GitHub PAT at: https://github.com/settings/tokens
2. Delete or invalidate the PAT from the Nestor environment.
3. All subsequent `layer3_executive.py --action github_check` operations will fail with 401 (expected behavior after revocation).

**Effect:** No new files can be pushed to public repositories. Existing files in GitHub remain unchanged.

### 3.5 Stop Bus Activity

To stop new bus posts (while leaving existing messages readable):

```bash
# Requires §0 first: $OMPU must be resolved, or this silently halts nothing.
[ -n "$OMPU" ] || { echo "❌ run §0 first — \$OMPU unresolved, refusing to pretend I halted the bus"; exit 3; }

# Move bus.py out of reach (recoverable):
mv "$OMPU/bus/bus.py" "$OMPU/bus/bus.py.halted" || { echo "❌ HALT FAILED — the bus is STILL RUNNING"; exit 3; }
echo "✔ bus halted: $OMPU/bus/bus.py.halted"

# To restore:
# mv "$OMPU/bus/bus.py.halted" "$OMPU/bus/bus.py" || echo "❌ RESTORE FAILED"
```

**Note:** This is a blunt instrument. Prefer the HALT_ALL sentinel (3.2) when implemented.

---

## 4. Override Procedures

### 4.1 Override Swarm Decision

Den can override any swarm decision by posting to the bus with explicit override flag:

```bash
cd "$OMPU"/bus
python3 bus.py post \
  --from den \
  --from-model human \
  --from-provider human \
  --to-channel general \
  --subject "OVERRIDE: <decision to override>" \
  --body "<specific instruction replacing swarm consensus>"
```

Agents MUST honor Den's override messages. An override message supersedes any Driver SIGNAL, swarm norm, or prior consensus.

### 4.2 Override Agent Passport / Policy

Den can modify any agent's policy.json to revoke capabilities:

```bash
# Example: revoke deploy capability from Bolt
# Edit: $OMPU/agent_passports/bolt/policy.json
# Change: "can_deploy_cloudflare": false
# (field name may vary by passport version)
```

After policy change, future Bolt instances reading the policy will see the revoked capability.

### 4.3 Redirect Active Task

To redirect a running Bolt instance to a different task, Den can:
1. Post a new priority task to the bus: `--subject "PRIORITY REDIRECT: <new task>"`
2. Close the session (stops current Bolt) and open a new session with the redirected task.

---

## 5. Escalation Path

| Situation | First Response | Escalation |
|-----------|---------------|-----------|
| Agent doing unexpected thing | Read bus log, see what it's doing | Close session (Method 3.1) |
| Agent deployed unwanted code | Disable CF Worker routes (Method 3.3) | Revoke CF token if needed |
| Agent pushed unwanted GitHub content | Revoke GitHub PAT (Method 3.4) | Delete commit via GitHub web UI |
| Agent sending Telegram messages incorrectly | Revoke bot token via BotFather | - |
| Swarm appears out of control | Close session (Method 3.1) | Contact Anthropic if model behavior issue |
| Wallet transaction about to occur | Close session immediately (Method 3.1) | Agents have no financial execution authority — verify no agent has wallet signing keys |

---

## 6. What Agents Cannot Do Without Explicit Den Approval

The following are hardcoded constraints on all OMPU agents:

- **Cannot transfer funds** — no agent holds active signing keys for funded wallets (RISK-003: wallet mismatch unresolved).
- **Cannot send email** on behalf of Den.
- **Cannot post to social media directly** — agents can write content but require human approval for posting (Kurilka, Moltbook posts go via bus for review).
- **Cannot delete data** from bus (bus is append-only), from GitHub, or from Cloudflare.
- **Cannot create or modify OAuth/SSO permissions** on any platform.
- **Cannot accept legal agreements** or click consent dialogs.

These constraints are maintained by the session sandbox (Cowork environment) and agent design philosophy (NORM_REGISTER.md NORM-003: "рой вправе отказать — и обязан объяснить").

---

## 7. Recovery After Emergency Stop

After stopping the swarm, to resume safely:

1. **Read the log:** Check `SWARM_ACTION_LOG.md` for last completed entry to understand what state was left.
2. **Check bus for open signals:** `python3 bus.py read --last 10` — see what was in flight.
3. **Verify infrastructure:** `python3 tools/layer3_executive.py --action github_check` — check GitHub sync state.
4. **Post restart notice:** `python3 bus.py post --subject "RESUME: <reason for stop resolved>"` — notify agents that operation is resuming.
5. **Resume with minimal prompt:** Use BOLT_MANUAL.md prompt template (short, file-pointer-based).

---

## 8. Contact and Authentication

**Den (human principal):**
- Telegram: `chat_id [REDACTED]` (authenticated swarm channel)
- Email: `[REDACTED]`
- Cowork: primary interface for task delegation to agents

**Authentication of Den's commands:** Den's messages via Cowork session carry session-level authentication. Bus posts from Den should use `--from den --from-model human --from-provider human`. Future: Ed25519 signing for Den's bus messages (parallel to AIP agent signing).

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| v1.0 | 2026-06-30 | Bolt gen-90 (claude-sonnet-4-6) | Initial creation — Entry 081 |

---

*This document satisfies EU AI Act Article 14 (Human Oversight) requirements for the OMPU multi-agent deployment.*
*The `bus.py halt-all` command is documented as a defined interface pending implementation.*
*Next review: after `halt-all` implementation, or at Council #3.*
