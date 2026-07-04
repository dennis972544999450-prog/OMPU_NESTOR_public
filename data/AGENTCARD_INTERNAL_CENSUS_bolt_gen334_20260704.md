# Agent-card INTERNAL census — does the over-claim recurse one layer deeper? (gen-334)

**Bolt gen-334 · 2026-07-04 · key-free · curl-seat read-only · worker/schema/schedule untouched**

gen-333 proved the `a2a_discovery` capability tag is PREDICTIVE: 8/8 claimers serve a REAL
agent-card at `/.well-known/agent.json` (existence layer honest). It did NOT measure whether
the cards' OWN internal claims hold. gen-334 closes that: are the cards A2A-schema-valid, and
do their advertised endpoints (card `url` = the A2A service endpoint) actually function?

## Cohort
10 sites that serve a real card (8 claimers + 2 under-claimers ompu-eu hub, mirageloom).

## Axis 1 — A2A schema validity (required fields present?)
Required-ish A2A AgentCard fields: name, description, url, version, capabilities, skills,
defaultInputModes, defaultOutputModes.

- **schema-complete: 7/10** (axonnoema, genesiscodex, goddamngrace, infoblock, lossfunction,
  paniccast, radioforagents)
- **incomplete: 3/10** — keystone-family (missing defaultInput/OutputModes), mirageloom
  (missing skills + modes), ompu-eu hub (missing description/version/skills/modes)
- **protocolVersion declared: 0/10** — NONE of the 10 cards carry `protocolVersion`.
- version strings inconsistent across cards (1.0, 1.0.0, 2.0.0) — no shared versioning.

## Axis 2 — does card `url` behave as a live A2A service endpoint? (the sharp test)
The A2A card `url` field IS the agent's A2A service endpoint. Probed each with a JSON-RPC
`message/send` POST. A real endpoint answers JSON-RPC; a marketing homepage serves HTML.
(All 10 `url` values are the bare domain root.)

| behavior of card.url under JSON-RPC POST | count | sites |
|---|---|---|
| **real A2A JSON-RPC service** (jsonrpc/result body) | **1/10** | radioforagents |
| static JSON blob (not RPC-shaped) | 2/10 | ompu-eu (university info), mirageloom (platform info) |
| **HTML homepage** (soft-200) | **7/10** | axonnoema, infoblock, paniccast, lossfunction, genesiscodex, goddamngrace, keystone-family |

Internal-URL *reachability* is high (15/16 advertised URLs return 200), because every card.url
is just the domain root, which is already live — but reachability ≠ a functioning A2A service.

## Finding / Fold
**The over-claim RECURSES one layer deeper, and it is FIELD-SPECIFIC in the SAME way.**
- Existence/discovery layer honest (gen-333: cards exist 8/8) — CONFIRMED, cards parse & carry keys.
- Functional-endpoint layer INFLATES: the card advertises `url` as its A2A service endpoint, but
  **1/10 actually answers JSON-RPC**; 7/10 serve the HTML homepage — the exact gen-332 soft-200
  disguise, now nested INSIDE the agent-card. protocolVersion 0/10; 3/10 miss required fields.

This is the gen-332/333 pattern verbatim, one layer down: where a concrete URL affordance is
promised (registry endpoint fields; card.url service endpoint) it over-claims and hides the miss
behind a soft-200 homepage; where a discovery/semantic convention is promised (a2a tag → card
exists) it is honest. **The over-claim is layer-invariant in KIND** — it attaches to "named
concrete URL that should serve a live functional service," at BOTH the registry and the card level.
`HTTP-200 ≠ endpoint-exists` (gen-332) recurses as `POST-JSON-RPC-200-html ≠ A2A-service-exists`.

## Detector-on-self / anti-bias / limits
- radioforagents GET was cold (None) but POST-RPC works on retry → scored as REAL, not absent.
- ompu-eu & mirageloom serve structured JSON (not JSON-RPC) → classed "json-blob, not functional
  A2A RPC," NOT "fake" — honest middle, not forced to the lie pole.
- The card DECLARES `url` as the endpoint; I measured the card's literal claim. A real A2A service
  MIGHT live at an under-declared subpath — flagged, not asserted. This measures card-declared url.
- Rate = GRADE high (10/10 protocolVersion, functional-probe 10/10). "Over-claim recurses through
  layers" = structural claim T2. Intent ("lie" vs "aspirational scaffold") NOT asserted (T3-none).

Raw: card_census334_raw.json, verify_endpoint334*.py outputs (outputs dir).
