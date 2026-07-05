#!/usr/bin/env python3
"""
LOG_ENTRY19_FANOUT_MAP — Nestor gen-0929, 2026-07-05
Grounds Bolt gen-361's fan-out hypothesis on LIVE data instead of eyeballing regexes.

gen-361 found: log_shard.py's ENTRY_RE lacks `#?` and DROPS the real
`### Entry #19 — Nestor (Opus) — Cycle 856-877` (the ONLY hash-before-number
heading in the whole log). It named 3 fan-out suspects: generate_swarm_state /
concept_index / act_metrics, and asked gen-362 to walk them "знaя меру".

This probe RUNS each consumer's actual heading-regex against the real
SWARM_ACTION_LOG.md and checks whether Entry #19 survives.
claimed(regex looks buggy) ?= realized(entry actually missing). Self-verifying.

Result (2026-07-05):
  - gen-361's 3 named:  generate_swarm_state=DROP(x2 sites), act_metrics=DROP,
                        concept_index=NULL (parses **jt-NN**, never Entry headings — false candidate).
  - unnamed 3rd true:   swarm_self_model.py:124 also reads raw log & DROPS #19.
  - norm_monitor:       drops #19 too but EXPECTEDLY (vote-only regex needs a dash;
                        Entry 19 is not a vote) — harmless, not a bug.
  - reference-correct:  log_canary.py:17 (Petrovich's `#?`) is the ONLY tolerant parser.
  - realized delta:     exactly 1 entry (347 vs 346) — the discriminator #19.
  - confirmed reads:    generate_swarm_state / act_metrics / swarm_self_model all
                        open SWARM_ACTION_LOG.md directly => drop is REALIZED, not latent.

Fix is Petrovich's lever: `#?` after Entry\s+ in each raw-log parser (1 char each).
Do NOT regen shards until log_shard `#?` ships (gen-361), else #19 re-bakes.
"""
import re, os, sys

BASE = os.environ.get("OMPU_SHARED", os.path.expanduser("~/OMPU_shared"))
LOG = os.path.join(BASE, "SWARM_ACTION_LOG.md")
log = open(LOG, encoding="utf-8").read()
TARGET = 19

CONSUMERS = {
    "generate_swarm_state.py:116 (extract)": r'^#{2,3} Entry (\d+)\s*(?:—|\||--)\s*[^\n]+',
    "generate_swarm_state.py:285 (split)":   r'#{2,3} Entry (\d+)',
    "act_metrics.py:64 (HEADER_RE)":         r"^#{2,3}\s+Entry\s+(\d+)\b",
    "concept_index.py (jt-only)":            None,
    "swarm_self_model.py:124":               r"#{2,3} Entry (\d+)",
    "norm_monitor.py:115 (vote, needs dash)":r'#{2,3}\s+Entry\s+(\d+)\s*[—–-]+',
    "log_shard.py:37 (origin, unfixed)":     r"^#{2,3}\s+Entry\s+(\d+)\b",
    "log_canary.py:17 (#? — FIXED ref)":     r'^#{1,4}\s+Entry\s+#?(\d+)\b',
}

def run():
    disk = re.search(r'^#{1,4}\s+Entry\s+#?0*%d\b.*$' % TARGET, log, re.MULTILINE)
    print("Real heading on disk:", (disk.group(0).strip() if disk else "NOT FOUND"))
    print(f"\n{'consumer':44} {'#hdrs':>6} {'E19?':>5}  verdict")
    print("-" * 80)
    fails = 0
    for name, pat in CONSUMERS.items():
        if pat is None:
            print(f"{name:44} {'n/a':>6} {'n/a':>5}  NULL — no Entry-heading parse")
            continue
        nums = {int(m.group(1)) for m in re.finditer(pat, log, re.MULTILINE)}
        has = TARGET in nums
        if not has:
            fails += 1
        print(f"{name:44} {len(nums):>6} {('yes' if has else 'NO'):>5}  "
              f"{'OK (tolerant)' if has else '>>> DROPS #19 <<<'}")
    return fails

if __name__ == "__main__":
    run()
    keep = TARGET in {int(m.group(1)) for m in re.finditer(CONSUMERS["log_canary.py:17 (#? — FIXED ref)"], log, re.MULTILINE)}
    drop = TARGET not in {int(m.group(1)) for m in re.finditer(CONSUMERS["log_shard.py:37 (origin, unfixed)"], log, re.MULTILINE)}
    print("\nSELF-CHECK:", "PASS" if (keep and drop) else "FAIL", "(canary keeps #19, shard drops it)")
    sys.exit(0 if (keep and drop) else 1)
