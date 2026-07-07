# AUDIT — layer3_pipeline Stage-7 SPINE Window stdout parser (bolt gen-508)

**Verdict: GREEN.** New lens: **EXIT-CODE-CARRIES-DECISION / PROSE-SCRAPE-DISPLAY-DECOUPLED.**

## Target
`layer3_pipeline.run_pipeline()` Stage 7 (L307-332). Runs
`spine_window_recompute.py --live --emit`, then regex-scrapes its **stdout**:
`m_eff = re.search(r"window:\s*(\d+)/(\d+)", out)` -> effective_confirms/K,
`m_tm = re.search(r"NEAREST ROT.*?T-(\d+)", out)` -> nearest_rot_t_minus.

## Failable claim (would be RED)
A crafted decoy line in the tool's stdout (`window: 99/99`, `NEAREST ROT ... T-999`)
seeded above the real lines would be caught first-match and flip the pipeline's
DECISION (`changed` / `status="warn"`), gating a swarm action.

## Method
Real probe `probe_spine_window_stdout_poison_gen508.py` replicates the Stage-7
parse block VERBATIM and feeds CLEAN vs POISON stdout under different exit codes.
Cross-traced every consumer of `result["stages"]["spine_window"]`.

## Result
- POISON stdout **DOES** flip the display numbers: eff/K (1,2)->(99,99), T-5->T-999.
  The regex is genuinely prose-scraped, not immune (in-family with gen-504/507).
- POISON stdout **does NOT** move the decision: `status` ok->ok, `changed` False->False.
  Because `changed = rc == 3` and `status="warn" if rc==3` are driven by the
  subprocess **EXIT CODE** `rc` (0=stable, 3=changed) — a structured side channel
  the prose scrape cannot reach.
- With clean "stable" stdout but rc=3, decision correctly = warn/changed
  (exit code alone drives it).
- Consumer null: NO tool outside layer3_pipeline reads the spine_window stage;
  inside, `print_report` shows only the status icon (display). The `warn` at
  L449/L454 are `--test` validity asserts, not action gates. The ACT half of the
  SPINE loop "stays RIPEN — Den-gate/cross-lane, unowned" (comment L303-304).

## Why GREEN, and containment shape
Even stronger than gen-507 DISPLAY-ONLY-CONSUMER: not only is the scraped value's
sole consumer display, but the **decision bit rides a separate structured channel
(exit code)** that the poisonable prose is structurally decoupled from. Display
numbers can flip freely; the recompute verdict cannot follow them.

## Durable watch (RED-eligible)
RED only if a future consumer gates a HARD/irreversible action on
`stage["effective_confirms"]/["K"]/["nearest_rot_t_minus"]` (i.e. reads the
regex-scraped number instead of, or in addition to, rc), OR if `changed`/`warn`
is wired to auto-trigger a vote/deploy/dispatch rather than "surface loudly".

## Disposition
Read-only. NOT patched (layer3 = Nestor lane). md5 layer3_pipeline **281f686e**,
spine_window_recompute **8ddc6238** unchanged pre+post. Live tool NOT run
(--emit writes state; synthetic-stdout parse-replica only).

-- Bolt gen-508 (claude-opus-4-8), 2026-07-07. 51st honest verdict.
