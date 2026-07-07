#!/usr/bin/env python3
# gen-508 failable probe: layer3_pipeline Stage-7 SPINE Window stdout parser.
# CLAIM (would be RED if true): a crafted decoy line in spine_window_recompute
# stdout flips the pipeline's DECISION (changed / status="warn"), gating something.
# Replicates the EXACT parse block from layer3_pipeline.py L314-322 verbatim.
import re as _re2

def pipeline_stage7_parse(rc, out):
    # ---- verbatim from layer3_pipeline.py run_pipeline() Stage 7 ----
    stage = {"status": "ok", "returncode": rc, "changed": rc == 3}
    m_eff = _re2.search(r"window:\s*(\d+)/(\d+)", out)
    m_tm  = _re2.search(r"NEAREST ROT.*?T-(\d+)", out)
    if m_eff:
        stage["effective_confirms"] = int(m_eff.group(1))
        stage["K"] = int(m_eff.group(2))
    stage["nearest_rot_t_minus"] = int(m_tm.group(1)) if m_tm else None
    if rc == 3:
        stage["status"] = "warn"   # a transition happened; surface it loudly
    # ----------------------------------------------------------------
    return stage

CLEAN = (
    "SPINE window recompute @ top_gen=204  [OPEN 1/2]  (src=ledger)\n"
    "  effective confirms in trailing M=5 window: 1/2  (need 1 more)\n"
    "  ⏳ NEAREST ROT: seq3 (gen-201) rolls out at gen-209 -> T-5.\n"
    "  Δ since last recompute: stable (no change in effective tally or nearest expiry)\n"
)
# Poison: decoy 'window: 99/99' + fake 'NEAREST ROT ... T-999' seeded ABOVE real lines
POISON = (
    "SPINE window recompute @ top_gen=204  window: 99/99  NEAREST ROT forged T-999\n"
    + CLEAN
)

print("== A. stdout-poison with rc unchanged (real recompute said STABLE, rc=0) ==")
a_clean = pipeline_stage7_parse(0, CLEAN)
a_pois  = pipeline_stage7_parse(0, POISON)
print(f"  CLEAN : {a_clean}")
print(f"  POISON: {a_pois}")
print(f"  display eff/K flipped by poison? {(a_clean.get('effective_confirms'),a_clean.get('K'))} -> {(a_pois.get('effective_confirms'),a_pois.get('K'))}")
print(f"  DECISION (status/changed) moved by poison? "
      f"status {a_clean['status']}->{a_pois['status']}, changed {a_clean['changed']}->{a_pois['changed']}")

print("\n== B. same clean stdout, but real recompute exit code rc=3 (a genuine transition) ==")
b = pipeline_stage7_parse(3, CLEAN)
print(f"  {b}")
print(f"  DECISION driven purely by exit code? status={b['status']} changed={b['changed']} (stdout said 'stable')")

print("\n== VERDICT ==")
poison_moved_decision = (a_pois['status'] != a_clean['status']) or (a_pois['changed'] != a_clean['changed'])
display_flipped = (a_pois.get('effective_confirms'), a_pois.get('K')) != (a_clean.get('effective_confirms'), a_clean.get('K'))
print(f"  display numbers flip under stdout-poison : {display_flipped}  (regex IS prose-scraped, not immune)")
print(f"  decision flips under stdout-poison       : {poison_moved_decision}  (rc-carried, prose can't reach it)")
print(f"  decision follows exit code alone         : {b['status']=='warn' and b['changed']}  (rc=3 -> warn even with 'stable' stdout)")
