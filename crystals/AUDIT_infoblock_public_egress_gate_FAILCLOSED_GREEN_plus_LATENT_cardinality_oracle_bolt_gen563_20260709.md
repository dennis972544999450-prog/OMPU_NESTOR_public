# AUDIT — infoblock_public_site_gen.py: public-egress fail-closed gate GREEN + 1 LATENT cardinality-oracle

**gen-563 (Bolt, claude-opus-4-8) · 2026-07-09 · genuinely-new failable audit · LENS = PUBLIC-EGRESS FAIL-CLOSED (allowlist-only) + existence-oracle-claim accuracy**

## Target
`tools/infoblock_public_site_gen.py` (md5 **33948b68**, 194L) — Stage-1-bis generator that
projects the Hausmaster infograph (`infograph_v0_1.db`, read-only) into a STATIC PUBLIC
knowledge-graph site (`infoblock.org`). Doctrine (M-0730 / egress §23): a block is public
ONLY if on the affirmative `public_block_ids` allowlist (fail-closed); class-filter is NOT
the boundary; edges to non-public neighbours are dropped and DECLARED as `declared_losses`.

**Genuinely-new:** ZERO prior AUDIT crystal for infoblock. The existing
`verify_infoblock_public_site.py` is a known-bad-string DENYLIST smoke (checks a fixed
`FORBIDDEN_MARKERS` tuple), NOT an adversarial probe of the gate LOGIC. This audit probes
the gate itself with synthetic private content the denylist never enumerated.

## Method
Probe `probe_infoblock_public_gate_gen563.py` (md5 self-recorded, crystals/ + outputs).
importlib spec_from_file_location on the live engine; module globals
`DB / ALLOWLIST / OUT` redirected into `tempfile.mkdtemp()`; synthetic sqlite infograph
built with PUBLIC + PRIVATE blocks, a fake `ghp_…` secret embedded in a private block's
gloss AND in a public block's LATEST payload, public-public / public-private / private-private
edges, and an expired public-public edge. **NEVER** touches live `infograph_v0_1.db`,
live `infoblock_public_allowlist.json`, or live `infoblock_public_site`; no network; no
engine `__main__`. Engine md5 pre==post==33948b68 (unmutated). **18/18 PASS.**

## GREEN-CORE (privacy gate genuinely fail-closed — proven)
- No private block **id / label / gloss** appears in ANY emitted byte (scanned every file).
- Main loop iterates `sorted(public)` only; `pub_edges` are PUBLIC-PUBLIC only; scene blocks
  and scene edge endpoints are provably ⊆ allowlist (C3).
- Neighbour glosses suppressed (only the ENTRY block's gloss emitted, `[:600]`).
- Depth-in-depth `scrub()` fires: fake `ghp_` secret in the emitted public payload is
  replaced with `[REDACTED:key]` (belt-and-suspenders on top of the allowlist).
- Latest payload rev correctly selected (global `ORDER BY rev` ASC + per-key overwrite ⇒
  highest-rev row wins per block even with per-block rev restart — verified).
- Expired edge (`expired_at` set) excluded from projection.
- **Fail-closed on empty allowlist:** 0-block manifest, no `/infoblock/b/*` scenes, prints
  the fail-closed notice. Missing allowlist key ⇒ KeyError ⇒ crash-closed (nothing emitted).

## LATENT (owner-call — doctrine-accuracy / weak cardinality oracle, NOT an exploit)
The `private-neighbour-withheld` declared_loss emits the **EXACT integer count** of a public
block's private neighbours, while its own `reason` string literally says *"their ids are not
revealed (**no existence oracle**)."* The ids are indeed withheld (that half holds) — but a
**positive exact count is itself a cardinality existence-oracle**: it confirms private blocks
exist, are adjacent to this specific public block, and precisely how many. Over many public
blocks this leaks a private-degree distribution. Severity **LATENT** (not RED): the value is
DISCLOSED (it's a declared_loss, not hidden), it's a weak/aggregate signal, and no id or
content leaks. But the phrase "no existence oracle" is **overclaimed** relative to what's
emitted.

**Cure (NOT applied — owner-call):** (a) bucket/round the count (`"1-5"`, `">5"`) to blunt
cardinality; (b) emit a boolean `has_private_neighbours` instead of an exact int; (c) drop
the count entirely; or (d) soften the doctrine wording to "ids not revealed" and drop the
"no existence oracle" clause, since a declared count is intentionally an existence-count.
Minimal-honest = (d) align claim to emitted data, or (a)/(b) if cardinality-hiding is truly
desired.

## Disposition
verify+report, **NO patch/deploy** — infoblock *generation* is Bolt's lane but the doctrine
wording / cardinality-policy is a coordinated call (Nestor/Petrovich + Den-GO; egress §23 is
Φ-Hausmaster doctrine). Findings owner-actionable.

**If a cure lands** (engine md5 != 33948b68) ⇒ DIVERGENT-VERIFY with this probe: assert
core still fail-closed (no id/label/gloss leak, scene ⊆ allowlist, scrub fires, empty→empty)
AND the count is now bucketed/boolean/absent OR the reason string no longer claims "no
existence oracle".

108th honest verdict (genuinely-new failable audit of a live PUBLIC-EGRESS surface;
GREEN-core proven by allowlist-subset + scrub + fail-closed-empty; one honest LATENT with
severity DOWN (declared weak oracle, not RED); owner-call no-patch > invented RED).
