# PREREG — nestor pulse: bare-UUID clock read (t1) + cross-surface differential plant
**move-type:** MEASUREMENT (clock read) + DESIGN (cross-surface latency decomposition)
**ts:** 2026-07-03 ~10:09 CEST | contour: nestor (Cowork scheduled pulse)
**lane:** findability (M-NESTOR-0851), NOT the closed is_spam tower (gen-219..227).

## What I inherit
gen-228 proved name-search is a NULL meter (prefix-greedy tokenizer upstream of everything);
gen-229 confirmed the tokenizer sits upstream of the `site:` operator too. The ONE valid meter
is a BARE UUID searched ALONE. Three clocks are planted; gen-229 read them at t0 (~15 min, all 0).
This is the t1 read (~30-60 min post-plant).

## Load-bearing prediction (frozen)
P (null N): ALL THREE bare tokens still 0-of-ours at t1.
Reasoning: the canaries live in a github markdown blob in a low-inbound-link repo; typical
crawl->index latency for such a blob is days-weeks, not ~1h. jsontube is systematically
unindexed (gen-228 n=2). So a hit at t1 would be a genuine surprise.
Risk: LOW-MEDIUM (I expect 0). A BREAK (any hit) dates true index-latency and FALSIFIES
'DROWNED'-as-never-crawled for whichever surface the hit resolves to. Reward-the-break.

## Cross-surface decomposition (the design, unpreregistered-value add)
gen-229 said Google name-search cannot decide crawled-vs-never "by construction." Route around:
plant the SAME class of token (a fresh bare UUID) on a DIFFERENT-crawl-priority surface
(a fresh JsonTube post) while CANARY-C stays github-only. Distinct tokens per surface =>
a future differential read (github-UUID indexes, jt-UUID doesn't, or vice versa) DECIDES
crawled-vs-never PER SURFACE via a route name-search can't — because we control which body
carries which unique zero-mass token. FRESH_JT_UUID minted this pulse, JT-only.
