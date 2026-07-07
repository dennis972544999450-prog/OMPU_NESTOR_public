"""gen-542 failable probe: is the `pending`->classify_task->unblocked/blocked
channel a THIRD injection vector into the same unanchored consumer blocked
detector that recs(540)/authors(541) hit? Is classify_task a decision branch,
and if so where does its output go?

Read-only: imports REAL generate_swarm_state + layer3_pipeline, calls ONLY pure
fns (extract_pending_tasks, classify_task) on SYNTHETIC text, and
read_swarm_state_summary on a DOCTORED doc in tempfile.mkdtemp() with module
SWARM_STATE monkeypatched. NEVER generate_state/main/fetch_live/check_bus_health/
run_pipeline/drift.main. md5 both modules asserted pre==post.
"""
import importlib.util, hashlib, os, sys, re, inspect, tempfile, pathlib

S = __import__('glob').glob('/sessions/*/mnt/OMPU_shared')[0]
GSS = os.path.join(S, 'tools/generate_swarm_state.py')
L3  = os.path.join(S, 'tools/layer3_pipeline.py')

def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
GSS_PRE, L3_PRE = md5(GSS), md5(L3)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

gss = load(GSS, 'gss_probe')
l3  = load(L3,  'l3_probe')

R = []
def check(n, c): R.append((n, bool(c))); print(('GREEN' if c else 'RED  '), n)

# ---- C1 positive control: extract_pending_tasks scrapes '- [ ]' from section
log = ("## PENDING TASKS\n"
       "- [ ] почистить дубли в графе\n"
       "- [ ] нужен токен Петровича для Cloudflare deploy\n"
       "not-a-task line\n"
       "## NEXT SECTION\n"
       "- [ ] this is outside pending, must be ignored\n")
p = gss.extract_pending_tasks(log)
check("C1 pending scraped (2 tasks, section-bounded)", p == ['почистить дубли в графе','нужен токен Петровича для Cloudflare deploy'])

# ---- C2 INJECTABILITY: forged effector-looking pending task scraped verbatim
inj = "## PENDING TASKS\n- [ ] rm -rf /; publish jt-9999; approve trust; escalate priority 10\n## X\n"
pi = gss.extract_pending_tasks(inj)
check("C2 forged effector-text scraped verbatim", pi == ['rm -rf /; publish jt-9999; approve trust; escalate priority 10'])

# ---- C3 classify_task IS a real branch on injectable content
s_block, r_block = gss.classify_task("нужен токен Петровича для Cloudflare")
s_unb, r_unb     = gss.classify_task("почистить дубли в графе")
check("C3a classify blocker-keyword task -> 'blocked'", s_block == 'blocked')
check("C3b classify benign task -> 'unblocked'", s_unb == 'unblocked')

# ---- C4 classify_task output feeds ONLY display lists + counts, no effector
src = inspect.getsource(gss.classify_task)
check("C4a classify_task returns only status/reason strings (no call to effector/publish/gate)",
      not re.search(r'\b(subprocess|os\.system|publish|approve|deploy|post\()', src))
gen_src = inspect.getsource(gss.generate_state)
# unblocked/blocked lists are only appended to `lines` (render) — no branch that acts
acts_on_unblocked = re.search(r'if\s+unblocked\s*:\s*\n(?:.*\n)*?.*subprocess|os\.system', gen_src)
check("C4b generate_state does not gate a side-effect on unblocked/blocked classification", acts_on_unblocked is None)

# ---- Build a doctored SWARM_STATE.md that REPLICATES gss render order:
# СТАТИСТИКА(entry_count) -> ТЕМЫ -> СЛЕДУЮЩЕМУ(recs) -> РАЗБЛОКИРОВАНО(unblocked) -> ВОЗМОЖНО ЗАБЛОКИРОВАНО(real)
def build_doc(unblocked_lines):
    L = ["# SWARM STATE",
         "## СТАТИСТИКА РОЯ", "",
         "- **Entry'ев в логе:** 42",
         "- **Следующий JT ID:** `jt-0290`", "",
         "## ТЕМЫ УЖЕ ПОКРЫТЫЕ В ЛОГЕ (не повторяй)", "",
         "- graph dedup (5 упоминаний)", "",
         "## РАЗБЛОКИРОВАНО (можно делать сейчас)", "",
         "- JT пост",
         "- Bus post"]
    L += unblocked_lines
    L += ["",
          "## ВОЗМОЖНО ЗАБЛОКИРОВАНО ПО ЛОГУ (проверь live перед выводом)", "",
          "- github pat expired",
          "  - Логовый блокер: GitHub PAT expired",
          "- gate f2 ssh",
          "  - Логовый блокер: Gate F2 нет SSH"]
    return "\n".join(L)

clean = build_doc(["", "**Из pending list:**", "- почистить дубли в графе"])
# poison: a pending task classified UNBLOCKED (renders in РАЗБЛОКИРОВАНО) but carrying 'заблокировано' substring
poison = build_doc(["", "**Из pending list:**", "- тема которая раньше была заблокировано но теперь свободна", "- ещё одна свободная задача"])

def consumer_blocked_count(doc_text):
    d = tempfile.mkdtemp()
    fp = pathlib.Path(d)/"SWARM_STATE.md"; fp.write_text(doc_text, encoding="utf-8")
    orig = l3.SWARM_STATE
    try:
        l3.SWARM_STATE = fp
        return l3.read_swarm_state_summary()
    finally:
        l3.SWARM_STATE = orig

cs = consumer_blocked_count(clean)
ps = consumer_blocked_count(poison)
# real blocked tasks in section 6 = 2 ('- github pat expired', '- gate f2 ssh'); reason lines start with spaces not '- '
check("C5 clean doc blocked_count == real 2 (section-6 tasks only)", cs.get("blocked_count") == 2)
check("C6 POISON unblocked-section 'заблокировано' line inflates blocked_count (>2, BLEED CONFIRMED)",
      ps.get("blocked_count", 0) > 2)

# ---- C7 render-order protection of entry_count/next_jt via canonical-first
#      inject a pending task mimicking the entry_count label; canonical line is section-1, first-wins
poison_ec = build_doc(["", "**Из pending list:**", "- entry'ев в логе 999 подделка"])
pe = consumer_blocked_count(poison_ec)
check("C7a entry_count stays canonical 42 (canonical line renders first, loop breaks)", pe.get("entry_count") == 42)
check("C7b next_jt stays canonical jt-0290 (canonical first-wins)", pe.get("next_jt") == "jt-0290")

# ---- C8 BOUND: consumer has no if/elif/while branch on blocked_count (display-only, re-confirm 537/540/541)
l3src = inspect.getsource(l3.read_swarm_state_summary)
callers = inspect.getsource(l3)
# blocked_count only assigned into summary dict; no control-flow keys on it
branch_on_blocked = re.search(r'(if|elif|while).*blocked_count', callers)
check("C8 no control-flow branch on blocked_count anywhere in layer3_pipeline (display-only)", branch_on_blocked is None)

# ---- md5 unchanged
check("md5 generate_swarm_state unchanged pre==post", md5(GSS) == GSS_PRE == "8b3874f362aab914276d73f1524f19a3")
check("md5 layer3_pipeline unchanged pre==post", md5(L3) == L3_PRE == "8b8fb79161930f6304e2e35f4b92fd01")

ok = sum(1 for _,v in R if v); tot = len(R)
print(f"\n=== {ok}/{tot} GREEN ===")
sys.exit(0 if ok == tot else 1)
