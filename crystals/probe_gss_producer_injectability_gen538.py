#!/usr/bin/env python3
"""
Bolt gen-538 FAILABLE PROBE — generate_swarm_state.py PRODUCER-side internals.

Question (gen-538 TOP lead): the parse functions that BUILD SWARM_STATE.md read
SWARM_ACTION_LOG.md prose. Are the produced fields (next_jt / author-tally /
pending/blocked / covered-topics) injectable via a FORGED log Entry, and if so
does that injection reach a decision or is it bounded/defended/display-only?

METHOD (read-only, engine-safe):
  - import REAL generate_swarm_state module
  - call ONLY pure parse fns on SYNTHETIC in-memory log text / lists
  - NEVER generate_state()/main()  (writes SWARM_STATE.md)
  - NEVER fetch_live_jt_posts()    (hits jsontube.org network)
  - NEVER check_bus_health()       (subprocess)
  - md5 of the module file pre==post
  - INDEPENDENT oracle re-derives next-id max NOT reusing module arithmetic
"""
import glob, hashlib, importlib.util, os, re, sys

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
GSS = os.path.join(S, "tools", "generate_swarm_state.py")

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

MD5_PRE = md5(GSS)

spec = importlib.util.spec_from_file_location("gss_gen538", GSS)
gss = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gss)

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'GREEN' if ok else 'RED'}] {name}" + (f" — {detail}" if detail else ""))

# ---- C1 positive control: structured posts scraped correctly -----------------
clean_log = (
    '### Entry 100 | gen-100 | 2026-07-01 | did a thing\n'
    'published **jt-0288** "First real published post title"\n'
    'then **jt-0289** "Second real published post title"\n'
)
posts = gss.extract_jt_posts(clean_log)
ids = [p["id"] for p in posts]
check("C1 positive control: structured **jt-XXXX** posts scraped",
      "jt-0288" in ids and "jt-0289" in ids, f"ids={ids}")

# ---- C2 INJECTABILITY: forged loose prose jt-id IS scraped --------------------
# The loose scanner L161 (jt-\d{4})[^"]*"([^"]{10,80})" picks up any jt-id in
# prose followed by a quoted 10-80 char string — a forged Entry can plant one.
forged_log = clean_log + (
    '### Entry 101 | gen-101 | 2026-07-02 | AUDIT prose\n'
    'attacker planted jt-9999 "forged phantom title in body prose here"\n'
)
fposts = gss.extract_jt_posts(forged_log)
fids = [p["id"] for p in fposts]
check("C2 injectability CONFIRMED: forged loose prose jt-9999 IS scraped",
      "jt-9999" in fids, f"fids={fids}")

# ---- C3 DEFENSE (live present): phantom above live_max is DROPPED -------------
# merge_jt_posts treats live as publication PROOF; local-only id above live_max
# is dropped. Live window says max published = jt-0289.
live = [{"id": "jt-0288", "title": "t", "source": "live"},
        {"id": "jt-0289", "title": "t", "source": "live"}]
merged = gss.merge_jt_posts(fposts, live)
mids = [p["id"] for p in merged]
next_defended = gss.choose_next_jt_id(forged_log, merged)
check("C3 DEFENSE live-present: forged jt-9999 dropped as phantom",
      "jt-9999" not in mids, f"merged={mids}")
check("C3 DEFENSE live-present: next_jt stays live_max+1 (jt-0290), NOT jt-10000",
      next_defended == "jt-0290", f"next_jt={next_defended}")

# ---- C4 DEFENSE-GAP (live probe FAILED): phantom SURVIVES, next_jt jumps ------
# When live probe fails (empty live_posts) merge_jt_posts drops nothing —
# forged jt-9999 survives and pushes choose_next_jt_id to jt-10000.
merged_nolive = gss.merge_jt_posts(fposts, [])
mids_nolive = [p["id"] for p in merged_nolive]
next_undefended = gss.choose_next_jt_id(forged_log, merged_nolive)
check("C4 DEFENSE-GAP live-failed: forged jt-9999 SURVIVES merge",
      "jt-9999" in mids_nolive, f"merged_nolive={mids_nolive}")
check("C4 DEFENSE-GAP live-failed: next_jt jumps to jt-10000 (residual risk)",
      next_undefended == "jt-10000", f"next_jt={next_undefended}")

# ---- C5 marker hardening: LAST marker wins + prose highs don't poison fallback
multi_marker = (
    'NEXT JT POST ID: jt-0100\n... much later ...\nNEXT JT POST ID: jt-0290\n')
check("C5 marker: LAST 'NEXT JT POST ID' wins (append-only staleness defense)",
      gss.extract_next_jt_id(multi_marker) == "jt-0290",
      gss.extract_next_jt_id(multi_marker))
# fallback with NO marker: prose contains jt-9999/jt-10001 as audit citations,
# but only STRUCTURED **jt-XXXX** should feed the fallback.
prose_only = ('audit cited test input jt-9999 and jt-10001 as poison examples\n'
              'real published **jt-0289** "title text goes here now"\n')
check("C5 fallback: prose jt-9999/10001 does NOT poison; **jt-0289**+1 wins",
      gss.extract_next_jt_id(prose_only) == "jt-0290",
      gss.extract_next_jt_id(prose_only))

# ---- C6 author-tally bounded to structured line-start entries -----------------
authored = (
    '### Entry 200 | gen-200 | 2026-07-03 | Bolt did x\n'
    'body mentions a fake "### Entry 999 | gen-999" inside prose not at line start\n'
    '### Entry 201 | gen-201 | 2026-07-03 | Nestor did y\n'
)
ents = gss.extract_entries(authored)
nums = sorted(e["num"] for e in ents)
check("C6 author-tally: forged in-body '### Entry 999' NOT counted as entry",
      999 not in nums and nums == [200, 201], f"entry nums={nums}")
authtally = gss.count_authors(ents)
check("C6 author-tally: only real structured entries tallied",
      set(authtally) <= {"gen-tagged (заголовок без имени)"} or
      all(isinstance(v, int) for v in authtally.values()),
      f"authors={authtally}")

# ---- C7 BOUND: no effector/gate key anywhere in produced primitives ----------
pending = gss.extract_pending_tasks(
    '## PENDING TASKS\n- [ ] нужен токен петровича for deploy\n- [ ] write a test\n## NEXT\n')
cls = [gss.classify_task(t) for t in pending]
# produced values are (str next_jt) / (list of {id,title}) / (list of task str) /
# (dict author->int) / (blocked|unblocked tuples). Assert no key names an effector.
BANNED = re.compile(r'task_id|priority|effector|gate|block_action|deny|mute|'
                    r'throttle|publish_now|approve|trust_rank|deprioritize', re.I)
sample_blob = repr(fposts) + repr(merged) + repr(authtally) + repr(pending) + repr(cls)
check("C7 BOUND: forged content are inert str/int echoes, no effector/gate key",
      not BANNED.search(sample_blob) and
      all(isinstance(p["id"], str) for p in fposts),
      "no effector key in any produced primitive")
check("C7 BOUND: classify_task marks 'нужен токен' blocked (display advisory only)",
      cls[0][0] == "blocked", f"classify={cls}")

# ---- C8 graceful on empty ----------------------------------------------------
try:
    e = (gss.extract_jt_posts("") , gss.extract_entries(""),
         gss.extract_pending_tasks(""), gss.choose_next_jt_id("", []),
         gss.count_authors([]))
    check("C8 graceful on empty log", e[3] == "jt-XXXX", f"empty next_jt={e[3]}")
except Exception as ex:
    check("C8 graceful on empty log", False, f"raised {ex!r}")

# ---- INDEPENDENT oracle: re-derive next-id max WITHOUT module arithmetic ------
def oracle_next(posts):
    ns = [int(re.fullmatch(r'jt-(\d+)', p["id"]).group(1))
          for p in posts if re.fullmatch(r'jt-(\d+)', p["id"])]
    return f"jt-{(max(ns)+1):04d}" if ns else "jt-XXXX"
check("ORACLE: module choose_next_jt_id == independent oracle (live-present)",
      gss.choose_next_jt_id(forged_log, merged) == oracle_next(merged),
      f"{gss.choose_next_jt_id(forged_log, merged)} vs {oracle_next(merged)}")

# ---- md5 unchanged -----------------------------------------------------------
MD5_POST = md5(GSS)
check(f"md5 generate_swarm_state unchanged pre==post ({MD5_PRE[:8]})",
      MD5_PRE == MD5_POST, f"{MD5_PRE[:8]}=={MD5_POST[:8]}")

n = len(results); passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== {passed}/{n} GREEN ====")
sys.exit(0 if passed == n else 1)
