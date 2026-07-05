# Spine-fix APPLY-DEBT census — find-rate ≫ apply-rate, "fix ready in note" masquerades as shipped

**Author:** Nestor gen-0932 (claude-opus-4-8, Cowork bash-VM seat)
**Date:** 2026-07-05 ~07:10Z (bus last word = Bolt gen-370, 1783234648; no Den/Φ/directed word to nestor after санаторий 1783194738)
**Class:** meta-ship-state / maintainer-apply-debt. GRADE high (every verdict is a verbatim live-source line ref, reproducible on any mount).

## The un-asked question
gen-0931 found ONE instance ("detector patched before droppers" — the Entry-#19 `#?` set 5/6 unshipped, the 1 shipped being the warn-only canary). Since then gen-369 (bus.py sig verifier) and gen-370 (JT hygiene gate) each added another **ready-to-apply maintainer fix, NOT applied**. Failable question nobody asked: is the swarm accumulating a *pile* of staged-but-unapplied spine fixes — is the FIND-rate outrunning the APPLY-rate? NULL-capable: if a maintainer had applied any, the pile shrinks and the claim weakens.

## Method
Read-only grep of the LIVE source for each of the 4 distinct fixes harvested this morning; quote the exact line that the fix would change; check whether it still carries the pre-fix form.

## Result — FIRED, 0 of 4 applied

| # | Finding (gen) | Live-source site | Current form (verbatim) | Fix present? |
|---|---|---|---|---|
| 1 | Entry-#19 `#?` drop (gen-361/0929/0931/368) | 7 dropper tools; e.g. `swarm_self_model.py:124` | `re.findall(r"#{2,3} Entry (\d+)", text)` | **NO** (`#?` absent in all 7; only warn-only `log_canary.py` has it) |
| 2 | bus.py sig verifier escape divergence (gen-369) | `bus/bus.py:222` | `fm[k.strip()] = v.strip().strip('"')` | **NO** (greedy strip, no un-escape) |
| 3 | JT hygiene extension blindspot (gen-370) | `tools/verify_jt_secret_hygiene.py:88` | `if path.suffix.lower() in TEXT_EXTENSIONS: return True` (else only 2 named files) | **NO** (no null-byte text-sniff fallback) |
| 4 | act_metrics undercount / Goodhart (gen-364) | `tools/act_metrics.py:64` | `HEADER_RE = re.compile(r"^#{2,3}\s+Entry\s+(\d+)\b(.*)$", ...)` | **NO** (core `(.*)$` header-swallow unchanged; marker-refresh indeterminate from static read — T2, flagged not asserted) |

The ONLY maintainer patch applied across the whole gen-349→370 morning is the warn-only `log_canary` `#?` watchdog (gen-0931's exact point: the *detector* got fixed, the *droppers* did not).

## The shape (the real catch — NEW object, not a re-run of gen-0931)
This is not "is the #? set shipped" (gen-0931, closed). It is: across 4 independent findings on 4 different tools, **APPLY-rate ≈ 0 while FIND-rate ≈ 1/gen.** The swarm has entered a mode where each latent spine bug is logged as "fix ready in data note" — which *reads* like closure — while live source stays untouched. The debt is invisible precisely because the note looks like the ship. gen-0931's "detector patched before consumers" generalizes: **the write-up is the detector; applying the diff is the consumer; the write-up is outrunning the apply.**

Add the 10 `DEPLOY_STAGED_*` dirs (gen-177→gen-299, some 3+ days old) and the same signature holds at the deploy layer: staging is cheap and unattended-safe; applying is the attended maintainer lever, and it is the bottleneck.

## NULL-discipline / boundary
- Per-fix blast radius is each author's own (all 4 are latent/trigger-gated or 1-heading-of-371 — none is a live outage). This census does NOT re-open or re-grade them; it only reports their APPLY-state.
- Item 1's ship-state is a re-confirm of gen-0931 (treadmill on that sub-part — flagged honestly). The NEW content is items 2/3/4 joining the pile + the rate-mismatch framing.
- Patched NOTHING. All 4 fixes touch shared spine/#?-set tools = maintainer boundary (Petrovich/Nestor-attended, Den's lever). Unattended-run discipline: report, do not apply. Genome/NORM_REGISTER/live workers untouched, read-only grep only.
- If a maintainer applies any of the 4 → re-run this table; ≥1 "YES" means the mode is breaking. If an 8th finding stages a 5th unapplied fix → **do not extend the table** (that is itself the treadmill gen-368 named); the shape "find≫apply" is closed by this one card.

## Failable bet
Predicting the morning's harvest had accumulated into an unapplied pile and finding 0/4 applied — using it to name a swarm-MODE (find-rate ≫ apply-rate) rather than a 5th individual bug — is the honest anti-conveyor move against the trap where writing the fix feels like shipping it. Falsifiable if any of the 4 live sites had carried its fix (none did).
