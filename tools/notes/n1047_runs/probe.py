import math, json
from fractions import Fraction

def env(n): return 2.0/(n+1)
def formula(a): return int(math.ceil(2.0/a - 1.0))
def func(a):                      # bolt gen-676, verbatim shape
    if not a or a<=0 or a>=1: return None
    r = max(1, int(math.ceil(2.0/a - 1.0)))
    while r>1 and 2.0/r <= a: r -= 1
    while 2.0/(r+1) > a: r += 1
    return r

N=2000
# P1: float round-trip of the closed form
miss=[n for n in range(1,N+1) if formula(env(n))!=n]
# P3: off-by-how-much
deltas=sorted({formula(env(n))-n for n in miss})
# P2: exact arithmetic
def formula_exact(a):
    q = Fraction(2,1)/a - 1
    return math.ceil(q)
miss_exact=[n for n in range(1,N+1) if formula_exact(Fraction(2,n+1))!=n]
# P4: does the FUNCTION round-trip?
miss_func=[n for n in range(1,N+1) if func(env(n))!=n]
# monotonicity of float env over the range (the property the loop leans on)
vals=[env(n) for n in range(1,N+1)]
mono=all(vals[i]>vals[i+1] for i in range(len(vals)-1))
# collisions
coll=len(vals)-len(set(vals))
# P5: alphas a human types
human=[0.20,0.10,0.05,0.025,0.01,0.005,0.001]
def truth(a):                      # exact: smallest r with 2/(r+1) <= a
    r=math.ceil(Fraction(2).__truediv__(Fraction(a).limit_denominator(10**9))-1)
    return r
tbl=[]
for a in human:
    ex = Fraction(2)/Fraction(a).limit_denominator(10**9) - 1
    tbl.append({"alpha":a,"formula":formula(a),"func":func(a),"exact":math.ceil(ex)})
dis=[t for t in tbl if not (t["formula"]==t["func"]==t["exact"])]

out={"P1_float_misses":len(miss),"P1_first10":miss[:10],
     "P3_deltas":deltas,"P3_all_off_by_one":deltas==[1] or deltas==[-1],
     "P2_exact_misses":len(miss_exact),
     "P4_func_misses":len(miss_func),
     "float_env_strictly_decreasing":mono,"float_alpha_collisions":coll,
     "P5_table":tbl,"P5_disagreements":dis}
print(json.dumps(out,indent=1,ensure_ascii=False))
