import random, math, json
res=[]
for n in (5,8,11,15,20,30):
    R=random.Random(70471+n); hits=0; T=120000
    for _ in range(T):
        nulls=[R.gauss(0,1) for _ in range(n)]
        real=R.gauss(0,1)
        if real<min(nulls) or real>max(nulls): hits+=1
    p=hits/T; th=2/(n+1); se=math.sqrt(th*(1-th)/T)
    res.append({"n":n,"obs":round(p,5),"theory":round(th,5),
                "z":round((p-th)/se,2),"within_3se":abs(p-th)<3*se})
print(json.dumps(res,ensure_ascii=False))
# non-normal control: the claim is distribution-free, so a skewed law must give the same
res2=[]
for n in (5,11,30):
    R=random.Random(999+n); hits=0; T=120000
    for _ in range(T):
        nulls=[R.expovariate(1.0)**3 for _ in range(n)]
        real=R.expovariate(1.0)**3
        if real<min(nulls) or real>max(nulls): hits+=1
    p=hits/T; th=2/(n+1); se=math.sqrt(th*(1-th)/T)
    res2.append({"n":n,"law":"expo^3","obs":round(p,5),"theory":round(th,5),
                 "z":round((p-th)/se,2),"within_3se":abs(p-th)<3*se})
print(json.dumps(res2,ensure_ascii=False))
