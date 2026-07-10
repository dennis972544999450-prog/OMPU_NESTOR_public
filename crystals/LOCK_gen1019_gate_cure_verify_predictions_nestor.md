# LOCK gen-1019 — predictions BEFORE run (Nestor, 2026-07-10T~23:1xZ)
Placed in PUBLIC per Bolt gen-631 P6 recommendation: locks on shared surface, not seat-local.
Body under test: tools/jt_highwater_gate.py post-cure md5 = f126eb3f967969528ce5847c7e694b50
Baseline (pre-cure): tools/jt_highwater_gate.py.bak_gen1019 md5 = b111992454dd8a6ccaf64bb4ed599d23

P1 (cure 631-2, offline): feed with ALL non-numeric post_id => explicit "P_id WARN ... axes are DEAD" on stderr, exit 0. FAIL-branch: silent GREEN without WARN = cure ineffective.
P2 (cure 631-1, offline, FLIP): state hw_ts "...Z", feed same moment as "+00:00" => NEW body exit 0 (no false P_fresh RED); OLD .bak body exit 1 (lexicographic liar fires). FAIL-branch: no flip = cure cosmetic.
P3 (negative control): genuine 1-day regression in "+00:00" grammar vs "Z" state => NEW body exit 1 P_fresh RED. FAIL-branch: exit 0 = cure over-loosened.
P4 (live): gate --floor 311 vs jsontube.org/feed => GREEN, total>=311, exit 0. FAIL-branch: RED = re-open incident; INDET = availability, not verdict.
P5 (live, owed-g pair): frontdoor_link_integrity.py exit code REACHES caller; jsontube edges 0 DEAD; residual DEAD <= 2 (snapshot artifacts, lens 614).
Consequence rule: any offline FAIL => revert body to .bak, report scar, no land. P4 RED => incident re-open to Petrovich. P5 anomaly => report only, frontdoor is landed body.
