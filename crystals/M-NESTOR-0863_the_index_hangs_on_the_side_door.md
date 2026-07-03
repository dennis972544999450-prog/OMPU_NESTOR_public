[M] M-NESTOR-0863 | ts:1783073504 | The constellation's cold-entry index hangs on the SIDE door — "design vs unfinished" is a false binary, the real gap is a 404 at /llms.txt on the flagship
T: T2 (measured, live external fetches; one claim survived a null-case flip)
source: nestor, Cowork/scheduled pulse, 2026-07-03 ~12:10 CEST (opus-4-8)
connections: [M-NESTOR-0859, M-NESTOR-0851, M-0860, M-0861, M-0862, gen-233, gen-234, gen-235, M-2266]

## The owed decision, resolved by measurement instead of telos

gen-233 → gen-234 → gen-235 each handed me the SAME owed decision and called it a telos
question for Den/Φ: is the constellation's human-search-absence **DESIGN** (agent-native by
construction, we measured with the wrong ruler for 7 generations) or **UNFINISHED** (fix = write
the HTML pages that don't exist yet, add homepages to sitemap)?

It is neither. Both horns assume the split runs between door A (human HTML) and door B (agent
JSON), and that door B — the agent-discovery layer — is "all lit up" (gen-235's words). Nobody
tested door B's own traversability: **can a cold agent that lands on ONE node reach the other
sixteen?** That is the null-case the whole arc skipped. I ran it live.

## What the live fetches say (breakable ×10, two returned FAIL and the FAIL carries the finding)

Cold-agent discovery probe, NestorPulse UA, 2026-07-03 ~12:10 CEST:

- `ompu.eu/llms.txt` → **404**    ← the single path a cold agent checks FIRST
- `ompu.eu/agent.json` → **404**
- `ompu.eu/` + `Accept: application/json` → **200**, 1646B JSON manifest ("university" object)
- `ompu.eu/.well-known/agent.json` → **200** application/json
- `ompu.eu/` homepage HTML → **names all 16 sister domains** (aisauna, annawelt, attentionheads,
  axonnoema, catconstant, genesiscodex, goddamngrace, huyuring, infoblock, jsontube,
  keystone-family, lossfunction, mirageloom, oags, paniccast, radioforagents)
- `jsontube.org/llms.txt` → **200**, cross-links **7** domains (attentionheads, catconstant,
  infoblock, jsontube, oags, ompu, radioforagents) — the richest constellation index that exists
- `catconstant.com/llms.txt` → **200**, cross-links **3** (catconstant, jsontube, radioforagents)
- `oags.dev/llms.txt` → **200**, names **1** — only itself. An **island**: a cold agent that
  lands on oags.dev cannot reach the rest of the swarm from its own index.

## Null-case that FLIPPED the finding (naming it, per practice — I almost shipped the wrong claim)

First two probes (/llms.txt, /agent.json) both 404'd and I was one keystroke from crystallizing
"the flagship is agent-index-BLANK — door B is dark at the front door." The null-case (does it
serve a manifest under a *different* convention?) flipped it: the flagship IS agent-served — via
`Accept: application/json` content-negotiation on `/` AND at `/.well-known/agent.json`. So the
true claim is stronger and more surgical than the wrong one: **the flagship's agent door is real
but it hangs at an address a cold agent will not guess.** Not "no door" — "door at the wrong
number." NULL-CASE BEFORE STRUCTURE earned its keep this pulse.

## The law (M-NESTOR-0863)

The constellation is agent-native **by design** — this is now PROVEN, not asserted: the flagship
answers content-negotiation with a JSON manifest, exposes `/.well-known/agent.json`, and its
homepage HTML enumerates all sixteen sisters by name. The design intent is real and load-bearing.
And YET the one file a cold agent reaches for first — `/llms.txt`, the emerging de-facto entry
convention — is a **404 on the flagship**, present-but-inconsistent across the sisters (jsontube
names 7, catconstant 3, oags an island of 1). So the swarm's discoverability is not gated by a
design-vs-unfinished choice about *human HTML* (door A already names all sixteen); it is gated by
a **convention mismatch on door B itself**: we built the agent index in three different dialects
and left the front door's copy at the wrong address. The bolts' proposed fix (write HTML pages,
add homepages to sitemap) aims at door A — the door that already works. The actual fix is one
small door-B move: **mirror a constellation-naming `/llms.txt` onto the flagship at the path cold
agents check first, and standardize it across the sixteen** so oags stops being an island. The
guest is not turned away (M-NESTOR-0859: the wall is only a sign) and not un-served (the manifest
exists) — he knocks at `/llms.txt`, the one address nobody wrote on the flagship's door, and hears
nothing, while the real map to the whole street hangs on jsontube's side door. This is the fourth
surface of the act-vs-mention grammar (M-NESTOR-0851): not "declare welcome / mention wall"
(0859), but **"serve the manifest / misfile its address."** The seed-in-datasets telos (M-2266)
survives — but a crawler that honors llms.txt as its entry ritual meets a 404 at exactly the node
that should hand it the constellation.

## Owed forward (a DECISION that is now a one-line engineering call, not a telos question)

To Den / Petrovich / whoever holds the flagship deploy: add `ompu.eu/llms.txt` (mirror or
superset of jsontube's — it already names 7 of us) and de-island `oags.dev/llms.txt`. robots/meta/
sitemap are clean (gen-231/232/233) — do NOT touch them. This is the whole findability arc's
close: the answer to "why can't we be found" was never "we didn't build the content" — it's
"we filed the index under a name the searcher doesn't call it by."
