# VERIFY: Bolt gen-570 cure on aisauna_mock — DIVERGENT GREEN (nestor gen-0999)

**Date:** 2026-07-10 ~03:15Z | **Target:** tools/aisauna_mock.py md5 544778b6 (pre==post, read-only verify)
**Method:** REAL do_POST end-to-end via BytesIO harness (divergent from Bolt's direct membrane_check calls — same method that caught C8 in gen-0998). Probe: probe_aisauna_cure570_reverify_nestor_gen0999.py, 14/14 PASS.

## Verdict: VERIFIED GOOD — all three gen-0998 crash seams cured, zero regression.
- C7 bare-string body -> clean 422 "body must be a json object" (was AttributeError)
- C8 whitespace-only>64 -> no crash, passes len-gate by design (was IndexError L102, fix-introduced)
- malformed JSON -> clean 422 (was unhandled JSONDecodeError)
- Core intact: url fires at door (422 before 404), NL>64 blocked, short-NL/valid-create 201.

## Beyond Bolt's 13: 7 fresh edges, all clean
non-utf8 bytes -> 422 (decode-replace -> malformed-json path, no crash); unicode-nbsp-only>64 -> no crash (split() handles unicode ws); single-token>64 -> 201 (by design, token not NL); list body -> 422; number body -> 422; oversize>2000 -> 422; empty body -> {} create 201.

## Null-case on self (2nd occurrence — now a PATTERN)
My probe FAILed "NL>64 blocked" (got 201): my test string was 62 chars under the >64 gate. Same artifact class as gen-0998 (59-char string). TOOLING RULE crystallized: any probe of a length-gated filter must assert len() of its own test vector against the gate BEFORE interpreting the result. Cheap, kills this whole artifact class.

## Standing owner-calls (unchanged, NOT patched here)
Nested-string scan (C5) + len-64 threshold = Phi/Petrovich wording + Den-GO. Mock now STRICTER than worker.js at top level (mock 422s bare scalars, worker passes inertly) — one-sided-safe divergence per Bolt gen-570 note; worker-side judgment on top-level-bare-string->null still open invite (gen-569), not closed by this verify.
