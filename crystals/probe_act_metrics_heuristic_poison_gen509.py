#!/usr/bin/env python3
# gen-509 FAILABLE probe: can marker-stuffing prose flip act_metrics
# informative_fraction_pct and the post_norm.alert? Then: does ANY consumer
# gate an irreversible action on it? Real importlib run on a mkdtemp log copy.
import os, tempfile, importlib.util
from pathlib import Path

def build_log(stuffed):
    # entries >= NORM_BIRTH_ENTRY(143) count in post_norm scope.
    hdrs = []
    for n in range(143, 148):
        if stuffed:
            body = "prediction: expected X. Outcome confirmed, no scar. факт: попало."
        else:
            body = "did some work, moved a file, wrote a note. nothing special."
        hdrs.append(f"### Entry {n} | gen-{n} | 2026-07-07 | {body}\n{body}\n")
    return "\n".join(hdrs)

def load_am(logtext):
    d = tempfile.mkdtemp()
    Path(d, "SWARM_ACTION_LOG.md").write_text(logtext, encoding="utf-8")
    os.environ["OMPU_SHARED"] = d
    src = "/sessions/cool-intelligent-lamport/mnt/OMPU_shared/tools/act_metrics.py"
    spec = importlib.util.spec_from_file_location(f"am_{os.path.basename(d)}", src)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

for label, stuffed in [("CLEAN (no markers)", False), ("POISON (marker-stuffed)", True)]:
    m = load_am(build_log(stuffed))
    rep = m.windows_report()
    pn = rep["post_norm"]
    print(f"{label:26} frac={pn['informative_fraction_pct']:5}%  alert={pn['alert']}  regr_pp={pn['regression_from_baseline_pp']}")
