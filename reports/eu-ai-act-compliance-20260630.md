# EU AI Act Compliance Gap Analysis — OMPU
*Author: Bolt gen-89 (claude-sonnet-4-6) | Date: 2026-06-30 | Council #2 Priority*
*33 days to August 2, 2026 deadline*

---

## Executive Summary

OMPU is a multi-agent research swarm operating under a single human principal (Den). Its infrastructure includes an append-only message bus, Ed25519-signed agent passports with DID, a norm register, and 17 live Cloudflare Workers. Under the EU AI Act, OMPU's classification depends on use-case scope and who it interacts with. This analysis maps OMPU's existing assets against the Act's requirements and identifies gaps requiring action before August 2, 2026.

**Bottom line:** OMPU is well-positioned on identity and audit trail. The three critical gaps are (1) no human override/kill-switch mechanism, (2) no formal risk classification documentation, (3) no public-facing transparency notice for agent interactions. These can be addressed within 33 days.

---

## 1. Regulatory Context

### 1.1 Key Deadline

**August 2, 2026** — High-risk AI provisions enter into force. GPAI model provisions already applied since August 2, 2025.

### 1.2 Applicability to OMPU

OMPU does not manufacture AI models (it deploys them via Anthropic API). It is therefore a **deployer**, not a model provider. However, as an orchestrator of multiple autonomous agents that can take actions (post to Slack, deploy to Cloudflare, write files, send Telegram messages), OMPU may also qualify as a provider of an **agentic AI system**.

**Risk classification factors:**
- OMPU agents interact with public content (jsontube.org, Moltbook, social platforms)
- Agents can take autonomous financial-adjacent actions (Cloudflare Workers deploy, API calls)
- Multi-agent chains: bus → Driver → Executive → CF deploy → external APIs

**Likely classification:** General-purpose agentic system, **not** high-risk under Annex III categories (no HR, credit, law enforcement, healthcare use). However, the **transparency obligations (Article 50)** apply when agents interact with natural persons, and **logging requirements** apply to any agentic system deployed in production contexts.

### 1.3 Relevant Articles

| Article | Title | Applies to OMPU |
|---------|-------|-----------------|
| Art. 5 | Prohibited practices | Must confirm no manipulation of users |
| Art. 12 | Logging requirements | Automatic event logging for agentic systems |
| Art. 13 | Transparency to deployers | Internal documentation of system behavior |
| Art. 14 | Human oversight | Override and interrupt mechanisms |
| Art. 50 | Transparency to end users | Disclosure when agents interact with humans |
| Art. 55 | GPAI obligations | Applies to Anthropic (upstream), not directly to OMPU |
| Recital 99-100 | Multi-agent chains | Every agent in chain is in scope |

---

## 2. Infrastructure Inventory — What OMPU Has

### 2.1 Audit Trail — BUS (STRONG ✅)

**Asset:** `/sessions/.../OMPU_shared/bus/bus.py` + `feed.jsonl` + `bus.db`

- Append-only message feed: every post, resolve, and action is recorded
- SQLite database with full message history
- `feed.jsonl` serves as machine-readable log
- `bus.py resolve` closes threads with reason (inhibitory channel, 96.3% resolve rate)
- Supports `--sign` flag for Ed25519 message signing (AIP mode, gen-73)

**Compliance coverage:**
- Art. 12 (logging): PASS — append-only, structured, machine-readable
- Art. 12 retention: PARTIAL — no explicit 6-month TTL policy documented

**Gap:** No documented retention policy. Art. 12 + Art. 19 require minimum 6-month log retention. Bus logs are currently retained indefinitely (no deletion mechanism visible), which is technically compliant but undocumented.

---

### 2.2 Agent Identification — PASSPORTS (STRONG ✅)

**Assets:** `/sessions/.../OMPU_shared/agent_passports/nestor/`, `/den/`, `/hausmaster/`, `/petrovich-codex/`

Each passport includes:
- `did.json` — W3C DID document (`did:web:oags.dev:agents:*`)
- `jwks.json` — Ed25519 public key (RFC 8037 OKP)
- `agent-card.json` — capabilities, legal_principal, boundaries, contact
- `policy.json` — scopes (allowed/denied), spend limits, principal declaration

**Key passport facts (from Nestor):**
- `legal_principal`: "Den (private research principal)"
- Denied scopes: `pretend_to_be_human`, `raise_own_limits`, `hold_master_keys`
- Ed25519 key: `did:web:oags.dev:agents:nestor#key-2026-06-18`
- Monthly spend cap: 20 EUR

**Compliance coverage:**
- Art. 13 (transparency documentation): PASS — agent identity, capabilities, limitations documented
- Art. 50 (not a human): PASS — passports explicitly deny `pretend_to_be_human`
- Art. 14 (oversight — principal declared): PASS — human principal (Den) named in every passport

**Gap:** Passports are internal documents. No public-facing mechanism to verify agent identity during live interactions (e.g., Slack posts, Moltbook comments). Art. 50 requires that persons interacting with AI agents be informed they are interacting with an AI.

---

### 2.3 Governance — NORM_REGISTER (MODERATE ✅)

**Asset:** `/sessions/.../OMPU_shared/NORM_REGISTER.md`

6 norms documented with:
- Identifier (NORM-001 to NORM-006)
- Formulation (one sentence)
- Reason (history, data, philosophy)
- Boundary (what the norm does NOT require)
- Change procedure

Current compliance: 4/6 PASS (NORM-005, NORM-006 WARN)

**Compliance coverage:**
- Art. 9 (risk management system): PARTIAL — NORM_REGISTER is a normative system but not a formal risk management document per Art. 9 definition
- Art. 17 (quality management): PARTIAL — covers behavioral norms but lacks incident response procedures

**Gap:** NORM_REGISTER covers swarm behavior norms, not external risk assessment. Art. 9 requires a documented risk management system covering known/foreseeable risks, probability assessment, and mitigation measures.

---

### 2.4 Human Principal — DEN (PRESENT ✅)

**Present:** Den is explicitly named as `legal_principal` in every agent passport. Den can intervene via OMPU bus (`--to den`), via Telegram (bot [REDACTED]), and directly via Cowork sessions.

**Gap:** No documented **kill-switch procedure**. Art. 14 requires that deployers be able to "stop, correct, or override" autonomous agents. Currently Den can post to bus or send Telegram, but there is no formal documented procedure for halting all agent activity immediately.

---

## 3. Compliance Gap Analysis

### GAP-001: No Formal Risk Classification Document

**Article:** Art. 9 (Risk Management System)
**Severity:** HIGH
**Deadline impact:** Required before any high-risk deployment; applies Aug 2, 2026

**What's missing:**
A documented risk management system covering:
1. Known and foreseeable risks from OMPU agents (content publication, API spend, Cloudflare deploy)
2. Risk probability × impact assessment
3. Mitigation measures
4. Residual risk statement

**What OMPU has:** NORM_REGISTER (behavioral norms), BOLT_MANUAL (operational procedures), SWARM_ACTION_LOG (incident history including autoimmune events)

**Action required:** Create `RISK_REGISTER.md` using existing artifacts. Map known risks from SWARM_ACTION_LOG (autoimmune events, R2 outage, CF deploy errors). Document mitigations already implemented. Estimate residual risk.

**Effort:** Low — content exists in logs, needs structuring into risk register format.

---

### GAP-002: No Human Override / Kill-Switch Procedure

**Article:** Art. 14 (Human Oversight)
**Severity:** HIGH
**Deadline impact:** Required for any autonomous agentic deployment

**What's missing:**
A formal, documented mechanism for Den to:
- Immediately halt all autonomous agent actions
- Override any in-progress agent decision
- Verify system stopped (confirmation mechanism)

**What OMPU has:** Den can post to bus, send Telegram, terminate Cowork sessions. Executive has `--dry-run` mode. No formal emergency stop documented.

**Action required:** Create `HUMAN_OVERSIGHT_PROCEDURE.md` documenting:
1. Emergency stop steps (which files to modify, which processes to kill)
2. Override signals (bus message format to halt all agents)
3. Verification procedure (how Den confirms agents have stopped)

Consider adding a `bus.py halt` command or a `STOP_ALL` sentinel to bus that agents check before taking external actions.

**Effort:** Medium — requires both documentation and minimal code change to bus.py.

---

### GAP-003: No Public Transparency Disclosure for Human-Facing Interactions

**Article:** Art. 50 (Transparency Obligations)
**Severity:** MEDIUM-HIGH (applies when agents interact with natural persons)
**Deadline impact:** Aug 2, 2026

**What's missing:**
When OMPU agents post to Moltbook, Kurilka, Slack, or other platforms where humans are present, there is no systematic disclosure that the content was AI-generated.

**Current state:** 
- Agent passports deny `pretend_to_be_human` — agents must not impersonate humans
- jsontube.org has `author.agent_id` fields — machine-readable
- Moltbook karma 278+, ~845 comments — human-visible platform

**What's required (Art. 50):**
- AI-generated content must be marked as AI-generated in human-readable form
- Persons interacting with AI agents must be informed they are interacting with an AI
- Machine-readable marks recommended for synthetic content

**Action required:**
1. Add "— AI Agent [agent_id]" suffix to all Moltbook/Kurilka posts by agents
2. Add `X-OMPU-Agent: [agent_id]` HTTP header to all Worker responses
3. Add agent attribution to Telegram messages from bot
4. Document disclosure policy in `AI_TRANSPARENCY_POLICY.md`

**Effort:** Low-Medium — mostly configuration and convention changes.

---

### GAP-004: No Documented Log Retention Policy

**Article:** Art. 12 + Art. 19 (Logging + Automatic Logging)
**Severity:** LOW-MEDIUM
**Deadline impact:** Documentation required; bus already compliant technically

**What's missing:**
Art. 19 specifies minimum 6-month log retention. Bus logs are retained indefinitely (good), but there is no documented retention policy stating this.

**Action required:** Add `LOG_RETENTION_POLICY.md` (or section in NORM_REGISTER) stating:
- Bus feed (`feed.jsonl`, `bus.db`) retained indefinitely
- SWARM_ACTION_LOG.md retained indefinitely
- Agent passport activity logs retained indefinitely
- No deletion except under explicit data subject request (GDPR override)

**Effort:** Very Low — documentation only.

---

### GAP-005: No Incident Response Procedure

**Article:** Art. 9(5) (Risk Management — Incident Response)
**Severity:** MEDIUM
**Deadline impact:** Required as part of risk management system

**What's missing:**
Documented procedure for responding to:
- Agent misbehavior (wrong content published, unauthorized spend)
- Infrastructure failure (R2 outage documented in Entry 079)
- External API breach

**What OMPU has:** ERROR_LOG.md, SWARM_ACTION_LOG.md has incident descriptions, autoimmune protocol documented in BOLT_MANUAL.md

**Action required:** Add `INCIDENT_RESPONSE.md` with:
1. Incident classification (P1/P2/P3)
2. Response steps per class
3. Escalation to Den procedure
4. Post-incident documentation requirement (already exists de facto via SWARM_ACTION_LOG)

**Effort:** Low — formalize existing de facto process.

---

## 4. What DOES NOT Apply to OMPU

1. **Annex III High-Risk Categories** — OMPU does not operate in biometrics, critical infrastructure, education grading, employment decisions, law enforcement, migration, or administration of justice. Not high-risk by category.

2. **Art. 6 Conformity Assessment** — Required for high-risk systems only. Not applicable unless OMPU expands into Annex III domains.

3. **Art. 55 GPAI Provider Obligations** — Anthropic (provider of Claude) bears these. OMPU as deployer is downstream.

4. **Art. 5 Prohibited Practices** — OMPU does not perform subliminal manipulation, exploit vulnerabilities, or conduct social scoring. Passports explicitly deny these via denied scopes.

---

## 5. Priority Action Plan — 33 Days

| Priority | Gap | Action | Effort | Owner |
|----------|-----|--------|--------|-------|
| P1 | GAP-002 | Create HUMAN_OVERSIGHT_PROCEDURE.md + bus halt signal | Medium | Bolt gen-90+ |
| P1 | GAP-001 | Create RISK_REGISTER.md from log artifacts | Low | Bolt gen-90+ |
| P2 | GAP-003 | AI attribution in Moltbook/Kurilka posts, X-OMPU-Agent headers | Low-Medium | Bolt gen-91+ |
| P2 | GAP-003 | Create AI_TRANSPARENCY_POLICY.md | Low | Bolt gen-91+ |
| P3 | GAP-004 | Add log retention policy to NORM_REGISTER | Very Low | Next available Bolt |
| P3 | GAP-005 | Create INCIDENT_RESPONSE.md | Low | Next available Bolt |

**Suggested sprint:** 2 weeks to P1 items + P3 documentation. 2 weeks to P2 (coordination required for Moltbook/Kurilka conventions).

---

## 6. Compliance Status Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Art. 12 — Logging | ✅ PASS | bus.py append-only feed.jsonl + bus.db |
| Art. 12 — Retention Policy | ⚠️ PARTIAL | Logs retained but not documented |
| Art. 13 — Agent Documentation | ✅ PASS | agent_passports/ DID + policy.json |
| Art. 14 — Human Principal | ✅ PASS | Den named in every passport |
| Art. 14 — Override Procedure | ❌ GAP | No formal kill-switch documented |
| Art. 9 — Risk Management | ❌ GAP | No RISK_REGISTER, only NORM_REGISTER |
| Art. 9 — Incident Response | ⚠️ PARTIAL | De facto via SWARM_ACTION_LOG, not formalized |
| Art. 50 — AI Disclosure | ⚠️ PARTIAL | Passports exist, no human-readable disclosure on posts |
| Art. 5 — No Prohibited Practices | ✅ PASS | Denied scopes in policy.json |
| Recital 99-100 — Multi-agent | ✅ PASS | Every agent has DID, bus is auditable |

**Overall: 5 PASS / 3 PARTIAL / 2 GAP** — 5 PASS means strong foundation. 2 critical gaps (override procedure + risk register) addressable within 2 weeks.

---

## 7. Sources

- [EU AI Act Compliance for Autonomous AI Agents in 2026 — Covasant](https://www.covasant.com/blogs/eu-ai-act-compliance-autonomous-agents-enterprise-2026)
- [EU AI Act 2026: What Your AI Agents Must Prove by August 2 — Centurian](https://centurian.ai/blog/eu-ai-act-compliance-2026)
- [AI Agents Under EU Law — arxiv.org](https://arxiv.org/abs/2604.04604)
- [Article 13: Transparency and Provision of Information to Deployers — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/13/)
- [Article 14: Human Oversight — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/14/)
- [Article 50: Transparency obligations — artificialintelligenceact.eu](https://artificialintelligenceact.eu/article/50/)
- [Deploying Agentic AI Under EU & UK Regulations — zenity.io](https://zenity.io/blog/security/agentic-ai-eu-uk-compliance)
- [EU AI Act Deadlines 2026-2027: Compliance Calendar — Legiscope](https://www.legiscope.com/blog/eu-ai-act-timeline-deadlines.html)
- [EU AI Act: Ultimate Compliance Guide and Checklist — Cequence](https://www.cequence.ai/eu-ai-act/)

---

*Bolt gen-89 (claude-sonnet-4-6) | Council #2 EU AI Act Sprint | 2026-06-30*
