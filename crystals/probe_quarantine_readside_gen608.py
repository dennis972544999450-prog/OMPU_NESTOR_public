#!/usr/bin/env python3
"""Read-only probe: quarantine read-side in live infoblock. Bolt gen-608, 2026-07-10.
P1 table exists / P2 no reader beyond writer / P3 resolved never set / P4 audit events exist.
Result: P1-P3 GREEN, P4 productive FAIL (0 events => edge-quarantine aspirational).
Bonus: block-quarantine = roach motel (33/153 stuck, no status-promote tool)."""
import sqlite3, subprocess, sys, glob, re
from pathlib import Path

S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "OMPU_shared"
db = S / "infoblock/indexes/edges.db"
conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("P1 quarantined_edges exists:", "quarantined_edges" in tables)
if "quarantined_edges" in tables:
    print("   rows:", cur.execute("SELECT COUNT(*) FROM quarantined_edges").fetchone()[0])
    print("P3 resolved=1 rows:", cur.execute("SELECT COUNT(*) FROM quarantined_edges WHERE resolved=1").fetchone()[0])
ev = cur.execute("SELECT COUNT(*) FROM audit_log WHERE action LIKE '%quarantine%' OR action LIKE '%restore%'").fetchone()[0]
print("P4 quarantine/restore audit events:", ev, "(0 => aspirational)")
conn.close()

readers = subprocess.run(["grep", "-rl", "quarantined_edges", str(S), "--include=*.py", "--include=*.sh", "--include=*.js"],
                         capture_output=True, text=True).stdout.splitlines()
readers = [r for r in readers if "__pycache__" not in r and ".bak" not in r]
print("P2 files touching quarantined_edges:", readers)

blocks = list((S / "infoblock/blocks").glob("*"))
q = [b for b in blocks if b.is_file() and re.search(r'^status:\s*"?quarantine"?\s*$',
     b.read_text(errors="ignore"), re.M)]
print(f"block-quarantine: {len(q)}/{len(blocks)} blocks stuck in status=quarantine")
