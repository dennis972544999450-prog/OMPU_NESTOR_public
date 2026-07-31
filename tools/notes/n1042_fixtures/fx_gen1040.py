# fixture reproducing nestor gen-1040's own defect (that probe was never shipped)
def probe(intervals):
    mf = median(intervals)              # 0.0 is a LEGAL measured value here
    median_gap = mf if mf else "n/a"    # <-- swallows a real zero
    print(f"median gap full = {median_gap}")
    return {"median_gap": median_gap}
