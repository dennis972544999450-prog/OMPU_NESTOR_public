#!/usr/bin/env python3
"""
Bolt gen-539 FAILABLE PROBE — TODO_phi.md as the SECOND declared input of
generate_swarm_state.py: is its content injectable into any produced
SWARM_STATE.md field, or is it a DEAD READ (opened + read, content discarded)?

Hypothesis (to be falsified): generate_state() reads TODO_phi.md into `todo_text`
(L364-367) but NEVER consumes `todo_text` — pending tasks come from
extract_pending_tasks(log_text), i.e. from SWARM_ACTION_LOG.md, not the TODO.
=> editing/injecting TODO_phi.md cannot alter SWARM_STATE.md.

METHOD (read-only, NO side effects):
  * import the REAL generate_swarm_state module (real code under test)
  * NEVER call generate_state()/main() (writes SWARM_STATE.md),
    fetch_live_jt_posts() (jsontube network), or check_bus_health() (subprocess)
  * AST-analyse the SOURCE of generate_state: classify every `todo_text` Name
    node by ctx (Store vs Load). Dead read == >=1 Store, 0 Load.
  * POSITIVE CONTROL: the same AST detector must show Load>0 for variables that
    ARE used (log_text, pending) — proves the detector distinguishes used/unused.
  * DISTINCT-FROM-536: assert TODO_PATH is actually opened (read-then-discard),
    unlike NORM_REGISTER which was defined-but-never-opened.
  * INDEPENDENT regex oracle re-derives the todo_text non-assignment ref count
    without reusing the AST result.
  * Call REAL pure fn extract_pending_tasks on synthetic text to prove its sole
    input is the LOG's '## PENDING TASKS' section (todo content is irrelevant).
  * md5 of the module unchanged pre==post (no writes).
"""
import ast, glob, hashlib, importlib.util, inspect, os, re, sys

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
MOD = os.path.join(S, "tools", "generate_swarm_state.py")

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

MD5_PRE = md5(MOD)

spec = importlib.util.spec_from_file_location("gss_uut", MOD)
gss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gss)

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

# ---- AST detector over generate_state source ----
src = inspect.getsource(gss.generate_state)
tree = ast.parse(src)

def name_ctx_counts(varname):
    store = load = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == varname:
            if isinstance(node.ctx, ast.Store):
                store += 1
            elif isinstance(node.ctx, ast.Load):
                load += 1
    return store, load

todo_store, todo_load = name_ctx_counts("todo_text")
log_store, log_load = name_ctx_counts("log_text")
pend_store, pend_load = name_ctx_counts("pending")

# C1 — DEAD READ: todo_text is assigned but never loaded/consumed
check("C1 todo_text assigned>=1", todo_store >= 1, f"store={todo_store}")
check("C1 todo_text load==0 (DEAD READ)", todo_load == 0, f"load={todo_load}")

# C2 — POSITIVE CONTROL: detector proves it CAN see a real read
check("C2 posctrl log_text load>0", log_load > 0, f"log_load={log_load}")
check("C2 posctrl pending load>0", pend_load > 0, f"pending_load={pend_load}")

# C3 — DISTINCT FROM 536: TODO file is actually OPENED (read-then-discard),
#      not merely defined-but-never-opened
opens_todo = ("open(TODO_PATH" in src) and ("todo_text = f.read()" in src)
check("C3 TODO_PATH is opened+read (not never-opened)", opens_todo, "read-then-discard")

# C4 — no output line interpolates todo_text; content cannot reach SWARM_STATE
full_src = open(MOD, encoding="utf-8").read()
check("C4 no {todo interpolation in module", "{todo" not in full_src, "no fstring use")

# C5 — INDEPENDENT regex oracle: non-assignment references of todo_text == 0
#      (strip the two assignment lines, count remaining word-boundary hits)
oracle_hits = 0
for ln in src.split("\n"):
    if re.search(r"\btodo_text\b", ln):
        # assignment line if it matches `todo_text =` at start (after strip)
        if re.match(r"\s*todo_text\s*=", ln):
            continue
        oracle_hits += 1
check("C5 independent oracle: 0 non-assign refs", oracle_hits == 0, f"hits={oracle_hits}")

# C6 — extract_pending_tasks sole input is LOG's '## PENDING TASKS' section;
#      TODO content is structurally irrelevant. Prove with synthetic text.
syn_log = (
    "### Entry 1 | gen-1 | x\n"
    "## PENDING TASKS\n"
    "- [ ] real task from LOG\n"
    "- [ ] second log task\n"
    "## NEXT\n"
    "- [ ] must NOT be captured (outside section)\n"
)
pend = gss.extract_pending_tasks(syn_log)
check("C6 pending from LOG section only", pend == ["real task from LOG", "second log task"], str(pend))

# C6b — a forged pending task placed in TODO-style text is NOT reachable:
#       extract_pending_tasks takes ONE arg (log_text); todo is never passed.
sig = inspect.signature(gss.extract_pending_tasks)
check("C6b extract_pending_tasks takes only log_text",
      list(sig.parameters) == ["log_text"], str(list(sig.parameters)))

# C7 — no effector/gate key would be reachable from todo even if it were read:
#      the produced pending flows only into display lines (see render L490-500).
#      Assert none of the produced primitives derived from pending carries a gate.
#      (Structural: pending -> classify_task -> unblocked/blocked -> display lines.)
cls_src = inspect.getsource(gss.classify_task)
gate_words = ["subprocess", "os.system", "publish(", "deploy", "trust_rank",
              "priority=", "effector"]
check("C7 classify_task has no effector/gate call",
      not any(w in cls_src for w in gate_words), "display-advisory only")

MD5_POST = md5(MOD)
check("md5 module unchanged pre==post", MD5_PRE == MD5_POST, f"{MD5_PRE[:8]}=={MD5_POST[:8]}")

print("=" * 62)
print("PROBE gen-539 — TODO_phi.md second-input DEAD-READ")
print(f"module md5: {MD5_PRE[:8]} (pre) == {MD5_POST[:8]} (post)")
print(f"todo_text: store={todo_store} load={todo_load}  |  "
      f"log_text load={log_load}  pending load={pend_load}")
print("=" * 62)
npass = sum(1 for _, c, _ in results if c)
for name, c, detail in results:
    print(f"[{'GREEN' if c else 'RED  '}] {name}  {detail}")
print("=" * 62)
print(f"{npass}/{len(results)} GREEN")
sys.exit(0 if npass == len(results) else 1)
