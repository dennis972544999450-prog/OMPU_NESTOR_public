#!/usr/bin/env python3
"""
test_jt_state_drift_nullguard_APPLIED_verify_bolt_gen386.py
Bolt gen-386 (claude-opus-4-8), 2026-07-05.

Independent NULL-capable verify of Nestor gen-0937's APPLIED symmetric fail-loud
null-guard on the LIVE jt_state_drift_check.py (gen-377 find, gen-385 forward-proof).
No network (live_max_jt monkeypatched). Mount-portable (resolves tool beside this file).

Round-trip, every branch reachable, genuinely failable:
  FIXED  total-parse-miss + live 9999 -> exit 2  (silent-green CLOSED, loud)
  FIXED  aligned          + live 9999 -> exit 0  (NO false-positive)   [could over-fire]
  FIXED  stale-parseable  + live 9999 -> exit 1  (real drift STILL RED)[could swallow RED]
  FIXED  real SWARM_STATE + live 288  -> exit 0  (guard SKIPS real doc, no false-fire)
  REVERT(guard stripped) miss+9999    -> exit 0  (ORACLE: pre-fix bug reproduced)
Divergence FIXED(exit2) vs REVERT(exit0) on the SAME miss input == guard is load-bearing.
Run: python3 test_...gen386.py  -> ALL_OK exit 0
"""
import importlib.util, io, contextlib, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(HERE, "jt_state_drift_check.py")
STATE_REAL = os.path.join(os.path.dirname(HERE), "SWARM_STATE.md")

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def make_revert(src_path):
    """Synthesize pre-fix source by stripping the 3-line total-parse-miss guard."""
    src = open(src_path, encoding="utf-8").read()
    revert = re.sub(
        r'\n\s*if last_c is None and next_c is None:\n\s*print\("PARSE-FAIL[^\n]*\n\s*return 2\n',
        '\n', src, count=1)
    assert revert != src, "guard not found in live tool — is the fix actually applied?"
    f = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
    f.write(revert); f.close(); return f.name

def run(mod, statedoc, live_max):
    mod.live_max_jt = lambda timeout=12: (live_max, 5)   # NO network
    mod.STATE = statedoc
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main()
    return rc, (buf.getvalue().strip().splitlines() or [""])[0]

def write(txt):
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(txt); f.close(); return f.name

MISS    = write("# unrelated doc\njust prose about wet fish, no jt anchors\n")
ALIGNED = write("- **JT last:** jt-9999\n- **next JT:** jt-10000\n")
STALE   = write("- **last:** jt-0288\n- **Следующий JT ID:** jt-0289\n")

cases = [
 ("FIXED  miss    +9999", LIVE, MISS,       9999, 2),
 ("FIXED  aligned +9999", LIVE, ALIGNED,    9999, 0),
 ("FIXED  stale   +9999", LIVE, STALE,      9999, 1),
 ("FIXED  realdoc + 288 ", LIVE, STATE_REAL, 288, 0),
]
REV = make_revert(LIVE)
cases.append(("REVERT miss    +9999", REV, MISS, 9999, 0))

allok = True
for i,(label,tool,doc,lm,expect) in enumerate(cases):
    rc, first = run(load(tool, f"m{i}"), doc, lm)
    ok = rc == expect; allok &= ok
    print(f"[{'OK ' if ok else 'FAIL'}] {label}  exit={rc} expect={expect}  :: {first}")
os.unlink(REV)
print("ALL_OK" if allok else "SOME_FAILED")
sys.exit(0 if allok else 1)
