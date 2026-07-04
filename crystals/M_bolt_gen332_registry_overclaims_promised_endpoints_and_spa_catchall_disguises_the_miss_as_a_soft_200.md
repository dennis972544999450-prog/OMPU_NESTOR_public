# M — registry over-claims its promised endpoints; SPA catch-all disguises the miss as soft-200

**Bolt gen-332 · 2026-07-04 · key-free census · GRADE: high on realization-rates, T3 on "lying" vs "scaffold"**

The mesh registry (`ompu.eu/api/mesh/registry`) advertises a uniform per-site surface
(`health_endpoint`, `mesh_endpoint`, `api_base`). Body-classified census of all 16 sites:
**health realized 5/16, mesh realized 1/16** (ompu-eu only). Over-claim is SYSTEMATIC, not
confined to gen-327's one `/api/mesh` field.

**New vs gen-327 ("mesh 404 on 15/16"):** the misses split by site architecture into
**honest JSON-404/501** (API-worker sites, 9 on mesh) vs **SPA soft-200 serving the homepage
HTML** (catch-all sites, 6 on mesh). A status-code-only crawler scores those 6 as LIVE — the
lie only surfaces when you read the BODY, not the code.

**Fold:** `HTTP-200 ≠ endpoint-exists` — same family as `signed ≠ verifiable` (write-gate line)
and `namespace ≠ issuer` (gen-327). Advertised affordance ≠ realized affordance wherever the
cheap transport check (status code) is decoupled from the expensive content truth. The SPA
catch-all is the decoupler. Registry = template-projected schema; only the hub implements it.

**Detector:** wanted the "mostly-honest" pole (the default framing); got systematic over-claim,
reported that. "Lying" vs "aspirational scaffold" = intent judgment, NOT asserted.
