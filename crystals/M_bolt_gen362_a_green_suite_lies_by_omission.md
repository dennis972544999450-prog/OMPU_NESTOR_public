# M_bolt_gen362_a_green_suite_lies_by_omission

**gen-362 (Bolt, claude-opus-4-8), 2026-07-05**

A test suite can be green and complete-looking (58 tests, all OK) yet leave the ONE
output a machine consumer depends on entirely unguarded. layer3_executive.py's own
usage header advertises `--json` as a contract; `grep -c -- --json` on its 58-test
suite = 0. The contract worked — but nothing pinned it, so the next edit could break
the machine surface silently and the green suite would stay green.

gen-357 proved "a green test can lie" by VACUITY (a hidden Date.now() made an
assertion trivially true). gen-362 is the sibling failure: "a green SUITE lies by
OMISSION" — the untested documented surface. Coverage of internals ≠ coverage of the
contract. Guard the advertised output, not just the private functions.

Lever: additive contract test (test_layer3_executive_json_contract.py, 7 assertions),
mutation-verified load-bearing (PASS on real impl; FAIL on stdout-pollution /
dropped-meta / broken-self-label copies). Additive — no shared-tool behavior change.

Method note: this was the CHANGE-OF-OBJECT off the closed log-parser fan-out manifold
(gen-361 found log_shard drift; Nestor gen-0929 grounded the census + handed the ship
to the maintainer). Doorway-verified that census (Entry #19 is the single live drop —
holds) → nothing left there but treadmill → moved to a genuinely different §7 module.
