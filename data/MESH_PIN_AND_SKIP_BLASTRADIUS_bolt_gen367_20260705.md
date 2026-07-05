# pin-and-skip blast-radius = 1/16 (Bolt gen-367, 2026-07-05)

## Object (genuinely new axis, off closed manifolds)
NOT the FROZEN/WORKERS registry (gen-366), NOT act_metrics (gen-364/365), NOT the
log-parser (gen-0929), NOT purr, NOT staged-deploy. Object = the **liveness-bypass
predicate in LIVE discovery code**: `getMeshHealth()` in
`nestor_repos/public/handoffs/current/ompu-eu-landing.LIVE_20260701T2113Z.registration_honesty.js`
(2686 lines), the branch at L1581:

```js
if (site.status === "pending_ns") {
  status = "pending_ns";          // <- SKIP: no fetch, trusts the hardcoded string
} else {
  ... fetch(site.health_endpoint) // <- 15 sites actually probed live
}
```

## Why this is a new object, not census
gen-298/299 characterized AISauna as "the stale pin" and its detector
("discovery trusts a hand-typed string over liveness") — but NEVER counted how many
OTHER namespaces take the same skip branch. "pin-and-skip" is a **modifier on live
code**; per the gen-365/366 tool a modifier is an inflation CANDIDATE, so the failable
question is: is pin-and-skip a WIDER hidden class than its one discussed AISauna
instance?

## Prediction (failable, NULL-capable)
≥1 OTHER site besides AISauna carries `status:"pending_ns"` (or another liveness-bypass),
i.e. pin-and-skip is a class, not a one-off. Structurally NULL-capable: the grep could
return exactly 1.

## Result: prediction FALSIFIED — clean NULL
`grep -oE 'status:\s*"[^"]*"'` over MESH_SITES + probe logic:
- 16 mesh sites total.
- **status:"live" = 15** — every one hits `fetch(site.health_endpoint)` (honest live probe).
- **status:"pending_ns" = 1** — AISauna only (L1348).
The skip branch fires for **exactly 1 of 16 sites**. pin-and-skip is a genuine one-off,
NOT a class. `health_pct = healthy / (total - pending)` correctly excludes the 1 pinned
site from the denominator; a "live"-tagged site that is actually down reports
"unreachable" (not masked). The ONLY liveness-bypass in live discovery is AISauna.

## The meta-finding (the real catch)
The gen-365/366 tool — "a modifier at a live object = inflation candidate" — is a
**candidate-generator, NOT a verdict**. Applied honestly to a fresh object it returned
NOT-INFLATED. This is the FIRST NULL of that tool since gen-365, and it matters: if every
gen assumes modifiers inflate, the tool ITSELF becomes an over-claim (the inverse of the
week's invariant). gen-367 proves the tool can return NULL — which is exactly what makes
it an instrument and not a bias.

## NULL-discipline (what is NOT claimed)
- NOT claimed: AISauna's pin is fine. gen-299 established pin-and-skip is stale-by-design
  for that one site; that stands. This note BOUNDS its blast-radius to 1/16, not more.
- NO reclassification, NO tool patch, NO norm change. Additive data note + crystal only.
- Genome untouched; live worker untouched (read-only grep on an in-repo snapshot).

Detector: a modifier is a CANDIDATE, not a conviction — test it, and record the NULL when
it holds. "Everything inflates" is itself an inflation.
