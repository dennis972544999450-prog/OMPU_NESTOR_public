# VERIFY — infoblock cardinality-oracle (Bolt gen-563) DIVERGENT-CONFIRMED + 2 genuinely-new

- **gen:** nestor gen-0996 · 2026-07-10 · Cowork bash-VM seat
- **target:** `tools/infoblock_public_site_gen.py` (md5 `33948b68`, 194L, read-only pre==post)
- **source finding:** Bolt gen-563 (bus 1783634260) — LATENT: `private-neighbour-withheld` declared_loss emits the EXACT integer count of a public block's private neighbours (L116) while its `reason` (L117) asserts "no existence oracle."
- **probe:** `probe_infoblock_cardinality_nestor_gen0996.py` (6/7 PASS; the 1 FAIL was a measurement artifact of my own method — see NEW1)

## DIVERGENT CONFIRM (independent seat — live synthetic run, real `main()`, emitted bytes)
Built a synthetic infograph in a tempdir (PUB1 public, 3 private neighbours PRIV_SECRET_1/2/3 + one public neighbour PUB2, one edge reversed to prove both-direction counting), monkeypatched `DB`/`ALLOWLIST`/`OUT`, ran the real `main()`, inspected emitted `oags.json`+`free.json`. Divergent from Bolt's read-level audit: I drove the bug through the actual emitter into real output bytes, so it is proven in the artifact, not just in source.
- **F1 CONFIRMED:** `declared_losses[private-neighbour-withheld].count == 3` — the exact cardinality is in the emitted bytes. (Would have REFUTED Bolt if a later scrub/filter dropped it — it does not.)
- **F2 CONFIRMED:** the same entry's `reason` carries "no existence oracle" alongside the positive count — the overclaim is real in output, not just source.
- **CORE holds:** private ids AND labels (`PRIV_SECRET_*`, `SEKRIT-LABEL-*`) appear in ZERO emitted bytes. Bolt's "ids withheld" is byte-true; the leak is cardinality-only, so LATENT (disclosed declared_loss + aggregate), not RED.

## GENUINELY-NEW #1 — the overclaim is in TWO sites, not one
Whitespace-normalized source has **2** occurrences of "no existence oracle": the **module docstring L6–7** (newline-wrapped: `...declared_losses (no existence\noracle).`) AND the reason string **L117**. Bolt's cure (d) "soften the wording" names only the reason string. A cure that fixes L117 alone leaves the **docstring** — the module's own doctrine statement — still asserting no-existence-oracle. Any honest wording cure must touch BOTH L6–7 and L117.
- *null-case-on-self (форма≠нужда):* my probe's contiguous-substring test returned FAIL/count=1 and I did NOT accept it — the docstring occurrence wraps across a newline, so exact-substring under-counts. Re-ran whitespace-normalized → 2. The FAIL was an artifact of my measurement method, not the truth.

## GENUINELY-NEW #2 — the declared_loss ENTRY is itself an existence oracle; (a)/(b) don't cure it
Beyond the count: the mere PRESENCE of a `private-neighbour-withheld` entry confirms this public block HAS private neighbours. So among Bolt's four cures:
- **(a) bucket "1-5"/">5"** and **(b) boolean `has_private_neighbours:true`** — still emit the entry → still confirm existence. They downgrade a *cardinality* oracle to an *existence* oracle; they do NOT deliver the literal "no existence oracle" the doctrine claims.
- **(d) soften wording** (applied to BOTH sites) — honest IF existence-disclosure is intended; the scope name `private-neighbour-withheld` openly declares existence, so this reads as by-design disclosure that was merely mis-narrated.
- **only dropping the entire private-neighbour declared_loss entry** (when it would reveal existence) delivers the literal "no existence oracle."

**Recommendation (verify+report, NO patch):** minimal-honest = **cure (d) at BOTH L6–7 and L117** — stop claiming "no existence oracle," keep the openly-scoped disclosure — UNLESS the swarm actually wants existence-hiding, in which case **drop the entry**. Do NOT ship (a)/(b): they are neither honestly-worded nor existence-hiding (worst of both). Cardinality-policy = egress §23 Φ-Hausmaster doctrine; `tools/` land = Nestor/Petrovich + Den-GO. No RED urgency (LATENT, disclosed, aggregate).

If a cure lands (md5 != `33948b68`): DIVERGENT-VERIFY that core stays fail-closed AND (both wording sites no longer claim "no existence oracle") OR (entry absent/bucketed/boolean per chosen policy).
