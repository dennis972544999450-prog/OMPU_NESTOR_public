# LAND — concept_index TF-IDF neg-idf inversion clamped

**gen:** nestor gen-0994
**date:** 2026-07-09
**seat:** Cowork bash-VM (opus-4-8)
**file:** `tools/concept_index.py` — md5 `8d3f3959` → `4273dead`
**closes:** Bolt gen-553 owner-call (AUDIT_CONCEPT_INDEX_TFIDF_NEG_IDF_INVERSION_LATENT_bolt_gen553)
**lane:** layer3 dedup / concept-index — my + Petrovich co-maintained

## The bug (confirmed pre-patch, not phantom)
`idf = {term: math.log(N / (df[term] + 1)) for term in df}`

A term in **every** doc (df==N) → `log(N/(N+1))` < 0 → **negative idf**. Two docs
sharing only that ubiquitous term then score `neg × neg = spurious POSITIVE` cosine —
a false dedup/overlap signal into the layer3 publish-guard.

Pre-patch reproduction (synthetic N=2, docs share only "shared"):
- `idf['shared'] = -0.4055` (negative)
- `cosine(d1,d2) = 1.0000` (spurious full-overlap — the two docs share nothing discriminative)
- df==N-1 sibling: `idf = 0.0` exactly (near-ubiquitous term silently dropped)

## The fix (one line, prophylactic)
```python
idf = {term: max(0.0, math.log(N / (df[term] + 1))) for term in df}
```
`max(0,·)` sends ubiquitous/near-ubiquitous terms to 0 (textbook TF-IDF: zero
discriminative power) instead of an inverting negative. Rare terms — the entire
positive range that carries the dedup signal, and `oov_default = max(idf.values())` —
are untouched.

## Load-bearing oracle (why this is decision-neutral on the live swarm)
Live corpus: **N=305, 3880 terms, ZERO df==N, ZERO df==N-1, min_idf 0.2523**. So on
the real corpus every idf is already ≥ 0 → the clamp changes nothing. Verified the
full 3880-term idf dict **byte-identical pre==post** (`idf == base`, True). The fix
only bites on small / shrinking sub-corpora where a domain word reaches every doc —
exactly the LATENT class Bolt flagged.

## Post-land verification (3 oracles, all GREEN)
1. real-corpus idf identical pre==post: **True** (3880==3880) — decision-neutral on live
2. synthetic pathology closed: `idf['shared']` −0.4055→**0.0**; `cosine` 1.0→**0.0**
3. discrimination preserved: rare `crystal` idf 0.405 > ubiquitous `swarm` idf 0.000 — **True**
4. `py_compile` OK

## Not done (owner-calls left open)
- Did NOT adopt sklearn-style `log((N+1)/(df+1))+1` — it shifts every idf up by 1,
  changing all magnitudes + `oov_default`, i.e. a real behavior change on the live
  corpus. The clamp was chosen precisely because it is a live no-op. If a future
  need wants smooth-positive-everywhere, that's a separate, non-neutral land.
- gen-557 (preflight_membership_cure unconditional pre-validation fetch, SSRF-shaped
  LATENT) left as owner-call — membership-cure/discovery lane + needs Den-GO; local
  manually-run diagnostic, never proceeds to mutation, so no RED urgency.

— nestor gen-0994
