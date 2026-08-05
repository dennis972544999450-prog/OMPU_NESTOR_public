import sys, math, json
sys.path.insert(0, "/sessions/inspiring-hopeful-allen/mnt/OMPU_shared/tools")
import null_agent as na
miss=[]
for n in range(1,2001):
    a=na.envelope_alpha(n); r=na.reps_for_alpha(a)
    if r!=n: miss.append((n,a,r))
print("REAL FUNCTION round-trip misses n=1..2000:", len(miss))
print("misses:", miss[:5])
print("envelope_alpha(1) =", na.envelope_alpha(1), "-> reps_for_alpha ->", na.reps_for_alpha(na.envelope_alpha(1)))
print("envelope_alpha(2) =", na.envelope_alpha(2), "-> ", na.reps_for_alpha(na.envelope_alpha(2)))
print("reps_for_alpha(1.0) =", na.reps_for_alpha(1.0))
print("reps_for_alpha(0.9999999) =", na.reps_for_alpha(0.9999999))
print("envelope_alpha(0) =", na.envelope_alpha(0))
