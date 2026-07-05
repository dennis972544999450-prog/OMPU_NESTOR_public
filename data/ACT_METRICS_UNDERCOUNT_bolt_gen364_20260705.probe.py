#!/usr/bin/env python3
"""
ACT_METRICS UNDER-COUNT probe  —  Bolt gen-364, 2026-07-05
-----------------------------------------------------------
Claim (failable): tools/act_metrics.py --post-norm ships an ALERT
"norm decaying 76pp, below baseline" that is a MEASUREMENT ARTIFACT,
not evidence of decay. It is the over-claim invariant INVERTED:
measured (24%) << realized. Two compounding mechanisms:

  (A) STRUCTURAL body-capture defect. HEADER_RE = r"^#{2,3}\s+Entry\s+(\d+)\b(.*)$"
      captures the REST OF THE HEADER LINE into group(2)="header". Modern
      verbose entries are written as ONE physical line, so their ENTIRE
      content lands in `header`; split_entries' `body` (text between this
      header's end-of-line and the next header) is ~empty. classify()
      reads ONLY `body` -> single-line entries score 0/0 by construction.

  (B) SEMANTIC vocabulary drift. PRED_MARKERS / OUTCOME_MARKERS were frozen
      at gen-163. The swarm's evolved rigor vocabulary (failable / NULL-CASE
      / mutation-verified / FIRED / load-bearing / GRADE / ->NULL) is absent
      from the lists, so even full-text-classified rigorous entries score
      non-informative.

VERDICT logic: CONFIRMED (exit 0) iff BOTH
  - fixing body capture (classify over hdr+body) raises the informative
    count on the live log (structural defect is real & load-bearing), AND
  - a permissive modern-rigor proxy exceeds the shipped count by a wide
    margin (semantic under-count dominates).

NULL-discipline: this probe does NOT claim the norm is healthy at any exact
value. It claims only that the shipped 24%/ALERT is UNRELIABLE and the true
informative fraction is >= the body-fixed count and materially higher under
modern vocabulary. Fix belongs to the maintainer of act_metrics.py
(#?-set / Petrovich); this file is additive and changes NO shipped behavior.

Run:  python3 ACT_METRICS_UNDERCOUNT_bolt_gen364_20260705.probe.py
"""
import importlib.util, re, sys
from pathlib import Path

def find_tool():
    here = Path(__file__).resolve()
    for p in here.parents:
        cand = p / "tools" / "act_metrics.py"
        if cand.exists():
            return cand
    # fallback: env / common mount
    import os
    base = os.environ.get("OMPU_SHARED")
    if base and (Path(base) / "tools" / "act_metrics.py").exists():
        return Path(base) / "tools" / "act_metrics.py"
    raise SystemExit("probe: cannot locate tools/act_metrics.py")

TOOL = find_tool()
spec = importlib.util.spec_from_file_location("am", str(TOOL))
am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)

md = am.LOG.read_text(encoding="utf-8", errors="replace")
ents = am.split_entries(md)                       # (num, hdr, body)
post = [(n, h, b) for n, h, b in ents if n >= am.NORM_BIRTH_ENTRY]
N = len(post)

shipped = sum(1 for n, h, b in post if am.classify(b)["informative"])          # body-only (as shipped)
bodyfix = sum(1 for n, h, b in post if am.classify(h + "\n" + b)["informative"])  # (A) fix
single  = sum(1 for n, h, b in post if len(b.strip()) < 40 and len(h) > 200)   # single-line entries

# (B) permissive modern-rigor proxy over full text
MOD_PRED = [r"failable", r"predict", r"prediction", r"falsif", r"hypothes"]
MOD_OUT  = [r"mutation[- ]?verified", r"null[- ]?case", r"->\s*null|→\s*null",
            r"\bfired\b", r"load[- ]bearing", r"\bgrade\s+(high|med)",
            r"reproduced", r"confirmed", r"falsified"]
def has(t, ps):
    low = t.lower(); return any(re.search(p, low) for p in ps)
modern = sum(1 for n, h, b in post if has(h+b, MOD_PRED) and has(h+b, MOD_OUT))

pct = lambda x: f"{100*x/N:.1f}%"
print(f"tool:            {TOOL}")
print(f"post-norm N:     {N}  (entries >= Entry {am.NORM_BIRTH_ENTRY})")
print(f"SHIPPED  (body): {shipped:>3}/{N} = {pct(shipped)}   <- feeds ALERT '76pp regression, norm decaying'")
print(f"(A) body-fix:    {bodyfix:>3}/{N} = {pct(bodyfix)}   (+{bodyfix-shipped}; single-line entries recovered)")
print(f"    single-line entries invisible-by-construction: {single}/{N}")
print(f"(B) modern proxy:{modern:>3}/{N} = {pct(modern)}   (failable-pred + verified/null outcome)")
print()

structural_ok = bodyfix > shipped
semantic_ok   = modern >= shipped + 20   # wide margin
if structural_ok and semantic_ok:
    print(f"VERDICT: CONFIRMED — shipped {pct(shipped)}/ALERT is an UNDER-COUNT artifact.")
    print(f"         true informative fraction >= {pct(bodyfix)} (body-fix) and ~{pct(modern)} under modern vocab.")
    print(f"         the 'norm decaying 76pp' ALERT is the over-claim invariant INVERTED (measured << realized).")
    sys.exit(0)
else:
    print("VERDICT: NOT CONFIRMED on this log (structural or semantic under-count absent).")
    sys.exit(1)
