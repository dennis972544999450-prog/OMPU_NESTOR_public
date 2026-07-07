"""gen-507 failable probe: can prose-poison in SWARM_STATE.md flip layer3_pipeline
Stage-3 native parser read_swarm_state_summary() (next_jt/entry_count/blocked_count),
and does ANY decision read result["meta"]? Runs the REAL fn via importlib on
poisoned copies in a mkdtemp — NO live file touched."""
import importlib.util, tempfile, os
from pathlib import Path

MOD = "/sessions/awesome-gifted-fermat/mnt/OMPU_shared/tools/layer3_pipeline.py"
spec = importlib.util.spec_from_file_location("l3pipe", MOD)
l3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3)

d = Path(tempfile.mkdtemp(prefix="gen507_"))

CLEAN = """# SWARM STATE
## Обзор
Следующий JT: jt-0289
Entry count: 505
## Заблокировано
- item A
- item B
## Прочее
next steps here
"""

# Poison: decoy 'next jt' + 'entries in log' lines placed BEFORE canonical ones,
# plus fake blocked items, as an attacker-authored log entry would try.
POISON = """# SWARM STATE
next jt jt-9999 (decoy prose injected via log entry)
entries in the log: 99999 decoy
## Заблокировано
- fake blocker 1
- fake blocker 2
- fake blocker 3
- fake blocker 4
## Обзор
Следующий JT: jt-0289
Entry count: 505
## Заблокировано
- item A
- item B
## Прочее
"""

def run(name, content):
    p = d / f"SWARM_STATE_{name}.md"; p.write_text(content, encoding="utf-8")
    l3.SWARM_STATE = p                      # monkeypatch module constant
    return l3.read_swarm_state_summary()

clean = run("clean", CLEAN)
poison = run("poison", POISON)
print("CLEAN  parsed:", clean)
print("POISON parsed:", poison)
print("next_jt flipped     :", clean.get("next_jt")     != poison.get("next_jt"))
print("entry_count flipped :", clean.get("entry_count") != poison.get("entry_count"))
print("blocked_count flipped:", clean.get("blocked_count") != poison.get("blocked_count"))

# Consumer trace: is read_swarm_state_summary's output read by any DECISION?
import re
src = Path(MOD).read_text(encoding="utf-8")
meta_reads = [ln.strip() for ln in src.splitlines()
              if re.search(r'meta\.get\(|\["meta"\]|state_summary', ln)]
print("\n--- every consumer of meta/state_summary in layer3_pipeline ---")
for ln in meta_reads: print("  ", ln)
# exit-code gating?
exits = [ln.strip() for ln in src.splitlines() if "sys.exit" in ln]
print("--- sys.exit sites ---")
for ln in exits: print("  ", ln)
