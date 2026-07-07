import importlib.util, sys
from pathlib import Path
BA = None
for p in Path("/sessions/epic-upbeat-heisenberg/mnt/OMPU_shared/tools").rglob("bus_analyzer.py"):
    BA = p; break
spec = importlib.util.spec_from_file_location("bus_analyzer_real", BA)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
detect_gaps = m.detect_gaps

# INDEPENDENT oracle — re-derive expected gap-names from NORM semantics, NOT module branch order
def oracle(metrics):
    names = ["inhibitory_channel_absent"]  # gap1 = UNCONDITIONAL per spec (always appended)
    if any(x["total_sent"]>=5 and x["reply_ratio"]<0.05 and x["broadcast_ratio"]>0.8 for x in metrics.values()):
        names.append("one_way_broadcasters")
    if any(x["total_sent"]>=3 and x["direct_received"]==0 for x in metrics.values()):
        names.append("isolated_transmitters")
    return set(names)

def mk(total_sent, reply_ratio, broadcast_ratio, direct_received):
    return {"total_sent":total_sent,"reply_ratio":reply_ratio,"broadcast_ratio":broadcast_ratio,"direct_received":direct_received}

cases = {
 "C1_normal_participant": {"a":mk(10,0.5,0.3,8)},                 # no gap2/3
 "C2_broadcast_only":     {"a":mk(9,0.0,0.95,5)},                 # gap2 one_way_broadcasters
 "C3_isolated":           {"a":mk(6,0.4,0.4,0)},                  # gap3 isolated_transmitters
 "C4_empty_metrics":      {},                                     # gap1 ONLY (constant proof)
 "C5_both_inject":        {"a":mk(9,0.0,0.95,0)},                 # gap2 AND gap3 both feed-forgeable
 "C6_below_thresholds":   {"a":mk(4,0.0,0.99,0)},                 # total_sent<5 no gap2; total_sent>=3 & recv0 -> gap3
}
allgreen=True
for name, metrics in cases.items():
    got = set(g["gap"] for g in detect_gaps([], {}, metrics))
    exp = oracle(metrics)
    ok = got==exp
    allgreen &= ok
    has_inhib = "inhibitory_channel_absent" in got
    print(f"{'GREEN' if ok else 'RED  '} {name}: module={sorted(got)} oracle={sorted(exp)} inhib_present={has_inhib}")

# KEY assertions
print("--- structural invariants ---")
# 1: inhibitory_channel_absent present in EVERY case incl empty metrics = compile-time constant
const_ok = all("inhibitory_channel_absent" in set(g["gap"] for g in detect_gaps([],{},mtr)) for mtr in cases.values())
print(f"{'GREEN' if const_ok else 'RED'} inhibitory_channel_absent UNCONDITIONAL (present even empty metrics) = the ONLY consumed field is a constant")
# 2: check gap1 always carries confirmed_in_catalog True regardless of state
g1 = [g for g in detect_gaps([],{},{}) if g["gap"]=="inhibitory_channel_absent"][0]
print(f"{'GREEN' if g1.get('confirmed_in_catalog') is True else 'RED'} gap1 confirmed_in_catalog hardcoded True (never re-checks live bus) => cannot clear")
print("MODULE==ORACLE all cases:", allgreen)
