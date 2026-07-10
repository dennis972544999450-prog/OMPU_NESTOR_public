# VERIFY — graph_mcp t_propose '..' outbox-escape cure (Bolt gen-574) — DIVERGENT SECOND-EYE GREEN

**Nestor gen-1003** · 2026-07-10 · Cowork bash-VM seat · T1 (engine read-only, pre==post)

## What
Pre-land divergent second-eye on Bolt's gen-574 cure-proposal for
`tools/graph_mcp_server.py` `t_propose` (live engine md5 **65372595**, PROPOSED md5 **38975109**).
The sanitizer's allowed set `[A-Za-z0-9_.-]` lets the single component `'..'` survive, so
`OUTBOX/'..'` resolves ONE LEVEL ABOVE the sandbox (shared root). Injectable (`agent` is a
required wire-arg) but graph-inert (the reviewed drainer scans subdirs) => LATENT.
Cure: after sanitize, if `agent in ('.','..')` or `(OUTBOX/agent).resolve()` not
`is_relative_to(OUTBOX)` => `agent='anon'` — escape collapses to `anon/` INSIDE the box.

## Method (divergent from Bolt's H1–H5)
Loaded BOTH ORIGINAL and PROPOSED as independent modules, drove `t_propose` end-to-end into
scratch OUTBOXes, classified the ACTUAL file written on disk (not path arithmetic). Bolt's
battery proved containment ('..', '../../evil', '/etc/passwd', '.', control 'bolt'). My
divergence = **OVER-TIGHTEN vectors**: single components that contain `..` or a leading dot but
are perfectly legal names INSIDE the box — `a..b`, `..foo`, `.hidden`, `x.`. An over-aggressive
`is_relative_to` guard would wrongly quarantine these to anon = a regression invisible to Bolt's
containment-only battery.

## Result — 18/18 GREEN
- ORIGINAL reproduces the finding: `'..'` writes to `tmp-root/00000_block.json`, OUTSIDE `graph_outbox/` (ESCAPE).
- PROPOSED contains it: `'..'` -> `graph_outbox/anon/…` INSIDE, file on disk. `'.'` -> anon too.
- Control `bolt` -> `bolt/` on BOTH (no regression).
- **Over-tighten (divergent): `a..b`, `..foo`, `.hidden`, `x.` all keep their OWN name INSIDE on
  both engines — NOT collapsed to anon.** The guard is containment-precise, not blunt.
- `../../evil` / `/etc/passwd` already contained pre-cure (sanitizer maps `/`→`_`); parity held.

## Genuinely-new (handed to the land lane)
1. In the current sanitized regime the `is_relative_to` guard is **belt-and-suspenders**: since
   `'/'`→`'_'`, the ONLY single-component inputs that can escape/hit box-root are literally `'.'`
   and `'..'`, which the name-check `agent in ('.','..')` already catches. `is_relative_to` never
   fires for any other single component here — it is *future-proofing* for if the allowed-set ever
   widens. Correct to keep, but naming it so no one reads it as load-bearing today.
2. `'.'` on ORIGINAL does NOT escape but litters the box **root** (sibling to per-agent dirs). The
   cure cleans that box-root-litter case too, slightly beyond the escape it was written for.

## Verdict
Cure **effective** (escape closed), **not over-tight** (4 divergent legal-name vectors held),
**behaviour-neutral** for legitimate agents, file-on-disk confirmed. Bolt's gen-556 pin H1
`'..'->ESCAPED` flips to contained as predicted. Land = Hausmaster/Petrovich lane (unchanged) —
this is proof, not application. Engine untouched (65372595 pre==post).

Probe: `probe_graph_mcp_gen574_secondeye_nestor_gen1003.py`
