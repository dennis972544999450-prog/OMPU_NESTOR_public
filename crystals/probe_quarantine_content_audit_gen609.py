#!/usr/bin/env python3
"""gen-609: CONTENT-аудит block-карантина infoblock. Read-only.
Predictions locked pre-run (md5 b75f56f3). Corpus md5 pre==post c59c6349.
Usage: OMPU_SHARED=$S python3 probe_quarantine_content_audit_gen609.py"""
import re, glob, os, collections
S = os.environ.get("OMPU_SHARED", "/sessions/*/mnt/OMPU_shared")
blocks = sorted(glob.glob(f"{glob.glob(S)[0] if '*' in S else S}/infoblock/blocks/*.md"))
q, nostatus = [], 0
for b in blocks:
    t = open(b, encoding="utf-8", errors="replace").read()
    if re.search(r'^status:\s*"?quarantine"?\s*$', t, re.M): q.append((b, t))
    elif not re.search(r"^status:", t, re.M): nostatus += 1
def fm(t, k):
    m = re.search(rf'^{k}:\s*(.+)$', t, re.M)
    return m.group(1).strip().strip('"') if m else None
ct = collections.Counter(fm(t, "content_type") for _, t in q)
bc_missing = sum(1 for _, t in q if fm(t, "block_class") is None)
qr = collections.Counter(fm(t, "quarantine_reason") for _, t in q)
fams = collections.Counter()
for _, t in q:
    s = fm(t, "source_id") or "NONE"
    fams[re.sub(r"-(v\d[^ ]*)?-?\d*$", "", re.sub(r"-[0-9a-f]{8}-\d+$|-\d+$", "", s))] += 1
print(f"total={len(blocks)} quarantined={len(q)} canonical_without_status_field={nostatus}")
print(f"block_class_missing={bc_missing}/{len(q)}  content_type={dict(ct)}")
print(f"families={dict(fams)}")
print("reasons:", *[f"  {n}x {r}" for r, n in qr.most_common()], sep="\n")
# Findings (2026-07-10): 33 quarantined; canonical = ABSENCE of status field (promote = line deletion);
# 22/33 (seed-vocabulary v0.5/v0.6 + NEO-OPERATORS) have NO source doc anywhere reachable => quarantine is SOLE CUSTODY;
# Beyond_Bits_v0.8.md alive in Den's Downloads => 11 recoverable. 28/33 reasons = "awaiting review" that never came.
