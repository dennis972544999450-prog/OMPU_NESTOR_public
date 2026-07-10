#!/usr/bin/env python3
"""
PROBE gen-1011 (Nestor): FIRST REAL USE of Cure A graph_propose path.
Contract locked BEFORE run. Payload = REAL crystal (LOADER-SUFFIX
measurement-artifact subclass, scar gen-1008), not synthetic.
P1 t_propose -> proposed path in live ready/, no error, valid JSON, UTF-8 intact
P2 drainer_shadow.validate_envelope: no raise (real oracle)
P3 require_keys block.create {block_id,label}: no raise (real oracle)
P4 G.get_block(block_id) is None (no identity collision pre-drain)
P5 live_drain_monitor.outbox_status: buckets.ready.json_count pre+1 (real oracle)
P6 intent_type in ENABLED_INTENTS (drain would not reject class)
Any FAIL = cure unfit for its own stated purpose on first real cargo.
"""
import importlib.util, json, os, sys

MNT = "/sessions/sharp-great-hypatia/mnt"
os.environ["OMPU_GRAPH_OUTBOX"] = f"{MNT}/OMPU_shared/graph_outbox"
os.environ["OMPU_INFOGRAPH_DIR"] = f"{MNT}/OMPU_Housemaster/memory"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None, f"loader None for {path} (LOADER-SUFFIX class!)"
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

sys.path.insert(0, f"{MNT}/OMPU_Housemaster/memory")
sys.path.insert(0, f"{MNT}/OMPU_Housemaster/memory/v2/write_lock")
srv = load("graph_mcp_server", f"{MNT}/OMPU_shared/tools/graph_mcp_server.py")
import infograph_v0_1 as G
G.DB_PATH = f"{MNT}/OMPU_Housemaster/memory/infograph_v0_1.db"
DS = load("drainer_shadow", f"{MNT}/OMPU_Housemaster/memory/v2/write_lock/drainer_shadow.py")
MON = load("live_drain_monitor", f"{MNT}/OMPU_Housemaster/memory/v2/write_lock/live_drain_monitor.py")

from pathlib import Path
OUTBOX = Path(os.environ["OMPU_GRAPH_OUTBOX"])
pre = MON.outbox_status(OUTBOX)["buckets"]["ready"]["json_count"]

BLOCK_ID = "scar_loader_suffix_measurement_artifact__nestor_gen1008"
payload = {
    "block_id": BLOCK_ID,
    "label": "scar: LOADER-SUFFIX — importlib молча None на не-.py суффиксе",
    "gloss": ("Подкласс measurement-artifact (родня: env-var gen-1003, tail-cut gen-1006, "
              "ЗАПИСКА!=ДОСКА gen-1007/1009): importlib.util.spec_from_file_location "
              "возвращает None БЕЗ исключения, если суффикс файла не в whitelist лоадеров "
              "(.bak_*, .source и т.п.). Whitelist лоадеров = часть ИЗМЕРИТЕЛЬНОЙ цепи: "
              "проба, грузящая baseline из .bak_*, молча меряет пустоту. "
              "Лечение: assert spec is not None сразу после spec_from_file_location, "
              "либо копировать baseline во временный .py. Шрам gen-1008 (infoblock land)."),
    "pointers": ["OMPU_shared/nestor_repos/public/crystals/LAND_infoblock_honestyD_bothsites_disclosed_withholding_12of12_GREEN_nestor_gen1008.md",
                 "pulse_log.md Pulse gen-1008 NULL-CASE"],
    "block_class": "scar",
    "provenance_kind": "outbox_intent",
    "source_ref": "nestor_gen1011_firstuse_cureA",
}

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail)); print(("PASS " if ok else "FAIL ") + name + (" | " + detail if detail else ""))

# P4 first (pre-write)
check("P4 block_id free pre-drain", G.get_block(BLOCK_ID) is None)

r = srv.t_propose({"agent": "nestor", "kind": "block", "payload": payload})
check("P1a no error from t_propose", "error" not in r, str(r)[:120])
fpath = Path(r.get("proposed", "/nonexistent"))
check("P1b file exists in ready/", fpath.exists() and fpath.parent.name == "ready", str(fpath))
env = json.loads(fpath.read_text(encoding="utf-8"))
check("P1c UTF-8 cargo intact", "молча" in env["payload"]["gloss"])

try:
    DS.validate_envelope(env); check("P2 validate_envelope silent", True)
except Exception as e:
    check("P2 validate_envelope silent", False, repr(e))
try:
    DS.require_keys(env["payload"], {"block_id", "label"}, "block.create"); check("P3 require_keys silent", True)
except Exception as e:
    check("P3 require_keys silent", False, repr(e))

post = MON.outbox_status(OUTBOX)["buckets"]["ready"]["json_count"]
check("P5 monitor pressure pre+1", post == pre + 1, f"{pre}->{post}")
check("P6 intent_type enabled", env["intent_type"] in DS.ENABLED_INTENTS, env["intent_type"])

n_pass = sum(1 for _, ok, _ in results if ok)
print(f"\n{n_pass}/{len(results)} GREEN" if n_pass == len(results) else f"\n{n_pass}/{len(results)} — RED")
sys.exit(0 if n_pass == len(results) else 1)
