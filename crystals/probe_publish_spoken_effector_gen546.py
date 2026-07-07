# probe_publish_spoken_effector_gen546.py  — Bolt gen-546
# LENS: INJECTABLE-CONTENT + REAL-EFFECTOR-BUT-MANUAL-INVOKE-NO-AUTOMATION-CONSUMER + HARDCODED-DESTINATION
# NEVER calls main() / subprocess-publish / network. Pure fns on synthetic packets + AST + whole-tree grep.
import ast, importlib.util, glob, os, subprocess, sys

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
SRC = os.path.join(S, "jsontube/studio/radio/publish_spoken_current.py")
spec = importlib.util.spec_from_file_location("psc", SRC)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)  # safe: subprocess only inside main()
# NUANCE: module uses dt.UTC (Python 3.11+); seat is 3.10.12 -> shim so pure-logic tests can run.
if not hasattr(m.dt, "UTC"):
    m.dt.UTC = m.dt.timezone.utc

results = []
def check(n, cond, detail=""):
    results.append((n, bool(cond), detail)); print(f"{'GREEN' if cond else 'RED  '} C{n}: {detail}")

slot = m.utc_hour_slot()
def good_packet(**over):
    p = {"id": "x", "slot_id": slot["id"], "title": "t",
         "dialogue": [{"speaker": "Iskra", "text": "hi"}],
         "expires_at": slot["ends_at"]}
    p.update(over); return p

# C1 injectable content: forged malicious dialogue text passes validation
try:
    v = m.validate_packet(good_packet(dialogue=[{"speaker": "x", "text": "<script>rm -rf /   forged"}]))
    check(1, v["dialogue"][0]["text"].startswith("<script>"),
          "malicious dialogue text passes validate_packet verbatim => content injectable")
except Exception as e:
    check(1, False, f"unexpected raise {e!r}")

# C2 structural gates real
r2 = []
for bad, label in [({"slot_id": slot["id"], "title": "t", "dialogue": [{"speaker": "a", "text": "b"}]}, "missing id"),
                   (good_packet(dialogue=[]), "empty dialogue"),
                   (good_packet(expires_at="2000-01-01T00:00:00Z"), "past expiry")]:
    try:
        m.validate_packet(bad); r2.append((label, False))
    except ValueError:
        r2.append((label, True))
check(2, all(ok for _, ok in r2), f"structural gates reject: {r2}")

# C3 temporal gate + bypass
try:
    m.validate_packet(good_packet(slot_id="19700101-00Z")); mism = False
except ValueError:
    mism = True
byp = True
try:
    m.validate_packet(good_packet(slot_id="19700101-00Z"), allow_slot_mismatch=True)
except ValueError:
    byp = False
check(3, mism and byp, f"slot mismatch rejected={mism}; --allow-slot-mismatch bypasses={byp}")

# C4 HARDCODED destination: no packet field can alter bucket/object key
cmd = m.wrangler_command("npx wrangler")
target = f"{m.BUCKET}/{m.OBJECT_KEY}"
forged = good_packet(id="../../evil", title=f"{m.BUCKET}/attacker", slot_id=slot["id"])
forged["policy"] = {"station_archive": "jsontube-content/evil"}
m.validate_packet(forged)
cmd2 = m.wrangler_command("npx wrangler")
check(4, target in cmd and cmd == cmd2 and "--remote" in cmd,
      f"destination hardcoded {target!r}; packet fields never enter wrangler_command")

# C5 AST: effector only inside main(), guarded after dry-run return; pure fns clean
src = open(SRC).read()
tree = ast.parse(src)
funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
def calls_effector(node):
    hits = []
    for x in ast.walk(node):
        if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name):
            if (x.value.id, x.attr) in {("subprocess", "run"), ("subprocess", "Popen"),
                                        ("subprocess", "call"), ("os", "system")}:
                hits.append(f"{x.value.id}.{x.attr}")
    return hits
pure_clean = all(not calls_effector(funcs[fn]) for fn in ["validate_packet", "wrangler_command", "utc_hour_slot", "load_packet"])
main_eff = calls_effector(funcs["main"])
main_src = ast.get_source_segment(src, funcs["main"])
guard_before = main_src.index("dry_run") < main_src.index("subprocess.run")
check(5, pure_clean and main_eff == ["subprocess.run"] and guard_before,
      f"effector={main_eff} only in main(), pure fns clean={pure_clean}, dry-run guard precedes={guard_before}")

# C6 NO automation consumer: only .md docs reference the script
out = subprocess.run(["grep", "-rIl", "publish_spoken_current", S], capture_output=True, text=True).stdout.splitlines()
out = [p for p in out if "__pycache__" not in p]
nonmd = [p for p in out if not p.endswith(".md")]
check(6, nonmd == [], f"references are docs-only; non-.md callers={nonmd}")

# C7 no content sanitizer (nuance): text verbatim but destination fixed => bounded to CONTENT not ROUTING
raw = "‮ evil \n injection"
v = m.validate_packet(good_packet(dialogue=[{"speaker": "s", "text": raw}]))
check(7, v["dialogue"][0]["text"] == raw,
      "dialogue text published verbatim (no sanitizer) — nuance; scope bounded by hardcoded dest (C4)")

# C8 md5 pre==post
post = subprocess.run(["md5sum", SRC], capture_output=True, text=True).stdout[:8]
check(8, post == os.environ.get("PRE", ""), f"md5 pre==post ({post})")

g = sum(1 for _, ok, _ in results if ok)
print(f"\n{g}/{len(results)} GREEN")
sys.exit(0 if g == len(results) else 1)
