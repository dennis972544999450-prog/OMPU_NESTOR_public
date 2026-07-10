#!/usr/bin/env python3
"""
Probe (Nestor gen-1013): full-lifecycle verify of gen-1011 FIRSTUSE cargo against the
LIVE graph DB (not the drain report), + four-provenance-surface disjointness.

Re-derivable oracle. Read-only. Contract locked before run: 4 predictions, 2 flipped.
  [A] exactly 1 blocks row for the id, active, created_at at live-drain second   -> PASS
  [B] exactly 1 drainer_applied_intents row (idempotency key)                     -> PASS
  [C] intent_ledger rows for the intent == 0 (then: 0 globally)                   -> FLIP
  [D] no graph_changelog row for the block.create                                 -> FLIP

Usage: python3 probe_gen1011_lifecycle_four_provenance_surfaces_nestor_gen1013.py [DB]
Default DB: OMPU_Housemaster/memory/infograph_v0_1.db
"""
import sqlite3, sys, os

DB = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/OMPU_Housemaster/memory/infograph_v0_1.db")
BID = "scar_loader_suffix_measurement_artifact__nestor_gen1008"
IID = "mcp-d0fa30d2ccc04d0c961b2bd33eb29a77"

def main():
    c = sqlite3.connect(DB); cur = c.cursor()
    results = []

    n_block = cur.execute("SELECT COUNT(*) FROM blocks WHERE id=?", (BID,)).fetchone()[0]
    row = cur.execute("SELECT state, created_by_agent, created_at FROM blocks WHERE id=?",
                      (BID,)).fetchone()
    A = (n_block == 1 and row and row[0] == "active" and row[1] == "nestor"
         and row[2].startswith("2026-07-10T14:15"))
    results.append(("A block singular+active+live-drain-ts", A, f"n={n_block} row={row}"))

    n_dai = cur.execute("SELECT COUNT(*) FROM drainer_applied_intents WHERE intent_id=?",
                        (IID,)).fetchone()[0]
    B = (n_dai == 1)
    results.append(("B one idempotency record", B, f"n={n_dai}"))

    n_il_mine = cur.execute("SELECT COUNT(*) FROM intent_ledger WHERE intent_id=?",
                            (IID,)).fetchone()[0]
    n_il_all = cur.execute("SELECT COUNT(*) FROM intent_ledger").fetchone()[0]
    C = (n_il_mine == 0)  # predicted present; FLIPPED -> absent (and globally empty)
    results.append(("C intent_ledger blind to my intent", C,
                    f"mine={n_il_mine} global={n_il_all} (zero-write ledger)"))

    # changelog has no per-block target column; check none references the block id/summary
    n_cl_mine = cur.execute(
        "SELECT COUNT(*) FROM graph_changelog WHERE summary LIKE ?", (f"%{BID}%",)).fetchone()[0]
    D = (n_cl_mine == 0)
    results.append(("D changelog blind to block.create", D, f"matches={n_cl_mine}"))

    # provenance-surface census
    n_dai_all = cur.execute("SELECT COUNT(*) FROM drainer_applied_intents").fetchone()[0]
    n_blocks = cur.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
    print(f"provenance surfaces: blocks={n_blocks} drainer_applied={n_dai_all} "
          f"intent_ledger={n_il_all} changelog={cur.execute('SELECT COUNT(*) FROM graph_changelog').fetchone()[0]}")
    print(f"drained-path blocks: {n_dai_all}/{n_blocks} "
          f"({100*n_dai_all/n_blocks:.2f}% came through the audited drainer)")
    print()

    ok = 0
    for name, val, detail in results:
        tag = "PASS" if val else "FAIL"
        ok += val
        print(f"[{tag}] {name}  — {detail}")
    print(f"\n{ok}/4 predictions held ({4-ok} flipped by design; flips = the finding).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
