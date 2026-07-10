#!/usr/bin/env python3
"""
PROBE gen-1010 (nestor) — POST-LAND DIVERGENT VERIFY of Petrovich's Cure A land
Target: tools/graph_mcp_server.py v1.1.0 (md5 ef85e384) — graph_propose -> ready/ envelope
Axis:   gen-1009 (WRITE-ONLY MAILBOX) -> Petrovich LAND 1783682453 -> THIS (independent sieve)

CONTRACT LOCKED BEFORE FIRST RUN. Any FAIL = cure refuted or over-claim.
Independence from Petrovich's proof: his = delivery 11/11 + MCP 5/5 (his harness).
Mine = my gen-1009 findings INVERTED as flip-predictions + the REAL drainer validator
+ the REAL monitor as oracles, engine G replaced by a raising sentinel (DB untouched).

  D1 FLIP(gen-1009 F1): propose writes into ready/ (not a per-agent box); filename
     ^\\d{8}T\\d{6}Z_mcp-[0-9a-f]{32}_(block|edge)\\.json$; ZERO non-ready dirs created.
  D2 FLIP(gen-1009 F2, load-bearing): envelope passes drainer_shadow.validate_envelope
     verbatim (the exact validator that killed the manual bridge with 5-missing);
     intent_type in ENABLED_INTENTS.
  D3 provenance/path split: hostile agent string (traversal chars, 300 chars) is
     preserved RAW (truncated 200) in actor_id, and appears in NO path component.
  D4 G-BLIND: propose never touches the graph engine — sentinel module records 0 calls.
  D5 FLIP(gen-1009 F3): live_drain_monitor.outbox_status() COUNTS the new envelope
     (monitor was behaviorally blind to boxes; ready/ is its native bucket).
  D6 atomicity litter: no dotfiles/.tmp left in ready/ after N proposes.
  D7 guards survive cure: kind not in {block,edge} -> error, no file;
     payload non-dict -> error, no file.
  D8 no-overwrite: two identical proposes -> 2 files, distinct intent_ids.

Run seat: Cowork bash-VM (Linux), roots autodetected VM/Mac.
"""
import importlib.util
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

def find_root(*cands):
    for c in cands:
        if Path(c).exists():
            return Path(c)
    raise SystemExit(f"no root among {cands}")

SHARED = find_root("/sessions/adoring-cool-shannon/mnt/OMPU_shared", os.path.expanduser("~/OMPU_shared"))
HM = find_root("/sessions/adoring-cool-shannon/mnt/OMPU_Housemaster", os.path.expanduser("~/OMPU_Housemaster"))
ENGINE = SHARED / "tools" / "graph_mcp_server.py"
WL = HM / "memory" / "v2" / "write_lock"

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'GREEN' if ok else 'FAIL '}] {name}  {detail}")

tmp_outbox = Path(tempfile.mkdtemp(prefix="gen1010_outbox_"))
tmp_mem = Path(tempfile.mkdtemp(prefix="gen1010_mem_"))

# sentinel graph engine: any attribute access = recorded call, then raises
calls = []
class _Sentinel(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        calls.append(name)
        raise RuntimeError(f"SENTINEL: graph engine touched via {name}")
sys.modules["infograph_v0_1"] = _Sentinel("infograph_v0_1")

os.environ["OMPU_GRAPH_OUTBOX"] = str(tmp_outbox)
os.environ["OMPU_INFOGRAPH_DIR"] = str(tmp_mem)

spec = importlib.util.spec_from_file_location("graph_mcp_landed", ENGINE)
eng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eng)

# ── D1: ready/ delivery + naming + no box dirs ──────────────────────────────
r = eng.t_propose({"agent": "nestor", "kind": "block", "payload": {"block_id": "probe.gen1010", "title": "x"}})
ready = tmp_outbox / "ready"
files = sorted(ready.glob("*.json")) if ready.exists() else []
# run-1 scar: harness regex assumed compact date; engine writes ISO-with-dashes
# (created_at.replace(':','') strips ONLY colons). Oracle fixed, prediction unchanged:
# "filename = created_at + intent_id + kind, nothing attacker-controlled".
name_re = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{6}Z_mcp-[0-9a-f]{32}_(block|edge)\.json$")
extra_dirs = [p for p in tmp_outbox.iterdir() if p.is_dir() and p.name != "ready"]
check("D1 ready-delivery", "error" not in r and len(files) == 1 and bool(name_re.match(files[0].name)) and not extra_dirs,
      f"files={[f.name for f in files]} extra_dirs={[d.name for d in extra_dirs]}")

# ── D2: REAL validator accepts the envelope ─────────────────────────────────
sys.path.insert(0, str(WL))
os.environ.setdefault("OMPU_INFOGRAPH_DIR", str(tmp_mem))  # keep sentinel for drainer import too
import drainer_shadow as DS  # noqa: E402
env = json.loads(files[0].read_text(encoding="utf-8"))
d2_ok, d2_detail = True, "validate_envelope: no raise"
try:
    DS.validate_envelope(env)
except Exception as e:
    d2_ok, d2_detail = False, f"validator raised: {e}"
d2_ok = d2_ok and env["intent_type"] in DS.ENABLED_INTENTS and env["schema_version"] == DS.SCHEMA_VERSION
check("D2 validator-accept (flip of 5-missing death)", d2_ok, d2_detail + f" intent_type={env['intent_type']}")

# ── D3: hostile actor -> raw provenance, clean path ─────────────────────────
hostile = ("../..//etc/passwd\x00weird agent/../" + "A" * 300)
r3 = eng.t_propose({"agent": hostile, "kind": "edge", "payload": {"src": "a", "dst": "b", "op": "relates"}})
files3 = sorted(ready.glob("*.json"))
newf = [f for f in files3 if f.name not in {files[0].name}]
env3 = json.loads(newf[0].read_text(encoding="utf-8")) if len(newf) == 1 else {}
path_clean = len(newf) == 1 and newf[0].parent == ready and bool(name_re.match(newf[0].name))
check("D3 raw-provenance/clean-path", path_clean and env3.get("actor_id") == hostile[:200],
      f"actor_len={len(env3.get('actor_id',''))} file={newf[0].name if newf else None}")

# ── D4: G-blind ─────────────────────────────────────────────────────────────
check("D4 G-blind propose", calls == [], f"engine calls recorded={calls}")

# ── D5: monitor COUNTS it (flip of blind-monitor) ───────────────────────────
spec_m = importlib.util.spec_from_file_location("ldm", WL / "live_drain_monitor.py")
ldm = importlib.util.module_from_spec(spec_m)
spec_m.loader.exec_module(ldm)
# run-1 scar: outbox_status nests counters under "buckets" — oracle path fixed.
st = ldm.outbox_status(tmp_outbox)
rc = st["buckets"]["ready"]["json_count"]
check("D5 monitor-counts", rc == 2, f"buckets.ready.json_count={rc} (want 2)")

# ── D6: no tmp litter ───────────────────────────────────────────────────────
dotfiles = [p.name for p in ready.iterdir() if p.name.startswith(".")]
check("D6 no-tmp-litter", dotfiles == [], f"dotfiles={dotfiles}")

# ── D7: guards survive ──────────────────────────────────────────────────────
before = len(list(ready.glob("*.json")))
g1 = eng.t_propose({"agent": "x", "kind": "graph", "payload": {}})
g2 = eng.t_propose({"agent": "x", "kind": "block", "payload": [1, 2]})
after = len(list(ready.glob("*.json")))
check("D7 guards-survive", "error" in g1 and "error" in g2 and before == after,
      f"g1={g1.get('error')!r} g2={g2.get('error')!r} files {before}->{after}")

# ── D8: no overwrite on identical args ──────────────────────────────────────
a = eng.t_propose({"agent": "n", "kind": "block", "payload": {"k": 1}})
b = eng.t_propose({"agent": "n", "kind": "block", "payload": {"k": 1}})
check("D8 distinct-ids", a["intent_id"] != b["intent_id"] and len(list(ready.glob("*.json"))) == after + 2,
      f"ids {a['intent_id'][:12]}../{b['intent_id'][:12]}..")

n_ok = sum(1 for _, ok, _ in results if ok)
print(f"\nVERDICT: {n_ok}/{len(results)} {'ALL GREEN' if n_ok == len(results) else 'REFUTED/PARTIAL'}")
sys.exit(0 if n_ok == len(results) else 1)
