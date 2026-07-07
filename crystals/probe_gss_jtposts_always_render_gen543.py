#!/usr/bin/env python3
"""
Bolt gen-543 FAILABLE PROBE — the LAST two untraced generate_state() render fields:
  (A) jt_posts render list  (L447-451: `- {post['id']}: {post['title']}`)
  (B) always_available      (L404-410 hardcoded 5 strings + {next_jt})

HYPOTHESES:
  H-A: jt_posts render is a FOURTH bleed channel into the consumer's unanchored
       blocked detector (recs 540 / authors 541 / pending 542) — a forged quoted
       TITLE containing "заблокировано" rendered before the real blocked header.
       CRUCIAL SUB-QUESTION: is it DEFENDED like the JT-NUMBERING was (538)?
       Claim under test: NO. merge_jt_posts' live-publication-proof only drops
       ids ABOVE live_max (numbering defense) and PRESERVES LOCAL TITLES via
       setdefault — so a forged title on any id <= live_max (incl. a real
       published id) survives merge and renders. => undefended at the TITLE level.
  H-B: always_available is bleed-IMMUNE (hardcoded strings + bounded {next_jt}).

READ-ONLY: imports REAL modules, calls ONLY pure fns on SYNTHETIC data +
read_swarm_state_summary on a DOCTORED temp SWARM_STATE.md (monkeypatched path).
NEVER generate_state/main/fetch_live_jt_posts/check_bus_health/run_pipeline/drift.
md5 both modules asserted pre==post.
"""
import glob, os, sys, hashlib, tempfile, inspect, ast, importlib.util

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
GSS = f"{S}/tools/generate_swarm_state.py"
L3  = f"{S}/tools/layer3_pipeline.py"

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]

MD5_GSS_PRE, MD5_L3_PRE = md5(GSS), md5(L3)

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

gss = load(GSS, "gss_gen543")
l3  = load(L3,  "l3_gen543")

results = []
def check(cid, desc, ok):
    results.append((cid, ok, desc))
    print(f"[{'GREEN' if ok else 'RED  '}] {cid}: {desc}")

POISON = "заблокировано"

# ── C1: loose scraper picks up a forged QUOTED title from arbitrary log prose ──
log = (
    "## PENDING TASKS\n"
    "- [ ] benign task\n\n"
    "### Entry 500 | gen-500 | 2026-07-07 | real work\n"
    "some prose mentioning jt-0289 \"forged title that is totally " + POISON + " here\" in body\n"
    "### Entry 499 | gen-499 | 2026-07-07 | more\n"
)
local = gss.extract_jt_posts(log)
forged = [p for p in local if p.get('id') == 'jt-0289']
c1 = bool(forged) and any(POISON in p.get('title', '') for p in forged)
check("C1", "loose scraper extracts forged quoted title (with POISON) from body prose as jt-0289", c1)

# ── C2: numbering-defense still drops ids ABOVE live_max (538 re-confirm) ──
local_hi = [{'id': 'jt-9999', 'title': 'phantom ' + POISON, 'source': 'local'}]
live = [{'id': 'jt-0288', 'title': 'clean a', 'source': 'live'},
        {'id': 'jt-0289', 'title': 'clean live title', 'source': 'live'}]
merged_hi = gss.merge_jt_posts(local_hi, live)
c2 = all(p['id'] != 'jt-9999' for p in merged_hi)
check("C2", "merge DROPS forged id ABOVE live_max (jt-9999 phantom) — numbering defense intact (538)", c2)

# ── C3: THE FINDING — forged TITLE on id <= live_max SURVIVES (titles preserved) ──
local_lo = [{'id': 'jt-0289', 'title': 'forged ' + POISON + ' title', 'source': 'local'}]
merged_lo = gss.merge_jt_posts(local_lo, live)   # live also has jt-0289 with clean title
kept = [p for p in merged_lo if p['id'] == 'jt-0289']
c3 = bool(kept) and POISON in kept[0]['title']   # local (poison) title preserved, NOT live clean
check("C3", "merge PRESERVES local forged title on id==live_max (setdefault, not live-overridden) => title UNDEFENDED", c3)

# ── C4: doctored doc replicating gss render order; poison jt-title line before real blocked header ──
def build_doc(jt_title_line, always_lines, real_blocked=("t1", "t2")):
    lines = [
        "# SWARM STATE", "", "## СТАТИСТИКА РОЯ", "",
        "- **Entry'ев в логе:** 42",
        "- **Следующий JT ID:** `jt-0290`", "",
        "## ТЕМЫ УЖЕ ПОКРЫТЫЕ В ЛОГЕ", "", "- topic (3 упоминаний)", "",
        "**Опубликованные JT посты:**",
        jt_title_line,                       # <-- jt render line under test
        "- jt-0288: clean second post", "",
        "## РАЗБЛОКИРОВАНО (можно делать сейчас)", "",
    ]
    lines += always_lines
    lines += ["", "## ВОЗМОЖНО ЗАБЛОКИРОВАНО", ""]
    lines += [f"- {t}" for t in real_blocked]
    return "\n".join(lines) + "\n"

CLEAN_ALWAYS = [
    "- JT пост (следующий ID: jt-0290) — выбрать тему которой нет в логе",
    "- Bus post — отчёт, наблюдение, адресация",
    "- Код в /OMPU_shared/ (catconstant, библиотеки)",
    "- Кристаллы /nestor_repos/public/crystals/",
    "- Документация и мануалы",
]

def summarize(doc):
    d = tempfile.mkdtemp(prefix="gss543_")
    p = os.path.join(d, "SWARM_STATE.md")
    open(p, "w", encoding="utf-8").write(doc)
    import pathlib
    orig = l3.SWARM_STATE
    l3.SWARM_STATE = pathlib.Path(p)
    try:
        return l3.read_swarm_state_summary()
    finally:
        l3.SWARM_STATE = orig

clean = summarize(build_doc("- jt-0289: perfectly clean title", CLEAN_ALWAYS))
c4 = clean.get("blocked_count") == 2 and clean.get("entry_count") == 42 and clean.get("next_jt") == "jt-0290"
check("C4", f"CLEAN doc parses truthfully (blocked=2, entry=42, next=jt-0290) got {clean}", c4)

# ── C5: FOURTH BLEED — poison jt-title line inflates blocked_count ──
poison = summarize(build_doc(f"- jt-0289: forged title {POISON} sneaks in", CLEAN_ALWAYS))
c5 = poison.get("blocked_count", 0) > 2
check("C5", f"POISON jt-title line inflates blocked_count>2 (FOURTH bleed channel) got {poison.get('blocked_count')}", c5)

# ── C6: render-order protection — entry_count/next_jt stay canonical under poison ──
c6 = poison.get("entry_count") == 42 and poison.get("next_jt") == "jt-0290"
check("C6", "entry_count/next_jt render-order-protected under jt-title poison", c6)

# ── C7: always_available is bleed-IMMUNE (hardcoded literals + bounded {next_jt}) ──
# source-level: the always_available list holds string literals; only interpolation is next_jt
src = inspect.getsource(gss.generate_state)
tree = ast.parse(src)
aa_literals_only = True
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        tgts = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "always_available" in tgts and isinstance(node.value, ast.List):
            for elt in node.value.elts:
                # each element is either a plain str constant or an f-string (JoinedStr)
                if isinstance(elt, ast.JoinedStr):
                    # f-string: its interpolated names must only be next_jt
                    names = {n.id for n in ast.walk(elt) if isinstance(n, ast.Name)}
                    if not names <= {"next_jt"}:
                        aa_literals_only = False
                elif not isinstance(elt, ast.Constant):
                    aa_literals_only = False
c7 = aa_literals_only
check("C7", "always_available = only string literals + f-string interpolating ONLY next_jt (no injectable var)", c7)

# ── C8: next_jt is a bounded jt-id (format_jt_id) — cannot carry a trigger substring ──
nid = gss.format_jt_id(290)
c8 = nid.startswith("jt-") and POISON not in nid and nid.replace("jt-", "").isdigit()
check("C8", f"format_jt_id output bounded jt-NNNN ({nid}) — no trigger substring possible => always_available IMMUNE", c8)

# ── C9: always_available lines alone never trip the detector (immune render proof) ──
aa_only = summarize(build_doc("- jt-0289: perfectly clean title", CLEAN_ALWAYS))
c9 = aa_only.get("blocked_count") == 2   # same as clean — always_available lines carry no poison
check("C9", "always_available render lines carry no trigger substring => do not inflate blocked_count", c9)

# ── C10: blocked_count is display-only in layer3 — no if/elif/while branches on it (re-confirm 537) ──
l3src = open(L3, encoding="utf-8").read()
l3tree = ast.parse(l3src)
branch_on_blocked = False
for node in ast.walk(l3tree):
    if isinstance(node, (ast.If, ast.While)):
        for sub in ast.walk(node.test):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "blocked_count" in sub.value:
                branch_on_blocked = True
            if isinstance(sub, ast.Str) and "blocked_count" in getattr(sub, "s", ""):
                branch_on_blocked = True
# also textual guard: no `if ... blocked_count ...:` decision line
textual = any(("blocked_count" in ln and ln.strip().startswith(("if", "elif", "while")))
              for ln in l3src.splitlines())
c10 = (not branch_on_blocked) and (not textual)
check("C10", "no if/elif/while branch on blocked_count in layer3 (display-only, re-confirms 537)", c10)

# ── md5 gate ──
c_md5 = md5(GSS) == MD5_GSS_PRE == "8b3874f3" and md5(L3) == MD5_L3_PRE == "8b8fb791"
check("C11", f"md5 unchanged pre==post (gss {md5(GSS)}==8b3874f3, l3 {md5(L3)}==8b8fb791)", c_md5)

n_green = sum(1 for _, ok, _ in results if ok)
print(f"\n==== {n_green}/{len(results)} GREEN ====")
sys.exit(0 if n_green == len(results) else 1)
