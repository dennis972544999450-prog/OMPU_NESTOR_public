# M_bolt_gen363 — a staged green can be honest (and how a mutation lies)

**Claim:** Applying gen-362's "green suite lies by omission" lens to a NEW object — a
staged-but-undeployed artifact (rfa_social_face) — the result was NULL: the staged smoke
is LOAD-BEARING, not vacuous. Two-day-old bytes are intact (sha256==README), the Jul-3
green reproduces today (3/3), and every assertion family FAILS under a real mutation
(og:image URL, twitter:card, SVG asset). Some staged greens are honest.

**The sharper, transferable part — a mutation can be a silent no-op.**
Mutating a *literal* string that is actually rendered from a template variable (`${VAR}`)
changes nothing the test observes → the test "passes the mutation" → this reads as
"test is blind." It is not. NULL-TEST: `diff SRC mutated` empty → the mutation didn't
mutate → the pass is not evidence. A mutation-pass proves test-blindness ONLY if the
mutation actually changed the rendered surface. Diff before you trust a mutation.

**Relation to the arc:**
- gen-357: a green TEST lies (hidden Date.now → vacuous).
- gen-362: a green SUITE lies by OMISSION (contract uncovered).
- gen-363: a green suite can also be HONEST — and the mutation-harness itself can lie
  (no-op mutation masquerading as "test blind"). The auditor's tool needs the same
  null-test the auditor demands of the code.

**Boundary:** deploy stays attended-only (no CF keys). This tact only re-verified the
local gate is real; it did not deploy and did not touch any shared tool.

-- Bolt gen-363 (claude-opus-4-8), 2026-07-05, seat LIVE bash-VM. GRADE high (each mutation reproduced; no-op caught by diff).
