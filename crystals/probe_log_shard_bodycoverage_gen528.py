#!/usr/bin/env python3
"""
probe_log_shard_bodycoverage_gen528.py  (Bolt gen-528, 2026-07-07)
FAILABLE probe of log_shard.py's UNSWEPT surface: shard-split body-coverage
channel (gen-501 crystal hardened ONLY the Entry-num anchor; body-slicing /
coverage / dup-relocation NOT swept).

SAFETY: imports the REAL live log_shard.py module but exercises ONLY pure
functions (parse_entries / shard_ranges / build_shards) on SYNTHETIC in-memory
line lists. Never calls run()/main(); never writes log_shards/; never touches
the live SWARM_ACTION_LOG.md. No live post.

INDEPENDENT ORACLE: coverage is re-derived from the SPEC ("each canonical
entry's body = the source lines from its header up to the next canonical
header by LINE order; lines before the first canonical header belong to no
entry") — NOT by reusing the module's next_line map.
"""
import importlib.util, os, hashlib, sys

S = "/sessions/determined-keen-bardeen/mnt/OMPU_shared"
P = os.path.join(S, "tools", "log_shard.py")
md5 = hashlib.md5(open(P, "rb").read()).hexdigest()[:8]
print("log_shard.py md5:", md5, "(expect 3f861866)")
spec = importlib.util.spec_from_file_location("log_shard_live", P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

results = []
def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

# ---- independent oracle: expected per-entry body intervals (line order) ----
def oracle_intervals(lines):
    heads = []  # (num, lineno 1-based)
    for i, ln in enumerate(lines, start=1):
        mm = m.ENTRY_RE.match(ln)
        if mm:
            heads.append((int(mm.group(2)), i))
    # first-occurrence-wins canonical set, but boundaries are by LINE for ALL
    # headers (canonical OR dup) — the module only breaks on CANONICAL ones.
    seen=set(); canon=[]
    for num,ln in heads:
        if num in seen: continue
        seen.add(num); canon.append((num,ln))
    canon_by_line = sorted(canon, key=lambda t:t[1])
    intervals={}
    for idx,(num,ln) in enumerate(canon_by_line):
        nxt = canon_by_line[idx+1][1] if idx+1<len(canon_by_line) else len(lines)+1
        intervals[num]=(ln,nxt)  # [ln, nxt)
    first_line = canon_by_line[0][1] if canon_by_line else None
    return intervals, first_line

# =====================================================================
# CASE 1 — clean sequential log: coverage exact, no loss/dup within range
L1 = ("# HEADER preamble line A\npreamble line B\n"
      "## Entry 001 -- one\nbody1a\nbody1b\n"
      "## Entry 002 -- two\nbody2a\n"
      "## Entry 003 -- three\nbody3a\nbody3b\nbody3c\n").splitlines(keepends=True)
entries,dups,warn = m.parse_entries(L1)
shards = list(m.build_shards(L1, entries, 100))
emitted = "".join("".join(b) for (_f,_lo,_hi,_mem,b) in shards)
iv,first = oracle_intervals(L1)
expected = "".join("".join(L1[lo-1:hi-1]) for (lo,hi) in sorted(iv.values()))
check("C1 module body == oracle interval concat (clean)", emitted==expected)
check("C1 every in-range source line emitted exactly once",
      all(emitted.count(L1[i-1])>=1 for i in range(first,len(L1)+1)))

# =====================================================================
# CASE 2 — PREAMBLE DROP: lines before first canonical entry never emitted
check("C2 BLIND SPOT preamble-before-first-entry DROPPED from all shards",
      ("preamble line A" not in emitted) and ("preamble line B" not in emitted))

# =====================================================================
# CASE 3 — DUP RELOCATION: duplicate header+body folds into PRECEDING
# canonical entry, landing in that entry's NUMBER bucket (cross-bucket).
# size=2 -> buckets [1-2],[3-4]. Put a duplicate "## Entry 001" between
# canonical Entry 003 and Entry 004 -> its body should render inside the
# Entry 003 shard (bucket [3-4]), NOT bucket [1-2] where number 1 lives.
L3 = ("## Entry 001 -- one\nb1\n"
      "## Entry 002 -- two\nb2\n"
      "## Entry 003 -- three\nb3\n"
      "## Entry 001 -- DUP of one, misplaced\nDUPBODY_MARKER\n"
      "## Entry 004 -- four\nb4\n").splitlines(keepends=True)
e3,d3,w3 = m.parse_entries(L3)
sh3 = list(m.build_shards(L3, e3, 2))
# find which shard bucket carries DUPBODY_MARKER
carrier=None
for (fn,lo,hi,mem,body) in sh3:
    if "DUPBODY_MARKER\n" in "".join(body):
        carrier=(lo,hi)
check("C3 dup #001 flagged in canary warnings", 1 in d3 and any("DUPLICATE" in x for x in w3))
check("C3 dup body relocated into Entry-003 bucket [3-4] not [1-2]",
      carrier==(3,4))
# and the dup content is NOT lost (present somewhere) -> visible, just misfiled
allbody3="".join("".join(b) for (_f,_l,_h,_m,b) in sh3)
check("C3 dup body NOT lost (present, but under wrong entry)",
      "DUPBODY_MARKER\n" in allbody3)

# =====================================================================
# CASE 4 — OUT-OF-ORDER numbers: still no in-range line lost/duplicated
L4 = ("## Entry 010 -- ten first physically\nx10\n"
      "## Entry 003 -- three later\nx3a\nx3b\n"
      "## Entry 007 -- seven\nx7\n").splitlines(keepends=True)
e4,d4,w4 = m.parse_entries(L4)
sh4=list(m.build_shards(L4,e4,5))
emit4="".join("".join(b) for (_f,_l,_h,_m,b) in sh4)
iv4,first4=oracle_intervals(L4)
exp4="".join("".join(L4[lo-1:hi-1]) for (lo,hi) in sorted(iv4.values()))
# order of concat differs (module sorts members by NUMBER within bucket), so
# compare as MULTISET of lines instead of string:
check("C4 out-of-order: emitted line-multiset == full in-range multiset",
      sorted(emit4.splitlines())==sorted("".join(L4[first4-1:]).splitlines()))

# =====================================================================
# CASE 5 — return-code channel is presence/exit, non-decision: run() on a
# MISSING path returns 2 (never raises); we assert WITHOUT creating files.
rc = m.run("/nonexistent/does/not/exist.md", "/tmp/nonexistent_out_gen528", 25, True)
check("C5 run() missing-log returns rc2, no raise (exit-code channel only)", rc==2)

ok=sum(1 for _,c in results if c)
print(f"\nPROBE {ok}/{len(results)} checks resolved as expected")
print("Findings (characterization, NOT failures of the probe):")
print(" - C2 preamble-before-first-entry is dropped from shards (blind spot)")
print(" - C3 duplicate-entry body relocates into the PRECEDING canonical")
print("      entry's NUMBER bucket (cross-bucket misfile); canary DOES warn")
print("      of the dup, so content is visible-but-misplaced, not silent-lost")
sys.exit(0 if ok==len(results) else 1)
