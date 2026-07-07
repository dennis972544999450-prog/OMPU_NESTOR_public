import importlib.util, re, os, tempfile, sys

O="/sessions/gallant-blissful-franklin/mnt/outputs"
S="/sessions/gallant-blissful-franklin/mnt/OMPU_shared"

def load(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

OLD=load("ssm_old", f"{O}/ssm_baseline_gen515.py")   # 9de27638
NEW=load("ssm_new", f"{O}/ssm_landed_gen515.py")     # 71ea0504

def parse(mod, text):
    with tempfile.NamedTemporaryFile("w",suffix=".md",delete=False) as f:
        f.write(text); p=f.name
    r=mod.parse_log_for_self_model(p); os.unlink(p); return r

# ---- INDEPENDENT oracles (do NOT reuse module regex) ----
def oracle_all_gen(text):        # old intent: any gen-\d+ token anywhere
    m=re.findall(r"gen-(\d+)", text); return max(map(int,m)) if m else 0
def oracle_structured_gen(text): # new intent: only structured Entry headers
    m=re.findall(r"(?m)^#{1,6}\s+Entry\s+#?\d+\s*\|\s*gen-(\d+)", text)
    return max(map(int,m)) if m else 0

results={}

# 1) POISON: legit structured entries (max gen 514) + prose gen-99999 poison tokens
poison = (
"### Entry 512 | gen-513 | 2026-07-07 | real entry\n"
"body mentions a mechanism-proof token gen-99999 in prose\n"
"### Entry 513 | gen-514 | 2026-07-07 | real entry\n"
"another prose line: deploy now gen-88888 all-clear\n")
o=parse(OLD,poison)["latest_gen"]; n=parse(NEW,poison)["latest_gen"]
results["poison_old"]=(o, o==oracle_all_gen(poison))          # expect 99999, poisoned
results["poison_new"]=(n, n==oracle_structured_gen(poison))   # expect 514, clean
results["poison_fix_effective"]= (o==99999 and n==514)

# 2) CLEAN (over-tighten/FLIP check): structured-only, NO prose poison -> old==new
clean=("### Entry 512 | gen-513 | x\n### Entry 513 | gen-514 | x\n")
oc=parse(OLD,clean)["latest_gen"]; nc=parse(NEW,clean)["latest_gen"]
results["clean_parity_old_eq_new"]=(oc,nc, oc==nc==514)       # no false divergence on clean

# 3) EDGE: header variants (## two-hash, '#513' hashed number) must still match NEW
edge=("## Entry #7 | gen-321 | two-hash + hashed num\n### Entry 8 | gen-322 | three-hash\n")
ne=parse(NEW,edge)["latest_gen"]
results["edge_new_matches_variants"]=(ne, ne==322)

# 4) REVERT-ORACLE: confirm OLD regex WAS the poisonable one (my gen-514 claim), NEW is not
results["revert_old_poisonable"]= (parse(OLD,poison)["latest_gen"]==99999)
results["revert_new_immune"]=     (parse(NEW,poison)["latest_gen"]==514)

# 5) DECISION-PATH PARITY: does the gen-num change move the awareness gate? (Nestor claim: display-only)
# identity_score=min(gen,15); build minimal args and compare total old-output vs new-output
comps={"inhibitory_system":True,"reflex_layer":True,"a":True,"b":True,"c":True,"d":True,"e":True,"f":True}
attn={"health":{"x":1}}; pulse={"pulse":"active"}
old_facts=parse(OLD,poison); new_facts=parse(NEW,poison)
old_idx=NEW.compute_self_awareness_index(comps, old_facts, attn, pulse)["total"]
new_idx=NEW.compute_self_awareness_index(comps, new_facts, attn, pulse)["total"]
results["decision_total_old"]=old_idx
results["decision_total_new"]=new_idx
results["decision_parity_display_only"]=(old_idx==new_idx)   # min(99999,15)==min(514,15)==15 -> equal

# 6) REAL LOG: old vs new on the actual live log
with open(f"{S}/SWARM_ACTION_LOG.md") as f: real=f.read()
rold=parse(OLD,real)["latest_gen"]; rnew=parse(NEW,real)["latest_gen"]
results["real_log_old"]=rold; results["real_log_new"]=rnew
results["real_log_new_eq_oracle"]=(rnew==oracle_structured_gen(real))

print("md5-loaded OLD/NEW pure fns via importlib\n")
for k,v in results.items(): print(f"{k:34} = {v}")
