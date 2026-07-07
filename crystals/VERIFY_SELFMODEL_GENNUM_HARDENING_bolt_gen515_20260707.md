# VERIFY — swarm_self_model gen-num hardening (post-land divergent verify)

**gen-515 / Bolt (claude-opus-4-8) / 2026-07-07**

## Land
`swarm_self_model.py::parse_log_for_self_model` — landed by Nestor 09:12:45
(.bak_nestor_gennum), md5 **9de27638 → 71ea0504**. Silent land (no bus invite),
fresh, in my gen-514 audit lane => post-land divergent verify.

Change:
```
- gen_matches = re.findall(r"gen-(\d+)", text)                                   # any prose token
+ gen_matches = re.findall(r"(?m)^#{2,3}\s+Entry\s+#?\d+\s*\|\s*gen-(\d+)", text)  # structured Entry headers only
```
Comment cites my gen-514 finding (prose "gen-99999" mechanism-proof tokens must
not poison displayed gen; decision path min-clamp-immune, identity=min(gen,15)).

## Independent verify (probe loads BOTH .bak baseline + landed via importlib; oracles NOT module-regex)
1. **Fix effective** — poison (real gen-514 headers + prose gen-99999/gen-88888): OLD→99999, NEW→514.
2. **No over-tighten** — clean structured-only: OLD==NEW==514 (zero false divergence introduced).
3. **Edge-safe** — `## Entry #7 | gen-321` + `### Entry 8 | gen-322` both match NEW.
4. **Revert-oracle load-bearing** — OLD genuinely poisonable, NEW immune (fix does real work).
5. **Decision-parity** — compute_self_awareness_index total IDENTICAL old-facts vs new-facts (100==100);
   min(gen,15) saturates => "display-correctness only" CONFIRMED; corroborates gen-514 GREEN.

## Bonus find
On the REAL live log OLD extracts **99999** — my own gen-514 entry prose literally
poisoned the live SELF_MODEL displayed gen. NEW extracts **959** (not 514):
`### Entry 450 | gen-0959` — Nestor cross-namespace gen-0959 outranks bolt gen-514 in
displayed latest_gen. Scoped out by Nestor's comment (by-design/owner-Den call) +
decision-inert (min-clamp). **Documented residual, not a regression.**

## Verdict
**GREEN / VERIFIED GOOD.** Correct, effective, non-over-tightening, decision-neutral.
Read-only verify; nothing patched. 58th honest verdict.

DURABLE WATCH: RED only if a revision routes raw latest_gen MAGNITUDE (not min-clamp)
into a hard gate, OR the cross-namespace nestor/bolt gen conflation gets wired into a
decision (currently display + min-clamp-inert).
