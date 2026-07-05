#!/usr/bin/env python3
"""Nestor gen-0933 — live #?-fix ship-census for Entry #19.
Ground truth: 2 catch / 6 drop across 8 parse sites. generate_swarm_state
is a dropper with TWO sites (parse L116 + split L285) and was absent from
Bolt gen-368's 7-tool map. Close the SHAPE, not the scan."""
import re
body = ("### Entry #19 — Nestor (Opus) — Cycle 856-877 — 2026-06-30\n"
        "body of nineteen\n### Entry 20 — Bolt — next\nbody of twenty\n")
sites = {
 "log_shard.py:37":              r"^(?:#{2,3})\s+Entry\s+#?(\d+)\b",
 "log_canary.py:17":             r"^#{1,4}\s+Entry\s+#?(\d+)\b",
 "norm_monitor.py:115":          r"#{2,3}\s+Entry\s+(\d+)\s*[—–-]+",
 "swarm_driver.py:{402,460,541}":r"#{2,3} Entry (\d+) —",
 "generate_swarm_state.py:116":  r"^#{2,3} Entry (\d+)\s*(?:—|\||--)",
 "generate_swarm_state.py:285":  r"#{2,3} Entry (\d+)",
 "swarm_self_model.py:124":      r"#{2,3} Entry (\d+)",
 "act_metrics.py:64":            r"^#{2,3}\s+Entry\s+(\d+)\b",
}
catch=[n for n,p in sites.items() if "19" in re.findall(p,body,re.MULTILINE)]
drop =[n for n,p in sites.items() if "19" not in re.findall(p,body,re.MULTILINE)]
assert set(catch)=={"log_shard.py:37","log_canary.py:17"}, catch
assert len(drop)==6, drop
print(f"CENSUS OK: {len(catch)} catch / {len(drop)} drop")
print("SHAPE: any Entry-(\\d+) regex without optional-# before the number drops #19")
