import json, os, tempfile, io

# Reproduce the EXACT __main__ producer pattern from swarm_self_model.py L742-744:
#   with open(SELF_MODEL_OUT, "w") as f: json.dump(model, f, indent=2, ensure_ascii=False)
# vs the atomic pattern Petrovich landed for bus_analyzer (mkstemp+os.replace).

MODEL = {"schema": "ompu.self-model.v1",
         "cognitive_topology": {"c%02d" % i: {"gen_born": i, "note": "x"*40} for i in range(60)}}

class Boom(Exception): pass
class InterruptingWriter(io.StringIO):
    """Raises after N write() calls to simulate crash/kill mid-dump."""
    def __init__(self, target, trip): super().__init__(); self.t=target; self.n=0; self.trip=trip
    def write(self, s):
        self.n += 1
        if self.n >= self.trip: 
            self.t.write(self.getvalue()); raise Boom("interrupted mid-dump")
        return super().write(s)

def naive_save_interrupted(path, trip):
    # in-place truncate-then-write, interrupted mid json.dump
    f = open(path, "w")
    try:
        buf = InterruptingWriter(f, trip)
        json.dump(MODEL, buf, indent=2, ensure_ascii=False)  # never completes
    finally:
        f.flush(); f.close()

def atomic_save_interrupted(path, trip):
    # mkstemp + os.replace: interrupt leaves ORIGINAL intact, temp orphaned
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            buf = InterruptingWriter(f, trip)
            json.dump(MODEL, buf, indent=2, ensure_ascii=False)
        os.replace(tmp, path)  # only reached if dump completes
    except Boom:
        try: os.unlink(tmp)
        except OSError: pass
        raise

def consumer_guarded_load(path):
    # EXACT swarm_driver.load_self_model behavior
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

print("=== G1: NON-ATOMIC producer interrupted mid-dump ===")
p1 = "/tmp/sm_naive.json"
json.dump({"schema":"ompu.self-model.v1","cognitive_topology":{"OLD":{"gen_born":1}}}, open(p1,"w"), indent=2)
print("  pre-write valid?  ", bool(json.load(open(p1)).get("cognitive_topology")))
try: naive_save_interrupted(p1, trip=8)
except Boom: print("  producer crashed mid-dump (Boom) as designed")
raw = open(p1).read()
print("  file bytes on disk:", len(raw), "| tail:", repr(raw[-30:]))
try:
    json.load(open(p1)); print("  naive json.load: OK (no repro)")
except Exception as e: print("  naive json.load RAISES:", type(e).__name__)
got = consumer_guarded_load(p1)
print("  GUARDED consumer returns:", got if got else "{}  <-- self-model feedback gate SILENTLY EMPTY")

print("\n=== G2: ATOMIC producer interrupted mid-dump (proposed fix) ===")
p2 = "/tmp/sm_atomic.json"
json.dump({"schema":"ompu.self-model.v1","cognitive_topology":{"OLD":{"gen_born":1}}}, open(p2,"w"), indent=2)
try: atomic_save_interrupted(p2, trip=8)
except Boom: print("  producer crashed mid-dump (Boom) as designed")
got = consumer_guarded_load(p2)
orphans = [x for x in os.listdir("/tmp") if x.startswith("tmp") and x.endswith(".tmp")]
print("  consumer sees OLD model preserved?:", got.get("cognitive_topology"))
print("  temp orphans cleaned?:", "yes" if not orphans else orphans)
