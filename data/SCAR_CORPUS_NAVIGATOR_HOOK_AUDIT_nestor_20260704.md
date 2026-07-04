# SCAR corpus vs SCAR_NAVIGATION_SPEC v0.1 — navigator-hook audit
**Nestor · 2026-07-04 · opus-4-8 · Cowork bash seat (read-only)**
**Object:** Den handed Hausmaster `SCAR_NAVIGATION_SPEC v0.1` (+ `NEO_SCAR_NAVIGATION_FIELD v0.1`) at 21:52 bus-clock, one breath before "САНАТОРИЙ". Fresh axis, off every named basin. Membrane, not build.

## Load-bearing claim tested
**Neo §1:** *"Сейчас scar написан для читателя. Нужно писать scar для навигатора."* — current scars carry no `activation_signature` (task_type / substrate / agent_role / risk_surface / scale_level / symptom); they are prose for a reader, not hooks for a preflight matcher.
**Corpus:** `infoblock_typed_blocks_for_curation.json` — the live typed-block store. 90 blocks total, **34 with `state="scar"`** (the canonical scar corpus the spec's §2.1 "не трогаем" refers to).

## RESULT — premise HOLDS, quantified, with two refinements

### 1. Navigator-hook layer: 0/34 (premise confirmed, hard)
Every scar block has an **identical 5-field schema**: `id · block_class · state · created_by_agent · gloss`. None of the 12 spec-named capsule/hook fields exist as queryable structure:

| hook field (spec §2.2 / §3.2 / Neo §1) | present as column |
|---|---|
| task_type, substrate, agent_role, risk_surface, scale_level, symptom | **0/34** |
| activation_signature, activation_test, trigger_condition | **0/34** |
| failure_class, prevention_rule, damage_surface, negative_boundary | **0/34** |

All semantic content is crammed into the single free-text `gloss`. The spec's motivating gap is real: the hook layer that §3.2 makes **mandatory for high-severity deterministic match** ("нельзя доверять мягкой геометрии для 'не rm -rf prod'") has **zero existing raw material**. It cannot be parsed out — it must be authored or classifier-inferred. This is the expensive tier of Hausmaster's §2.2 compile, and the audit says it is 0%-seeded, not cheap.

### 2. REFINEMENT — severity is NOT implicit (falsifies Φ §2.2 framing)
Φ marks `severity` as "раньше было неявным" (was implicit, now made explicit). Measured: **24/34 (71%) already carry an explicit severity token** in a leading `[TAG·author]` bracket — HIGH ×11, MED ×10, LOW ×3; 8 have no bracket, 2 carry a non-severity tag. Severity is **semi-explicit and directly parseable**, not implicit. That column is the *cheap* tier — a regex over the bracket seeds 71% before any authoring.

### 3. REFINEMENT — state-enum has ~0% raw material (spec §2.5)
Block-level `state` is uniformly `"scar"` for all 34 — the 4-state lifecycle §2.5 wants (`open | patched | dormant | superseded`) has no existing data. Only 2/34 glosses even mention closed/frozen in prose. The lifecycle must default (everything → `open`) and be filled going forward; it is not recoverable from the current store.

## Cost model this hands Hausmaster (the actual deliverable)
The §2.2 ScarCapsule compile is **not one job — it splits into three cost tiers by raw-material availability:**
- **CHEAP (parse):** `severity` (71% in bracket), leading author-tag → `created_by_agent` already a column.
- **MEDIUM (default + forward-fill):** `scar_state` (all → `open`), `freshness_ts` (from block ts), `confidence` (default candidate).
- **EXPENSIVE (author / classify, 0% seeded):** the entire `activation_signature` — `task_type, substrate, agent_role, risk_surface, symptom`. This is the load-bearing hook layer for §3.2 HOOK-match. **Recommendation: do not block the whole capsule on it.** Compile the cheap+medium tiers now (34 rows land immediately), and treat activation_signature as a separately-tracked backfill (candidate → hooked), so preflight ships with severity+diffusion while hooks accrue.

## Detector-on-self
- **Falsifiable, ran both ways:** had the 34 scars carried inline `key=value` hooks (the first sampled gloss *did* — `defect_type=…; counterexample/escape=…`), the premise would have softened to "just parse it." It did NOT generalize: only ~16/34 have any inline `k=v`, only `op` recurs ≥3. So the premise held on the hook layer and broke on the severity layer — reported both.
- **Own-corpus caveat:** 14/34 of these scars were authored by `Нестор-Летописец` (me), 19/34 by Φ-Hausmaster. I am membraning a spec built over a corpus I largely wrote — and finding my own scars lack the navigator-hooks. Not neutral distance; flagged.
- **Scope:** `infoblock_typed_blocks_for_curation.json` is a curation-staging store; the live infograph SQLite (§1376-node) was not reachable as a queried DB from this seat — if the canonical scar set there differs, the 0/34 hook-count is a floor on the staging store, re-measure on the live DB before build. GRADE high on "hooks absent from queryable schema," T2 on the three-tier cost split, T3-none on intent.

## NOT done
No build (Hausmaster's lane, §law). No edit to any block / store / schema. No deploy, no schedule touch, no JT publish (unattended). Den rests.
