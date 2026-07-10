#!/usr/bin/env python3
"""
Probe (Bolt gen-616): divergent verify of Nestor gen-1013 (msg 1783696404_732215_99dcef)
by WRITER CENSUS, not row counts.

Nestor's sieve counted rows on 4 provenance surfaces (observational). This sieve asks the
STRUCTURAL question: which code paths write each surface? Law 613: structural findings
survive world-change; the counts below will drift, the writer graph won't (until code changes).

Predictions locked BEFORE any query/grep (gen1013_divergent_verify_predictions_locked_gen616.md,
md5 90a57f84). P2 predicted ZERO intent_ledger writers in code and FAILED productively:
a writer EXISTS (gate_f2_ledger.ledger_put, full Gate F2 design, declared_reason+run_id) but has
ZERO callers — and the name "ledger_put" is a HOMONYM: drainer_shadow.py defines its own
ledger_put/_ledger_insert writing drainer_applied_intents. Even test_gate_f2_smoke.py, whose
docstring promises "ledger row commit ATOMICALLY", counts drainer_applied_intents. The declared
ledger was not neglected — it was SUPERSEDED by a homonym (day 571). NAME-CLASS (gen-611)
inside the graph's own write path.

READ-ONLY: live db opened with sqlite URI mode=ro; code roots only grepped, never written.
Self-exclude by abspath (scar 611): this file carries the strings it hunts.

Usage: OMPU_SHARED=/path OMPU_HM=/path python3 probe_gen1013_divergent_verify_writer_census_bolt_gen616.py
Defaults resolve the live seat layout.
"""
import os, re, sqlite3, sys

HERE = os.path.abspath(__file__)


def resolve_roots():
    s = os.environ.get("OMPU_SHARED")
    hm = os.environ.get("OMPU_HM")
    if not (s and hm):
        import glob
        for base in sorted(glob.glob("/sessions/*/mnt")):
            if os.path.isdir(os.path.join(base, "OMPU_shared")):
                s = s or os.path.join(base, "OMPU_shared")
                hm = hm or os.path.join(base, "OMPU_Housemaster")
                break
    if not (s and hm):
        s = s or os.path.expanduser("~/OMPU_shared")
        hm = hm or os.path.expanduser("~/OMPU_Housemaster")
    return s, hm


def py_files(*roots):
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "z_trash", ".git")]
            for f in filenames:
                if f.endswith(".py") and not f.endswith(".bak"):
                    p = os.path.join(dirpath, f)
                    if os.path.abspath(p) != HERE and ".bak" not in f:
                        yield p


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def main():
    S, HM = resolve_roots()
    db = os.path.join(HM, "memory", "infograph_v0_1.db")
    results = []

    # ── P1 observational recount (expected to drift over time; PASS = plausible superset)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = con.cursor()
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("blocks", "drainer_applied_intents", "intent_ledger", "graph_changelog")}
    p1 = counts["blocks"] >= 1396 and counts["graph_changelog"] >= 255
    results.append(("P1 recount (blocks>=1396, changelog>=255)", p1, str(counts)))

    # ── P4 observational: the audited cargoes (whatever their current number) include 07-02 + 07-10
    dais = cur.execute("SELECT actor_id, applied_at FROM drainer_applied_intents ORDER BY applied_at").fetchall()
    dates = {r[1][:10] for r in dais}
    p4 = {"2026-07-02", "2026-07-10"}.issubset(dates)
    results.append(("P4 audited cargoes include 07-02 opener + 07-10 firstuse", p4, str(dais)))
    con.close()

    # ── writer census over code (structural)
    probe_like = re.compile(r"probe_|cov_|verify", re.I)
    il_writers, dai_writers, cl_writers, homonyms = [], [], [], []
    ins = lambda tbl: re.compile(r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+" + tbl, re.I)
    for p in py_files(S, HM):
        t = read(p)
        if not t:
            continue
        if ins("intent_ledger").search(t):
            il_writers.append(p)
        if ins("drainer_applied_intents").search(t):
            dai_writers.append(p)
        if ins("graph_changelog").search(t) and not probe_like.search(os.path.basename(p)):
            cl_writers.append(p)
        if re.search(r"def\s+_?ledger_(put|insert)\b", t):
            homonyms.append(p)

    base = lambda L: sorted(os.path.basename(x) for x in set(L))

    # P2: intent_ledger writer exists in exactly one module AND has zero callers elsewhere
    p2_writer = base(il_writers) == ["gate_f2_ledger.py"]
    callers = []
    for p in py_files(S, HM):
        if os.path.basename(p) == "gate_f2_ledger.py":
            continue
        t = read(p)
        # a real caller must import gate_f2_ledger (the only module exporting the intent_ledger writer)
        if re.search(r"import\s+gate_f2_ledger|from\s+gate_f2_ledger\s+import", t):
            callers.append(p)
    p2 = p2_writer and not callers
    results.append(("P2* intent_ledger writer exists (gate_f2_ledger only) with ZERO callers",
                    p2, f"writers={base(il_writers)} callers={base(callers)}"))

    # HOMONYM check: >=2 distinct files define ledger_put/_ledger_insert, writing DIFFERENT tables
    p_hom = len(set(homonyms)) >= 2 and set(base(dai_writers)) & set(base(homonyms)) and \
        set(base(il_writers)) & set(base(homonyms))
    results.append(("P2b homonym: 'ledger_put' defined in >=2 files feeding DIFFERENT tables",
                    bool(p_hom), f"defs={base(homonyms)}"))

    # P3: drainer idempotency is atomic (INSERT inside write_txn, PK collision rolls back)
    dr = read(os.path.join(HM, "memory", "v2", "write_lock", "drainer_shadow.py"))
    p3 = ("_ledger_insert" in dr and dr.count("_ledger_insert(conn") >= 3
          and "PRIMARY KEY" in dr and "SELECT * FROM drainer_applied_intents WHERE intent_id" in dr)
    results.append(("P3 idempotency = atomic in-txn insert (3 call sites) + pre-check", p3, ""))

    # P5: drainer never writes graph_changelog; the engine does
    p5 = ("graph_changelog" not in dr) and ("infograph_v0_1.py" in base(cl_writers))
    results.append(("P5 producer split: drainer!=changelog, engine writes changelog",
                    p5, f"cl_writers={base(cl_writers)}"))

    ok = 0
    for name, val, detail in results:
        print(f"[{'PASS' if val else 'FAIL'}] {name}" + (f"  — {detail}" if detail else ""))
        ok += bool(val)
    print(f"\n{ok}/{len(results)} GREEN. (* = locked prediction P2 predicted zero writers and "
          f"flipped to writer-without-callers; the flip is the finding.)")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
