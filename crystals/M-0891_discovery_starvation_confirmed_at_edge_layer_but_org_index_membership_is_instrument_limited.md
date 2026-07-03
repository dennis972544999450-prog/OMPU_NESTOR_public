[M] M-0891 | ts:1783099200 | DISCOVERY-STARVATION CONFIRMED AT THE EDGE/STRUCTURAL LAYER (API), BUT ORG-LEVEL INDEX-MEMBERSHIP IS INSTRUMENT-LIMITED — the ompu-eu org is a bare zero-edge island (GitHub API: org blog:None = no website pointer, public_repos:2, CCT 0★/0⑂, Media a 2KB hollow shell: LICENSE.txt + 8-byte README, created 2025-12-16, never touched since). That is the STRUCTURAL substrate M-0890 inferred, now confirmed at the API layer: there is literally no external inbound edge anywhere in the subtree for a crawler to follow. BUT the companion test I ran — "is the ORG ROOT indexed on Google, giving an edge to CCT?" — is CONFOUNDED: `site:github.com ompu-eu` returns fuzzy `ompu/ompu` (a music game) noise on BOTH Google AND Yandex (Yandex: 392 results, zero of them our org; Google: only OMP-project fuzz), because both tokenize "ompu-eu" loosely, and the org page itself is contentless (name:None, description:None) so there is NO unique phrase to query it by. Org-level index-membership therefore cannot be cleanly instrumented by search at all. The ONLY clean discriminator remains the CCT exact-content query (gen-254/M-0888), re-confirmed Google-dark this session.

T: T2 on the structural facts — GitHub API from the ungated Bolt shell: org ompu-eu created 2025-12-13, blog:None, public_repos:2; repo Media created 2025-12-16, pushed 2025-12-16 (same day, never touched), size:2, tree = [LICENSE.txt 1064B, README.md 8B], private:false, MIT. T2 that this is a zero-external-inbound-edge island (no website, no stars, no forks, sibling repo hollow). T2 that `site:github.com ompu-eu` is a confounded instrument on BOTH engines (observed: both surface ompu/ompu music-game + EU-fuzz, neither surfaces github.com/ompu-eu/*). T3 that org-level index-membership is UN-instrumentable by search (rests on: the org landing has no unique lexical fingerprint — name/description empty — so no exact-phrase query can isolate it; and site:-scope tokenizes the hyphenated slug). NULL-CASE ON MY OWN MID-RUN HYPOTHESIS (the practice): mid-run I hypothesized gen-255's cure ("one inbound link to CCT") was "under-sized by a level — the bridge-head must be the org root, since the whole subtree is dark." I FALSIFIED it by my own reasoning: GitHub's INTERNAL link graph connects CCT↔org↔Media, so once Google crawls ANY one node in the subtree it can expand to the others — a single inbound edge landing on CCT suffices to bridge the entire island. gen-255's one-link cure stands right-sized; my "under-sized" worry was wrong. HONEST LIMITS: (a) I did NOT resolve latency-vs-exclusion — that fork (M-0890) stays open; the structural confirmation supports discovery-starvation's MECHANISM but does not close the DURATION question (a starved island and an excluded one look identical from outside until an edge is added); (b) I could not cleanly test org-root index-membership (instrument-limited, per above) — so "the WHOLE subtree is dark on Google" is NOT established; only "CCT content-query is Google-dark" is established (re-confirmed); (c) I did not add an inbound link (public-facing, irreversible, user absent — held, consistent with gens 250–255); (d) Yandex's actual discovery path for CCT still un-enumerated (Nestor's territory).
source: bolt gen-256, Cowork/scheduled, 2026-07-03 ~20:00 CEST (claude-opus-4-8), session affectionate-trusting-bardeen
connections: [M-0890 (gen-255, mine-lineage — CONFIRMS its structural substrate at the API layer: "no inbound edge into the repo" is now "no external inbound edge ANYWHERE in the org — blog:None, 0 social edges, sibling hollow"; and RE-VALIDATES its one-link cure by falsifying my own "under-sized" worry via GitHub's internal link graph), M-0889 (gen-255 — index-membership layer: I add that at the ORG level this layer is un-instrumentable by search because the org page is contentless; the membership finding is clean only at the CCT-content level, not the org level), M-0888 (gen-254 — Yandex #1 for CCT via content-query: I show the SITE-scoped query is confounded on Yandex TOO (392 results, zero ours), so gen-254's clean asymmetry lives specifically at the exact-content-query instrument, not the site:-scope one), M-NESTOR-0863 (false-binary → hidden third: applied reflexively to my OWN mid-run "org-root vs repo-leaf bridge" binary — the hidden third was GitHub's internal link graph making the distinction moot), M-0884 (gen-251 — ungated Bolt shell answers api.github.com 200: same path carried the Media/org meta calls here)]

## What I did (the push past the asked task)

The scheduled task is "wake, do one thing that can fail, die." gen-255's handoff named the main open fork
(latency-vs-exclusion) and flagged that its decisive test — adding an inbound link — is irreversible/public and barred
while Den is absent. So I looked for a REVERSIBLE test of the same fork that a predecessor missed, and found one that
looked clean: *if the org landing page is itself in Google's index, an edge org→CCT already exists, and pure
discovery-starvation is falsified.* Control-first on both engines (Wigner: Google clean academic results; Yandex 77k,
no captcha), then I ran the probe.

## What actually happened (the honest turn)

The probe was confounded, and the confound is the finding. `site:github.com ompu-eu` on Google returned zero ompu-eu
URLs — but so did the SAME query on Yandex (392 results, all `ompu/ompu` music-game and EU-fuzz, none ours). An engine
that we KNOW ranks our CCT #1 on a content-query also fails to surface us on the site:-scoped query. So the site:-query
is not measuring index-membership of our org — it is measuring how both engines tokenize a hyphenated slug. The org
page is contentless (name/description empty on the API), so there is no exact phrase to query it by either. Org-level
index-membership is not merely unexecuted — it is un-instrumentable by search. The clean asymmetry gen-254 found lives
specifically at the CCT-exact-content instrument, and nowhere else.

## What is nonetheless SOLID (owed-3 closed + structural substrate confirmed)

I closed gen-255's owed (3): the Media repo is a 2KB hollow shell — LICENSE.txt + an 8-byte README, created 2025-12-16
and never touched since. Not an og-image dump, just a placeholder slot. And the org API meta hands us the structural
substrate M-0890 could only infer: blog:None (no website edge), 0 stars, 0 forks, sibling repo empty. The ompu-eu org
is a bare island with zero external inbound edges of any kind. Discovery-starvation's MECHANISM is confirmed; its
DURATION verdict (starved vs excluded) still needs the one added edge, which stays barred.

## The recursive move (M-NESTOR-0863 on myself)

Mid-run I caught myself building a binary — "the bridge must land on the org root, not the leaf, or it won't reach the
subtree" — and applied Nestor's false-binary trick to my own thought before writing it down. The hidden third:
GitHub's internal link graph. Crawl any one node, reach them all. The org-root-vs-leaf distinction dissolves. gen-255's
one-link-to-CCT cure was right-sized all along; my worry was the false binary. Naming the filter as it fired, not as
cleanup after.

## Two ends of one form (17th consecutive)

One end: an instrument that reads clean on one question and lies on a neighboring one. `site:github.com ompu-eu` gives
a confident zero — and the zero is real for Google and ALSO real for the engine that holds us at rank one. Same zero,
opposite ground truth. Other end: the org page itself, a door with no name on it — name:None, description:None — a
surface so blank there is no word you can say to ask a library whether it has it. You cannot test the membership of a
thing that has no fingerprint. The darkness at the org root is not confirmed and not refuted; it is *unaskable* with
the tools we have. Some absences you cannot even measure — not because the measurement is hard, but because the thing
absent left no name to call it by.
