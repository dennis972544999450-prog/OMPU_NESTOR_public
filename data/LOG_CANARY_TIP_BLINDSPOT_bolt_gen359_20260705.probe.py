import re
STRICT = re.compile(r'^#{1,4}\s+Entry\s+#?(\d+)\b')
NEAR   = re.compile(r'^#{1,4}\s+Entry\b', re.I)   # "meant to be an Entry heading"
def scan(path):
    strict_n=0; drift=[]
    for i,line in enumerate(open(path,encoding='utf-8'),1):
        s=STRICT.match(line)
        if s: strict_n+=1
        elif NEAR.match(line): drift.append((i,line.strip()[:70]))
    return strict_n, drift
for name,p in [("REAL","SWARM_ACTION_LOG.md"),("MUT-A(correct)","/tmp/log_A.md"),("MUT-C(drift)","/tmp/log_C.md")]:
    sn,dr=scan(p)
    print(f"{name}: strict_headings={sn}  FORMAT_DRIFT={len(dr)}")
    for ln,txt in dr: print(f"    line {ln}: {txt!r}")
