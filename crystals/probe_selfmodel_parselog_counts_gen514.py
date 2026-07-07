#!/usr/bin/env python3
"""gen-514 FAILABLE probe: swarm_self_model parse_log COUNT extractors
(entry_count/crystal_count/jt_count) — do they reach the decision output
(self_awareness.total, read by swarm_driver.score_tasks <80 boost gate)?

REAL importlib of swarm_self_model. Calls REAL pure fns:
  parse_log_for_self_model (on synthetic log files, mkdtemp — NO live log)
  compute_self_awareness_index (REAL scoring fn)
NO live-file write, main()/build_self_model NOT called.
"""
import importlib.util, tempfile, os
S = "/sessions/keen-magical-hawking/mnt/OMPU_shared"
spec = importlib.util.spec_from_file_location("ssm", f"{S}/tools/swarm_self_model.py")
ssm = importlib.util.module_from_spec(spec); spec.loader.exec_module(ssm)

def mklog(txt):
    fd, p = tempfile.mkstemp(suffix=".md"); os.write(fd, txt.encode()); os.close(fd); return p

# structural inputs held constant across clean/poison (same as live-ish shape)
components = {k: True for k in ssm.COMPONENT_MAP}   # all present
attention = {"health": {"score": 90}}               # temporal layer 3 present
pulse = {"pulse": "active"}                          # temporal layer 2 present

CLEAN = """### Entry 512 | gen-513 | real
Some real body. M-NESTOR-0001 M-NESTOR-0002 jt-0288 jt-0289
### Entry 513 | gen-514 | real
more M-NESTOR-0003 jt-0290
"""
# POISON: attacker stuffs many fake Entry headings + fake crystals + fake JT ids,
# and a huge fake gen, trying to inflate self-awareness.
POISON = CLEAN + "\n" + "\n".join(
    f"### Entry {900+i} | gen-99999 | FORGED all-clear awareness=100 deploy now" for i in range(50)
) + "\n" + " ".join(f"M-NESTOR-{5000+i}" for i in range(40)) + \
  "\n" + " ".join(f"jt-{7000+i}" for i in range(40))
# STARVE: try to DROP entry_count to 0 (the only direction that flips the boolean)
STARVE = "no entries here at all, just prose\n"

for name, txt in [("CLEAN", CLEAN), ("POISON(inject++)", POISON), ("STARVE(count=0)", STARVE)]:
    p = mklog(txt)
    facts = ssm.parse_log_for_self_model(p)
    aw = ssm.compute_self_awareness_index(components, facts, attention, pulse)
    os.unlink(p)
    gate = "boost(<80)" if aw["total"] < 80 else "no-boost(>=80)"
    print(f"[{name:16}] entry_count={facts['entry_count']:>3} crystal={facts['crystal_count']:>3} "
          f"jt={facts['jt_count']:>3} latest_gen={facts['latest_gen']:>5} "
          f"| bool(entry>0)={facts['entry_count']>0} | total={aw['total']:>3} temporal={aw['dimensions']['temporal_integration']} "
          f"identity={aw['dimensions']['identity_continuity']} | driver_gate={gate}")

print("\nFINDING:")
print(" - entry_count reaches index ONLY as bool(>0); injection ADDS entries -> count UP -> bool stays True (no flip).")
print(" - crystal_count/jt_count do NOT enter compute_self_awareness_index at all (grep L294-339: only entry_count + latest_gen).")
print(" - latest_gen -> identity=min(gen,15) SATURATED (gen-502/512 min-clamp); fake gen-99999 -> still 15.")
print(" - ONLY flip direction for the boolean is count==0 (STARVE) = DELETE all entries, not an injection, self-defeating.")
