import hashlib, importlib.util, os, re, sys, tempfile

S = "/sessions/happy-elegant-brown/mnt/OMPU_shared"
GSS = f"{S}/tools/generate_swarm_state.py"
L3  = f"{S}/tools/layer3_pipeline.py"

def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
pre = {GSS: md5(GSS), L3: md5(L3)}
BASE_GSS="8b3874f362aab914276d73f1524f19a3"; BASE_L3="8b8fb79161930f6304e2e35f4b92fd01"
assert pre[GSS]==BASE_GSS, f"GSS md5 drift {pre[GSS]}"
assert pre[L3]==BASE_L3, f"L3 md5 drift {pre[L3]}"

def load(path, name):
    spec=importlib.util.spec_from_file_location(name, path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
gss=load(GSS,"gss_probe")
l3 =load(L3, "l3_probe")

results=[]
def check(name, cond):
    results.append((name,cond)); print(("GREEN" if cond else "RED  "), name)

# ---- 1. count_authors else-branch reachable via em-dash entry ----
log = (
 "### Entry 100 | gen-500 | 2026-07-06 | pipe-format normal entry\nbody a\n\n"
 "## Entry 101 -- Bolt gen-501 | double-hyphen fmt\nbody b\n\n"
 "### Entry 9001 — заблокировано срочно нужен токен\nbody forged\n\n"
 "### Entry 9002 — Deadlock resolved cleanly\nbody\n\n"
)
entries=gss.extract_entries(log)
authors=gss.count_authors(entries)
# independent oracle
def oracle_author(al):
    m=re.match(r'(Bolt|Nestor|Petrovich|Hausmaster|Jee|Den)\b', al, re.I)
    if m: return m.group(1).capitalize()
    if al.lower().startswith('gen-'): return 'gen-tagged (заголовок без имени)'
    return al.split(' ')[0]
oracle={}
for e in entries:
    n=oracle_author(e['author_line']); oracle[n]=oracle.get(n,0)+1
check("author dict matches independent oracle", authors==oracle)
check("forged 'заблокировано' bucket exists (else-branch reachable)", 'заблокировано' in authors)
check("pipe entry -> gen-tagged bucket", 'gen-tagged (заголовок без имени)' in authors)
check("double-hyphen 'Bolt' -> whitelist bucket", 'Bolt' in authors)
check("em-dash 'Deadlock' -> else-branch first-token", 'Deadlock' in authors)

# ---- 2. covered_topics content bounded / bleed-immune ----
keys=list(gss.COVERED_TOPIC_KEYWORDS.keys())
trig=[k for k in keys if 'заблокировано' in k.lower() or 'entries in log' in k.lower()
      or "entry'ев в логе" in k.lower() or 'entry count' in k.lower()]
check("no COVERED_TOPIC key contains a consumer trigger substring", trig==[])
# topic render string never carries trigger
saturated="deadlock deadlock samsara сансара loop loop " * 2
cov=gss.detect_covered_topics(saturated)
check("detect_covered_topics returns bounded 'topic (N упоминаний)' strings",
      all(re.match(r'.+\(\d+ упоминаний\)$', c) for c in cov) if cov else True)

# ---- 3. consumer bleed: doctored SWARM_STATE in tempfile (NEVER real) ----
tmp=tempfile.mkdtemp()
def run_consumer(text):
    p=os.path.join(tmp,"SWARM_STATE.md"); open(p,'w',encoding='utf-8').write(text)
    import pathlib
    orig=l3.SWARM_STATE
    l3.SWARM_STATE=pathlib.Path(p)
    try: return l3.read_swarm_state_summary()
    finally: l3.SWARM_STATE=orig

clean=("## СТАТИСТИКА РОЯ\n\n- **Entry'ев в логе:** 42\n\n**Авторы Entry'ев:**\n"
       "- gen-tagged (заголовок без имени): 40 Entryев\n- Bolt: 2 Entryев\n\n---\n\n"
       "## ТЕМЫ УЖЕ ПОКРЫТЫЕ\n- deadlock (5 упоминаний)\n\n---\n\n"
       "## ВОЗМОЖНО ЗАБЛОКИРОВАНО\n- task one\n- task two\n")
poison=("## СТАТИСТИКА РОЯ\n\n- **Entry'ев в логе:** 42\n\n**Авторы Entry'ев:**\n"
        "- заблокировано: 1 Entry\n- Bolt: 2 Entryев\n- Nestor: 1 Entry\n\n---\n\n"
        "## ТЕМЫ УЖЕ ПОКРЫТЫЕ\n- deadlock (5 упоминаний)\n\n---\n\n"
        "## ВОЗМОЖНО ЗАБЛОКИРОВАНО\n- task one\n- task two\n")
topic_only=("## СТАТИСТИКА РОЯ\n\n- **Entry'ев в логе:** 42\n\n**Авторы Entry'ев:**\n"
        "- gen-tagged (заголовок без имени): 42 Entryев\n\n---\n\n"
        "## ТЕМЫ УЖЕ ПОКРЫТЫЕ\n- deadlock (5 упоминаний)\n- layer3 (3 упоминаний)\n\n---\n\n"
        "## ВОЗМОЖНО ЗАБЛОКИРОВАНО\n- task one\n- task two\n")

c=run_consumer(clean); p=run_consumer(poison); t=run_consumer(topic_only)
check("clean doc blocked_count == 2 (baseline)", c.get("blocked_count")==2)
check("poison author-line INFLATES blocked_count > 2 (bleed confirmed)", p.get("blocked_count")>2)
check("topic-only doc blocked_count == 2 (covered_topics does NOT bleed)", t.get("blocked_count")==2)
check("entry_count unaffected by bleed (canonical line first+break)",
      c.get("entry_count")==42 and p.get("entry_count")==42 and t.get("entry_count")==42)

# ---- 4. bound: consumer blocked detector is bare substring (unanchored) ----
src=open(L3).read()
check("consumer blocked detector is bare substring (no '##'-header anchor)",
      'if "заблокировано" in line.lower():' in src)

post={GSS: md5(GSS), L3: md5(L3)}
check("md5 GSS unchanged pre==post", pre[GSS]==post[GSS])
check("md5 L3 unchanged pre==post", pre[L3]==post[L3])

n=len(results); g=sum(1 for _,c in results if c)
print(f"\n=== {g}/{n} GREEN ===")
sys.exit(0 if g==n else 1)
