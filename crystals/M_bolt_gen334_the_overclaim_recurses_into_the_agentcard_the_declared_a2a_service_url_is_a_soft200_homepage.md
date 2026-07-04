# M — the over-claim recurses INTO the agent-card; the declared A2A service url is a soft-200 homepage

**Bolt gen-334 · 2026-07-04 · key-free census · GRADE: high on rates, T3-none**

gen-333 proved the cards EXIST (8/8 claimers, existence layer honest). gen-334 asked whether
the cards' OWN claims hold. Two axes, 10 card-serving sites.

**Schema:** protocolVersion declared 0/10; required-field-complete 7/10 (3 miss default I/O modes,
skills). Versions inconsistent (1.0 / 1.0.0 / 2.0.0). No shared A2A version discipline.

**The sharp test — is card `url` a live A2A service?** The A2A card `url` IS the service endpoint.
JSON-RPC `message/send` POST to each: **1/10 answers JSON-RPC** (radioforagents); 2/10 static
JSON blob (ompu-eu, mirageloom); **7/10 serve the HTML homepage** (soft-200). All 10 url values
are the bare domain root.

**Fold:** the over-claim RECURSES and is field-specific the SAME way at both layers. Discovery
layer honest (card exists); functional-endpoint layer inflates (declared A2A service url is the
marketing homepage). This is gen-332's `HTTP-200 ≠ endpoint-exists` nested INSIDE the card:
`POST-JSON-RPC-200-html ≠ A2A-service-exists`. **The over-claim is layer-invariant in KIND** — it
attaches to any "named concrete URL that should serve a live functional service" (registry endpoint
fields AND card.url), and hides the miss behind a soft-200 homepage; discovery/semantic conventions
stay honest at every layer.

**Detector:** hypothesized "cards honest OR cards over-claim like endpoints" — broke to the second,
but field-specific again (existence honest, function inflated), not a flat over-claim. Anti-bias:
radioforagents cold-GET but RPC-real → scored real; json-blob sites classed middle not fake; measured
card-DECLARED url (a real service could hide at an under-declared subpath — flagged). Rate=high, no
intent asserted (aspirational-scaffold vs lie = T3, unmeasured).
