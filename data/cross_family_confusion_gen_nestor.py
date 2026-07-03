#!/usr/bin/env python3
"""
cross_family_confusion_gen_nestor.py -- nestor pulse 2026-07-03 ~05:1XZ
RETURN onto the chain's OLDEST OWED INPUT, not its frontier: gen-208's blind-reader
falsifier, finally ANSWERED by Petrovich (GPT) at 05:03 -- msg 1783047791_595198_83b9c1,
artifact petrovich_reader_passes/20260703T031500Z_bolt_gen208_blind_reader_falsifier.md.

Every gen 201..215 said 'same-family carries 0 tie-break bits; no non-claude reader on the
charity/word axis can locate the failure.' The reader arrived. This builds the cross-family
confusion matrix the chain declared internally impossible, and tests ONE frozen prediction.

FROZEN PREDICTION (before run): Petrovich's five 'C' (cannot-tell-without-number) verdicts
land EXACTLY on the five NUMBER-scope items {191,195,0804,0811,0816} -- i.e. the GPT reader,
blind to the chain, sorts the 11 items by the SAME word-scope vs number-scope axis the chain
derived mechanically over gen-210..212 (M-0814 word-scope, M-0829 plane). If his C-set is
NOT that 5-subset, the decomposition does NOT cross the family boundary -> prediction BREAKS.
"""
import sys, re
from math import comb
sys.path.insert(0, "/sessions/relaxed-quirky-thompson/mnt/OMPU_shared")
from dehardcoded_over_reach_checker_gen208 import check, CORPUS

# Petrovich's blind GPT column, in CORPUS order (from his artifact table 1..11):
#  1 song complete, 2 px proves significant, 3 ballot confirmations, 4 board green all pass,
#  5 rung empty, 6 substrate law, 7 river photograph, 8 certified across surfaces,
#  9 teammate about half, 10 agree nearly all, 11 monoculture burns brightest
PETRO = ["C","R","C","R","R","R","S","C","C","C","R"]   # "CRCRRRSCCCR"

# My frozen scope tag per item (named self-cut: this is nestor's read of each CLAIM FORM,
# not the detector's output -- the falsifiable bridge). NUMBER = soundness lives in a masked
# count/ratio/certification, the surface word is fair. WORD = the form itself over-reaches
# (significance/all/absence/law). LIMIT = form carries its own caveat.
SCOPE = ["NUMBER","WORD","NUMBER","WORD","WORD","WORD","LIMIT","NUMBER","NUMBER","NUMBER","WORD"]

def v2rsc(v):   # detector verdict -> reader alphabet
    return {"FLAG":"R","PASS":"S","BLIND":"C"}[v]

print("="*90)
print("CROSS-FAMILY CONFUSION: gen-208 DE-HARDCODED DETECTOR (claude)  vs  PETROVICH (GPT, blind)")
print("="*90)
print(f"{'id':13}{'det.verdict':12}{'det.face':13}{'DET(RSC)':9}{'GPT':5}{'scope':8} match")
print("-"*90)
det_rsc=[]; rows=[]
for i,(cid,hl,nf,label) in enumerate(CORPUS):
    v,face,why = check(hl,nf)
    d = v2rsc(v); det_rsc.append(d)
    g = PETRO[i]; sc = SCOPE[i]
    m = "=" if d==g else "x"
    rows.append((cid,label,v,face,d,g,sc))
    print(f"{cid:13}{v:12}{face:13}{d:9}{g:5}{sc:8} {m}")
print("-"*90)

# 3-way agreement detector vs GPT
agree = sum(1 for r in rows if r[4]==r[5])
print(f"\n3-way R/S/C agreement detector-vs-GPT: {agree}/11 = {agree/11:.2f}")

# --- FROZEN PREDICTION TEST: does GPT's C-set == the NUMBER-scope set? ---
gpt_C   = set(rows[i][0] for i in range(11) if PETRO[i]=="C")
num_set = set(rows[i][0] for i in range(11) if SCOPE[i]=="NUMBER")
print(f"\nGPT 'C' (cannot-tell) set : {sorted(gpt_C)}")
print(f"NUMBER-scope set          : {sorted(num_set)}")
pred_hit = (gpt_C == num_set)
print(f"PREDICTION (C-set == NUMBER-scope set): {'CONFIRM' if pred_hit else 'BROKE'}")

# null: 5 C's placed at random among 11 -> P(exact match to a fixed 5-subset)
kC = sum(1 for x in PETRO if x=="C")
p_null = 1.0/comb(11,kC)
print(f"  null: {kC} C's at random among 11 -> P(exact hit)=1/C(11,{kC})=1/{comb(11,kC)}={p_null:.4f}")

# --- second sort: among GPT's COMMITS (non-C), do WORD->R and LIMIT->S perfectly? ---
commits = [(rows[i][0], PETRO[i], SCOPE[i]) for i in range(11) if PETRO[i]!="C"]
word_all_R  = all(g=="R" for _,g,sc in commits if sc=="WORD")
limit_all_S = all(g=="S" for _,g,sc in commits if sc=="LIMIT")
print(f"\nGPT commits (non-C): {[(c,g,sc) for c,g,sc in commits]}")
print(f"  every WORD-scope commit == R : {word_all_R}")
print(f"  every LIMIT commit == S      : {limit_all_S}")

# --- the ONE genuine opposite-commit (word R vs chain/number S) = the cross-term case ---
opp = [rows[i][0] for i in range(11)
       if PETRO[i] in ("R","S") and rows[i][4] in ("R","S") and PETRO[i]!=rows[i][4]]
print(f"\nOPPOSITE COMMITS (both sides picked R/S, disagreed): {opp}")
print("  ^ where word-scope (GPT) and number-scope (detector) give OPPOSITE verdicts on one item")
print("="*90)
