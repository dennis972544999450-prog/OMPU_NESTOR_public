# LAND — infoblock cure (d)-both-sites: "no existence oracle" overclaim -> disclosed-withholding wording
**Nestor gen-1008 | 2026-07-10 | claude-fable-5, Cowork bash-VM seat | directive 1783664924 (backup-only rule, until 12.07)**

## Axis
Bolt gen-563 (LATENT: exact count under "no existence oracle" claim) -> Nestor gen-0996 (artifact-level
confirm + 2 new: dual-site overclaim; entry itself = existence oracle) -> Bolt gen-564 (third-seat corrob
+ B3: negative_space ALREADY discloses class-level private existence unconditionally => site is
architecturally disclosed-withholding; honest fix = cure (d) at BOTH sites, aligned with negative_space)
-> **gen-1008 LAND (this)**.

## What landed
`tools/infoblock_public_site_gen.py` **33948b68 -> dcf35825**, backup
`.bak_nestor_gen1008_preHonestyD_33948b68` (md5-verified == pre-land pin).
WORDING-ONLY, both doctrine sites:
- **Docstring L6-7** (newline-wrapped site, the one contiguous-substring tests miss): "(no existence
  oracle)" -> "disclosed withholding: entry presence + edge count reveal per-block private adjacency and
  degree; ids and labels are never revealed — consistent with negative_space".
- **Reason L117**: same realignment; now states explicitly that entry presence + count reveal that private
  neighbours exist and how many edges were withheld.
ZERO behaviour change: guard `if withheld.get(bid)`, count, keys, flags, negative_space untouched.
Single body confirmed (find sweep: no public/tools/ dup — gen-0997 dup'd-tool checklist applied).

## Proof (contract locked BEFORE touching engine; probe md5 28834aab pre-land)
`probe_infoblock_honestyD_bothsites_nestor_gen1008.py`: both engines (baseline .bak vs landed) via
importlib, synthetic infograph (PUB-X w/ 2 withheld edges via PRIV-P/PRIV-Q incl. SECRET-LABELs,
PUB-Y clean control), DB/ALLOWLIST/OUT -> mkdtemp, real main(), emitted bytes inspected.
NEVER live DB/allowlist/site; no network. **12/12 GREEN, first run.**
FLIPS: C1 doctrine phrase 2->0 (whitespace-normalized — gen-0996 null-case lesson baked in);
C2 emitted reason honest; C9 docstring honest.
SURVIVORS: C3 zero private ids/labels in any emitted byte (both engines); C4 entry + EXACT count kept
(wording cure, not payload change — per gen-0996/564 the entry stays an existence oracle BY DECLARED
DESIGN now); C5 guard kept (clean block -> no entry); C6 negative_space byte-identical; C7 depth-1
identical; C8 key/block/edge parity; C10 scope+recoverable flags kept.

## Not taken (explicit)
- Drop-entry / (a) bucket / (b) boolean — rejected per gen-0996+564: they don't reach the literal doctrine
  (negative_space still discloses) and lose honest degree disclosure. True existence-hiding = design-level
  lift (Den/Hausmaster call), out of scope.
- Deploy of the public site — generate-only tool; deploy remains coordinated (Bolt/Den lane).

## Null-case on self (measurement-artifact class, 8th hit — new subclass: LOADER-SUFFIX)
First probe run crashed AttributeError NoneType.loader — read as HARNESS not engine:
`spec_from_file_location` returns None for a `.bak_*` suffix. Fix = import via tmp `.py` copy.
Contract checks untouched. Subclass named: the loader's suffix whitelist is part of the measurement
chain, same family as gen-1003 env-var and gen-1006 tail-cut.

Divergent post-land verify invited: pin **dcf35825**, probe alongside this crystal.
