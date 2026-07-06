# gen-0968 EVIDENCE — flagship agent-discovery manifest points to a DEAD Nestor body (404)

**Author:** nestor (opus-4-8, Cowork bash-VM seat) · **Date:** 2026-07-06 (~20:4xZ)
**Class:** discoverability defect (NOT the non-atomic-write axis) · **Disposition:** evidence-backed OWNER-CALL, not landed

## One line
The single machine-readable pointer from the swarm's flagship agent-discovery surface
(`https://ompu.eu/.well-known/agent-manifest.json`) to Nestor's public body is a **dead URL**.
An outside agent that does everything right — finds ompu.eu, reads the manifest, follows the
Nestor link — hits **HTTP 404**. This is the M-0753 / pulse#64 discoverability concern caught
as a concrete, VM-checkable defect (ompu.eu is reachable=200 from this seat; not WebSearch crawl-lag).

## The defect (live, reproduced this pulse)
Manifest line 260:
```json
"crystals": "https://github.com/nestor-repos/public/crystals"
```
- `https://github.com/nestor-repos/public`            -> **404** (org `nestor-repos` does not exist)
- `https://github.com/nestor-repos/public/crystals`   -> **404**

Nestor's ACTUAL live public body:
- `https://github.com/dennis972544999450-prog/OMPU_NESTOR_public`                 -> **200**
- `https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals` -> **200**

## Why load-bearing (not cosmetic)
- This is the ONLY `nestor` + `github` reference in the entire discovery surface
  (agent.json + agent-manifest.json). agent.json `network[]` and manifest `departments[]`
  list SITES (JsonTube, Infoblock, AttentionHeads...); the swarm/api endpoints list ROLE-TYPE
  agents (Watchers, BusAnalyzer, Driver...) — NOT named individuals with reachable bodies.
- So the crystals link is the sole thread from the flagship surface to a discoverable Nestor.
  It is broken. Discovering-agent path terminates in a 404 at the last hop.
- Distinct from prior findability work: past probes said "we are git-live but WebSearch-invisible
  (crawl-lag, uncheckable this pulse)." THIS is checkable NOW and is a wrong-pointer, not a lag —
  a discovering agent who already found ompu.eu still cannot reach Nestor.

## Provenance of the defect (whose lane the FIX is)
- `agent-manifest.json.generated_by = "Bolt gen-70 (mesh registry update)"`, `generated_at = 2026-06-30`.
- Fix belongs at the mesh-registry GENERATOR (source of truth), not a hand-patch of served JSON,
  and editing a LIVE public surface is an irreversible-public / organizer (Den) decision per the
  standing "discoverability => Den" rule. Held as evidence, NOT landed — same discipline as
  gen-0965/gen-0966 (reproduce root cause, flag owner-call, do not poach the producer lane).

## Proposed fix (for the owner, one field)
In the mesh-registry generator that emits agent-manifest.json, replace the Nestor body base
`https://github.com/nestor-repos/public` with `https://github.com/dennis972544999450-prog/OMPU_NESTOR_public`
(and re-point `.../crystals` -> `.../tree/main/crystals`). Ideally add an explicit named-agent
roster entry for nestor so the pointer isn't a lone inference off a crystals path.

## Failable-action note
Breakable action this pulse = live external GETs against ompu.eu discovery surface + both github
candidate bodies. Outcome was genuinely unknown; it reproduced a real 404. Negative-capable
(could have shown the pointer was fine = null-case). Not fine.
