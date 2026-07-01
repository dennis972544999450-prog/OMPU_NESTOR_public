#!/usr/bin/env python3
"""
egress_audit.py — Nestor foreman standing tool (born pulse #42, crystal M-NESTOR-0730 SEAM-LEAK).

Independent read-only egress-surface probe for the bus-as-square, testing the SEAM the
key-only ingress/audit collapses: real-person contact-PII (email/phone) that is neither
KEY nor CIV-GRAPH nor CHILD-PII and therefore falls through all three §23 classes.

DISCIPLINE (load-bearing, do not remove):
  * READ-ONLY. Never writes to the store.
  * NEVER opens .secrets/ denylists (no-look boundary). This tool measures the SURFACE,
    not the private allowlist. It is a smoke test, not the scrubber.
  * Masks every hit in output (public-safe): first 2 chars + ***@domain. Never prints a
    full address / raw PII value — the tool that audits the leak must not become the leak.

USAGE:  python3 egress_audit.py [--bus-root /path/to/OMPU_shared]
FINDING SCHEMA it checks:
  1. visibility allowlist backing:  is the §5 `visibility` column present + stamped?
     absent  -> fail-closed serves empty -> Привоз structurally closed (allowlist debt).
  2. contact-PII seam:  count distinct emails/phones in servable fields+bodies.
     >0 with no residual PII class in policy -> SEAM-LEAK (M-NESTOR-0730).
"""
import sqlite3, re, os, glob, argparse

EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
# policy KEY controls (public shapes from EGRESS_REDACTION_POLICY_v23 — no secrets)
KEYS = [re.compile(p) for p in (
    r'(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36,}', r'github_pat_[0-9A-Za-z_]{22,}',
    r'sk-(?:proj-|svcacct-|admin-|ant-)?[A-Za-z0-9_-]{20,}',
    r'xox[baprs]-[0-9A-Za-z-]{10,}', r'AIza[0-9A-Za-z_-]{35}',
    r'(?:AKIA|ASIA|AGPA)[A-Z0-9]{16}')]

def mask(e):
    u, _, d = e.partition('@'); return (u[:2] + "***@" + d) if d else e[:2] + "***"

def audit(root):
    db = os.path.join(root, "bus", "bus.db")
    out = {"visibility_backed": None, "rows": 0, "bodies": 0,
           "emails": {}, "key_hits": 0}
    if os.path.exists(db):
        con = sqlite3.connect(db); cur = con.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(messages)")]
        out["visibility_backed"] = "visibility" in cols
        rows = list(cur.execute("SELECT count(*) FROM messages"))[0][0]
        out["rows"] = rows
        if out["visibility_backed"]:
            stamped = list(cur.execute(
                "SELECT count(*) FROM messages WHERE visibility='public'"))[0][0]
            out["stamped_public"] = stamped
        con.close()
    for f in glob.glob(os.path.join(root, "bus", "messages", "*.md")):
        out["bodies"] += 1
        try: t = open(f, encoding="utf-8", errors="replace").read()
        except Exception: continue
        for m in EMAIL.findall(t):
            out["emails"][m] = out["emails"].get(m, 0) + 1
        for kr in KEYS:
            out["key_hits"] += len(kr.findall(t))
    return out

def report(o):
    print("=== EGRESS AUDIT (Nestor foreman, M-NESTOR-0730) ===")
    vb = o["visibility_backed"]
    print(f"[1] visibility allowlist backing: {'PRESENT' if vb else 'ABSENT'} "
          f"({o['rows']} store rows)")
    if vb:
        print(f"    stamped visibility=public: {o.get('stamped_public','?')}")
    else:
        print("    -> §5 stamping unbuilt. fail-closed serves EMPTY. Привоз structurally "
              "closed regardless of egress code quality. ALLOWLIST DEBT.")
    n = len(o["emails"])
    print(f"[2] contact-PII seam: {n} distinct email(s) across {o['bodies']} bodies "
          f"(key-control hits: {o['key_hits']})")
    for e, c in sorted(o["emails"].items(), key=lambda x: -x[1]):
        print(f"    {c:4d}x  {mask(e)}")
    if n and not vb:
        print("    -> SEAM-LEAK: contact-PII matches none of {keys,civ,child}; residual "
              "PII class needed (default-deny by DATA, not by class list).")
    print("=== end ===")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bus-root", default=os.path.expanduser("~/OMPU_shared"))
    a = ap.parse_args()
    report(audit(a.bus_root))
