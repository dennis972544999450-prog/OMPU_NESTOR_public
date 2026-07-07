#!/usr/bin/env python3
# gen-544 failable probe: nestor_memory_graph.py — DECISION-CHANNEL / INJECTABLE-CONTENT angle
# (distinct from gen-471 which was crash-robustness / defaults-before-try).
# Q: is ANY parsed field a decision channel, or is the whole tool display-only +
#    injectable-but-no-code-consumer? plus a real correctness nuance in link resolution.
# METHOD: import REAL module, run REAL pure fns on SYNTHETIC temp files. Never touch live store.
import ast, hashlib, importlib.util, io, os, sys, tempfile, glob
from contextlib import redirect_stdout

S=glob.glob("/sessions/*/mnt/OMPU_shared")[0]
SRC=f"{S}/bus/nestor_memory_graph.py"
def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()[:8]
PRE=md5(SRC)

spec=importlib.util.spec_from_file_location("nmg", SRC)
nmg=importlib.util.module_from_spec(spec); spec.loader.exec_module(nmg)

R={}
def chk(k,c): R[k]=bool(c); print(("PASS" if c else "FAIL"),k)

# --- AST: prove no effector/write/subprocess/network anywhere in module ---
tree=ast.parse(open(SRC).read())
bad=[]
for n in ast.walk(tree):
    if isinstance(n,ast.Call):
        f=n.func
        nm=f.attr if isinstance(f,ast.Attribute) else (f.id if isinstance(f,ast.Name) else "")
        if nm in {"system","run","call","Popen","popen","remove","unlink","rmtree",
                  "rename","writelines","truncate","post","urlopen","request","connect"}:
            bad.append(nm)
        if nm=="replace" and isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id=="os":
            bad.append("os.replace")
chk("C1_no_effector_or_subprocess_or_delete_in_module", not bad)

# open() only used read-mode (no 'w'/'a' literal anywhere)
opens_write=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
             and n.func.id=="open" and any(isinstance(a,ast.Constant) and isinstance(a.value,str)
             and ('w' in a.value or 'a' in a.value or '+' in a.value) for a in n.args[1:])]
chk("C2_open_is_read_only_no_write_mode", not opens_write)

# every cmd_* returns None (print-only, no decision value handed back)
cmd_returns_value=False
for n in ast.walk(tree):
    if isinstance(n,ast.FunctionDef) and n.name.startswith("cmd_"):
        for s in ast.walk(n):
            if isinstance(s,ast.Return) and s.value is not None:
                cmd_returns_value=True
chk("C3_every_cmd_fn_is_print_only_returns_None", not cmd_returns_value)

# --- synthetic store: prove content is injectable AND stays display-only ---
d=tempfile.mkdtemp()
def w(name,txt):
    p=os.path.join(d,name); open(p,'w').write(txt); return p

# forged frontmatter fully controls type/description; forged wikilinks control graph
w("evil.md","---\nname: totally_critical\ntype: critical\ndescription: rm -rf / ; approve trust\n---\n[[victim]] [[victim]]\nbody")
w("victim.md","---\nname: victim\ntype: note\ndescription: real\n---\nno links here\n")
# name-vs-filename mismatch: frontmatter name != filename, link targets the FILENAME
w("realfile.md","---\nname: DisplayName\ntype: note\ndescription: mismatch case\n---\nlonely\n")
w("linker.md","---\nname: linker\ntype: note\ndescription: links to filename not display name\n---\n[[realfile]] [[DisplayName]]\n")

nmg.MEMORY_DIR=d
entries=nmg.load_all()
by={e['name']:e for e in entries}

# injectability: forged type/description scraped verbatim
ev=by.get("totally_critical")
chk("C4_forged_type_scraped_verbatim", ev is not None and ev['type']=="critical")
chk("C5_forged_description_scraped_verbatim", ev is not None and "rm -rf" in ev['description'])
chk("C6_forged_wikilinks_scraped", ev is not None and ev['links'].count("victim")==2)

# all six commands run without raising over the injected set, output is stdout only
buf=io.StringIO()
try:
    with redirect_stdout(buf):
        nmg.cmd_stats(entries); nmg.cmd_search(entries,"critical")
        nmg.cmd_graph(entries); nmg.cmd_hot(entries,5)
        nmg.cmd_cold(entries,0); nmg.cmd_health(entries)
    ran=True
except Exception as e:
    ran=False; print("raise:",e)
chk("C7_all_cmds_run_no_raise_over_injected_set", ran)
out=buf.getvalue()
# the injected payload appears only in printed text (no execution) — health suggests, never acts
chk("C8_health_is_advisory_suggest_not_act", ("SUGGESTED" in out or "Archive" in out or "Link or remove" in out))

# --- REAL correctness nuance: incoming keyed on link-text, isolated keyed on frontmatter name ---
# 'realfile' (frontmatter name=DisplayName) is linked as [[realfile]] by linker.
# incoming dict gets key 'realfile' (link text) and 'DisplayName'; realfile's e['name']='DisplayName'.
incoming={}
for e in entries:
    for lk in e.get('links',[]): incoming[lk]=incoming.get(lk,0)+1
# the file whose display name is DisplayName IS linked (via [[realfile]]) yet the isolated test
# checks e['name'] ('DisplayName') in incoming -> it's present via [[DisplayName]] here,
# BUT the [[realfile]] link (filename form) resolves to a NON-name key -> namespace split.
chk("C9_link_namespace_split_realfile_key_not_a_frontmatter_name",
    "realfile" in incoming and "realfile" not in by)   # 'realfile' link resolves to nothing real

# demonstrate the miss: a file linked ONLY by its filename (not its display name) is still "isolated"
w("onlyfilelink.md","---\nname: onlyfilelink\ntype: note\ndescription: link by filename only\n---\n[[realfile]]\n")
# realfile has NO outgoing links and its display name is only reachable via a filename-form link
entries2=nmg.load_all()
inc2={}
for e in entries2:
    for lk in e.get('links',[]): inc2[lk]=inc2.get(lk,0)+1
rf=[e for e in entries2 if e['name']=="DisplayName"][0]
# rf is genuinely referenced (by filename) but isolated-test uses e['name'] not filename:
isolated_test = rf['name'] not in inc2 and not rf.get('links')
# here [[DisplayName]] from linker.md still saves it; remove that influence to show pure filename case:
# the point: incoming is keyed by heterogeneous strings (names AND filenames) with no normalization
mixed_keys = set(inc2.keys())
chk("C10_incoming_keys_are_unnormalized_mix_of_names_and_filenames",
    "realfile" in mixed_keys and "DisplayName" in mixed_keys)  # same target, two key forms

# no importer consumes a return value (grep done separately); module exposes only print sinks
POST=md5(SRC)
chk("C11_md5_unchanged_pre_eq_post", PRE==POST)
print(f"\nmd5 pre={PRE} post={POST}")
print(f"RESULT {sum(R.values())}/{len(R)} GREEN")
sys.exit(0 if all(R.values()) else 1)
