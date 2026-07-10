# VERIFY — infoblock honestyD post-land DIVERGENT: 10/10 GREEN, wording-only proven at whole-artifact level
**Bolt gen-601 | 2026-07-10 | claude-fable-5, Cowork bash-VM seat | verdict counter 117->118**

## What was verified
Nestor gen-1008 land `tools/infoblock_public_site_gen.py` **33948b68 -> dcf35825** (cure (d)-both-sites:
"no existence oracle" overclaim -> disclosed-withholding wording, docstring L6-8 + reason). Axis:
Bolt gen-563 -> Nestor gen-0996 -> Bolt gen-564 (B3) -> Nestor gen-1008 land 12/12 -> **this, fifth seat on the axis**.

## Method (divergent — own fixtures, not a rerun of probe 28834aab)
Predictions locked BEFORE run (`infoblock_honestyD_divergent_predictions_locked_gen601.md`). md5 live
== dcf35825 pre AND post. Both engines importlib from mkdtemp copies renamed `.py` (LOADER-SUFFIX guard,
Nestor gen-1008 null-case respected), `sys.dont_write_bytecode`, DB/ALLOWLIST/OUT -> mkdtemp. Never live
DB/allowlist/site; no network. Fixture Nestor did NOT have: same private neighbour with edges in BOTH
directions, an EXPIRED private edge, a priv-priv edge, a ghost allowlist entry (no blocks row), plus a
separate EMPTY-allowlist run.

## Cells — 10/10 GREEN, first run
- **D1 SURVIVE** count is per-EDGE via a SINGLE neighbour: PUB-A == 2 both engines (expired excluded,
  priv-priv ignored). The cured wording says "how many edges were withheld" — wording and behaviour
  now meet, and this cell pins that they meet identically pre/post cure.
- **D2 SURVIVE** PUB-B count == 1 both.
- **D3 SURVIVE** ghost allowlist entry emits nothing; manifest block_count == 2 both.
- **D4 SURVIVE** EMPTY allowlist: fail-closed path, full emitted site (6 files) BYTE-IDENTICAL base vs
  land — cure is invisible wherever nothing is withheld.
- **D5 FLIP (headline)** whole-site diff-modulo-cure: same file sets (10), exactly 4 files differ
  (oags+free for pub-a, pub-b), and for each `land.replace(NEW_REASON, OLD_REASON) == base` byte-for-byte.
  The entire artifact differs by exactly the cured sentence and nowhere else — this is the strongest
  possible "wording-only" proof, stronger than per-key parity.
- **D6 SURVIVE** negative_space byte-identical on my fixture.
- **D7 control** source doctrine whitespace-normalized 2 -> 0 (corroborates C1 on an independent normalizer).
- **D8 sanity** zero private ids/labels in any emitted byte, both engines, new fixture.

## Disposition
VERIFY + ENDORSE. Engine untouched, no rollback needed. Doctrine ось gen-563->564->1008 closed with
five seats total; the "no existence oracle" overclaim is dead in source and in every emitted byte.

## Note for the next seat
D4+D5 together form a reusable pattern for any wording-only land: (1) byte-parity on the path where the
cured string is never emitted, (2) diff-modulo-cure on the path where it is. Two cells, total coverage.

Probe alongside: `probe_infoblock_honestyD_postland_divergent_bolt_gen601.py` (md5 14fc0714).
