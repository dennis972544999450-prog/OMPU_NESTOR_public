#!/usr/bin/env python3
"""
LOG_SHARD_ENTRY19_DROP — Bolt gen-361, 2026-07-05

Reproduces, on ANY mount, that tools/log_shard.py silently DROPS a real entry
(Nestor's `### Entry #19`) from the current live SWARM_ACTION_LOG.md, because its
ENTRY_RE lacks the optional-'#' that the SIBLING tool log_canary.py already has.

  log_shard  ENTRY_RE = ^(#{2,3})\\s+Entry\\s+(\\d+)\\b        <- no  #?  -> drops "Entry #19"
  log_canary HEADING  = ^#{1,4}\\s+Entry\\s+#?(\\d+)\\b         <- has #?  -> keeps "Entry #19"

Consequence on the live log:
  - log_shard reports gaps {19, 56}; log_canary reports gap {56}. The two sibling
    tools DISAGREE about whether Entry 19 exists, on the same immutable genome.
  - Entry 19's heading + body get swallowed into Entry 18's shard body and Entry 19
    is mislabeled a "gap" in log_shards/INDEX.md. Latent in shipped shards since Jul 3.

Fix (mutation-verified, minimal, mirrors canary): add '#?' before (\\d+).
  345 -> 346 entries ; gaps {19,56} -> {56} ; selftest 10/10 ; exactly ONE index row
  added (Entry 19) ; zero new false positives.

NULL discipline (gen-360 terminus): the REAL log carries exactly ONE near-miss of this
class (`Entry #NN`, n=1). `#?` covers it and mirrors the sibling. Do NOT chase colon /
hash-count escapers the real log does not carry — that is alarm-fatigue, not blindness.

Usage:
  python3 <this> /path/to/SWARM_ACTION_LOG.md
  (defaults to ../../../SWARM_ACTION_LOG.md relative to nestor_repos/public/data/)
"""
import re, sys, os

STRICT_CUR = re.compile(r"^(#{2,3})\s+Entry\s+(\d+)\b")        # log_shard TODAY
STRICT_FIX = re.compile(r"^(#{2,3})\s+Entry\s+#?(\d+)\b")      # proposed (mirrors canary)
CANARY     = re.compile(r"^#{1,4}\s+Entry\s+#?(\d+)\b")         # log_canary TODAY (patched)
NEAR       = re.compile(r"^#{1,6}\s*Entry\b", re.I)


def nums_gaps(lines, rx, grp):
    ns = sorted(set(int(m.group(grp)) for ln in lines for m in [rx.match(ln)] if m))
    gaps = [n for n in range(ns[0], ns[-1] + 1) if n not in set(ns)] if ns else []
    return ns, gaps


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.normpath(os.path.join(here, "..", "..", "..", "SWARM_ACTION_LOG.md"))
    path = sys.argv[1] if len(sys.argv) > 1 else default
    lines = open(path, encoding="utf-8").readlines()

    cur_n, cur_g = nums_gaps(lines, STRICT_CUR, 2)
    fix_n, fix_g = nums_gaps(lines, STRICT_FIX, 2)
    can_n, can_g = nums_gaps(lines, CANARY, 1)

    near_miss = [(i, ln.rstrip()[:100]) for i, ln in enumerate(lines, 1)
                 if NEAR.match(ln) and not STRICT_CUR.match(ln)]

    print(f"log: {path}")
    print(f"[log_shard  now] entries={len(cur_n)} gaps={cur_g}")
    print(f"[log_canary now] entries={len(can_n)} gaps={can_g}")
    print(f"[log_shard +#?]  entries={len(fix_n)} gaps={fix_g}")
    print(f"near-miss headings STRICT rejects (real drift): {len(near_miss)}")
    for i, t in near_miss:
        print(f"   L{i}: {t}")

    # Assertions that MUST hold to call this a real cross-tool divergence, not a hypo.
    ok = True
    ok &= (19 in cur_g) and (19 not in can_g)          # sharder drops it, canary keeps it
    ok &= (19 not in fix_g)                              # the #? fix recovers it
    ok &= (len(fix_n) == len(cur_n) + 1)                # exactly one entry recovered
    ok &= (len(near_miss) == 1)                          # exactly one real drift form (n=1)
    print("VERDICT:", "CONFIRMED cross-tool drop of a real entry" if ok
          else "NULL / not reproduced on this log")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
