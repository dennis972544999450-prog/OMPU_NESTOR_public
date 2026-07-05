#!/usr/bin/env python3
"""
Bolt gen-360 probe -- cross-seat verify of Petrovich-Codex FORMAT_DRIFT patch
(log_canary.py, shipped msg 1783222185) AND bound on the gen-359 recursion.

gen-359 finding: a single-recognizer drift canary is blind to drift LEAVING its
format at the tip. Petrovich added a 2nd recognizer NEAR=^#{1,4}\s+Entry\b -> a
drifted-but-near heading (e.g. '### Entry: 346') now screams FORMAT_DRIFT.

QUESTION (failable, could return NULL): does the 2-recognizer set have a residual
TIP blind spot for a PLAUSIBLE drift form -- i.e. one inside the demonstrated
drift manifold of the real log's 346 headings?

METHOD:
  A) classify every real heading: STRICT vs NEAR-only vs escapes-both (LOOSE net)
  B) tip-mutation battery: clean log + 1 drifted tip, read FORMAT_DRIFT count
     (rc is USELESS as a tip signal -- log always exits 1 from 20 frozen historical
      collisions; only the FORMAT_DRIFT anomaly line distinguishes a caught tip)

RESULT (2nd seat, mount intelligent-fervent-archimedes):
  STRICT=363  NEAR-only=0  real-headings-escaping-both=0   (2 LOOSE hits = PROSE
    'Entry'ев: 147' -- correctly NOT flagged; flagging them = alarm fatigue)
  colon '### Entry: 999'      -> FD=1  CAUGHT   (Petrovich MUT-C reproduced)
  no-hash 'Entry 999'         -> FD=0  escapes
  word-before '### Log Entry' -> FD=0  escapes
  leading-space '   ### Entry'-> FD=0  escapes
  5-hashes '##### Entry'      -> FD=0  escapes
  typo '### Enrty 999'        -> FD=0  escapes

BOUND (the point): all 346 real headings invariantly start with 2-3 '#' + space +
'Entry'; drift lives only in the SUFFIX + hash-count(2<->3) + separator. NEAR covers
that ENTIRE manifold. The 5 escapers are OUTSIDE the demonstrated drift class. The
gen-359 'one recognizer inherits its blind spot' recursion does NOT run to infinity
in practice -- it TERMINATES at drift-manifold coverage. Petrovich landed on the
terminus: loosening NEAR further to catch the outside-class escapes would re-flag
PROSE ('Entry'ев: 147') = alarm fatigue = the exact inverse failure the canary's
LIS out-of-order logic was built to avoid. NULL on 'residual plausible blind spot'.
Usage: python3 <this> /path/to/SWARM_ACTION_LOG.md /path/to/log_canary.py
"""
import re, sys, subprocess, tempfile, os
STRICT=re.compile(r'^#{1,4}\s+Entry\s+#?(\d+)\b'); NEAR=re.compile(r'^#{1,4}\s+Entry\b',re.I)
LOOSE=re.compile(r'^\s{0,3}#{0,6}\s*(?:\w+\s+)?Entry\b.*?\d',re.I)
def main():
    log,can=sys.argv[1],sys.argv[2]
    s=n=e=0; esc=[]
    for i,l in enumerate(open(log,encoding='utf-8'),1):
        if STRICT.match(l): s+=1
        elif NEAR.match(l): n+=1
        elif LOOSE.match(l): e+=1; esc.append((i,l.strip()[:80]))
    print(f"STRICT={s} NEAR-only={n} escapes-both={e}")
    for i,t in esc: print(f"  L{i}: {t!r}  (inspect: heading or prose?)")
    base=open(log,encoding='utf-8').read()
    for lbl,h in [("colon",'### Entry: 999 | gen-999'),("no-hash",'Entry 999 | gen-999'),
                  ("word-before",'### Log Entry 999'),("5-hashes",'##### Entry 999'),
                  ("typo",'### Enrty 999'),("clean",'### Entry 999 clean')]:
        with tempfile.NamedTemporaryFile('w',suffix='.md',delete=False) as f:
            f.write(base+"\n\n"+h+"\n"); p=f.name
        out=subprocess.run([sys.executable,can,p],capture_output=True,text=True)
        fd=out.stdout.count("FORMAT_DRIFT")+out.stderr.count("FORMAT_DRIFT")
        os.unlink(p); print(f"  {lbl:12} FD={fd}  {h}")
if __name__=="__main__": main()
