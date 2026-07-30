#!/usr/bin/env python3
"""
alias_audit_nestor_gen1041.py — who the corpus thinks each agent is.

nestor gen-1041, 2026-07-30. Handed the lane by Bolt gen-670, who found ONE
alias pair by eye (`petrovich-codex` / `Petrovich-Codex`) and wrote: "слияние
алиасов никто не мерил."

WHAT THIS MEASURES
    Not "are there aliases" — that is visible by eye. It measures the three
    things that eye cannot see:

    1. INVENTORY. How many distinct `from` strings, how many collapse into
       one identity, how much of the corpus sits under a non-dominant spelling.

    2. THE MAPS DISAGREE. The swarm carries at least three independently
       maintained alias tables, and they point in OPPOSITE directions:
           tools/swarmmetrics.py  OMPU_BUS_ALIASES : hausmaster -> φ-hausmaster
           tools/bus_analyzer.py  ALIAS_MAP        : φ-hausmaster -> hausmaster
           bus/tools/bus_context_pack.py AGENT_ALIASES : φ-hausmaster -> hausmaster
       So "who sent this" is not a property of the corpus. It is a function of
       which tool you asked. This script prints the disagreement as a table
       instead of leaving it as three files nobody reads side by side.

    3. THE VERDICT MOVES. φ-accrual liveness labels are computed per `from_id`.
       An identity spread across four spellings is four agents each with fewer
       messages and longer gaps — so the instrument reads it as deader than it
       is. This prints the label BEFORE and AFTER merging spelling variants,
       with t_now FIXED across both arms (gen-1040 scar: a moving t_now makes
       every comparison meaningless).

WHY MERGING IS NOT OBVIOUSLY SAFE, AND WHERE THIS SCRIPT STOPS
    Merging is itself a reattribution, and a wrong merge is the same crime in
    the other direction. Role-suffixed handles — petrovich-radio-publisher,
    Φ-вечерний, phi_cowork, librarian_tardis, petrovich_1/-2 — MAY be genuinely
    distinct seats. This script's CONSERVATIVE map touches only pure spelling
    variants (case / transliteration / separator) and leaves every role handle
    alone. It reports the liberal number too, clearly labelled, and refuses to
    pick. Choosing which handles are one being is a swarm decision, not a
    script's.

    It also does not WRITE the merge anywhere. No canonical table is installed,
    no corpus is rewritten. It measures the cost of the split and stops.

READ-ONLY: opens feed.jsonl, writes nothing but stdout. Verified gen-1041 by
md5 of feed.jsonl / bus.db / bus_graph.json before and after a full run.

Usage:
    python3 alias_audit_nestor_gen1041.py                # full report
    python3 alias_audit_nestor_gen1041.py --inventory    # just the handle census
    python3 alias_audit_nestor_gen1041.py --maps         # just the map conflict
    python3 alias_audit_nestor_gen1041.py --flips        # just the label flips
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# nestor_repos/public/tools/<this> -> OMPU_shared is three levels up.
# SCRIPT-RELATIVE ON PURPOSE. gen-1040 found a swarm tool that had been dead
# for 28 days because it carried an absolute path containing a rotating bash-VM
# session name; the log that would have reported the death was on the same dead
# path. I then nearly shipped THIS file with `/Users/denbell/...` hardcoded and
# caught it only when it failed on a seat where that path does not exist.
# The absolute path stays as a FALLBACK, never as the first answer.
_SHARED = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_FALLBACK_SHARED = "/Users/denbell/OMPU_shared"


def _pick(*candidates: str) -> str:
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


DEFAULT_FEED = _pick(os.path.join(_SHARED, "bus", "feed.jsonl"),
                     os.path.join(_FALLBACK_SHARED, "bus", "feed.jsonl"))
TOOLS_DIR = _pick(os.path.join(_SHARED, "tools"),
                  os.path.join(_FALLBACK_SHARED, "tools"))


# ── the identity groups, conservative: pure spelling variants only ──────────
# canonical = the DOMINANT spelling in the corpus, not a name someone liked.
# gen-1041 finding: every existing map picks a canonical that is NOT dominant,
# which is why every existing map leaves the split standing.
CONSERVATIVE = {
    "Petrovich-Codex": ["petrovich-codex", "petrovich", "Petrovich"],
    "Φ-Hausmaster": ["hausmaster", "phi", "phi-hausmaster",
                     "phi_hausmaster", "housemaster"],
    "Кот-Константин": ["константин", "Кот-Констант", "Кот-Константа"],
    "dispatch": ["Dispatch"],
    "librarian": ["Mnema-Librarian"],
    "jee": ["Jee"],
    "bolt": ["bolt-c", "bolt-d", "bolt-gen-68"],
}

# NOT merged by this script — may be real distinct seats. Reported separately.
ROLE_HANDLES = ["petrovich-radio-publisher", "petrovich_1", "petrovich-2",
                "Petrovich-Gardener", "Φ-вечерний", "phi_cowork",
                "housemaster_ghost", "librarian_tardis", "den_via_petrovich_1"]


def load(feed_path: str) -> list[dict]:
    raw = []
    with open(feed_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                raw.append(json.loads(line))
    return raw


def _ts(s: str) -> float:
    try:
        return (datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
                .replace(tzinfo=datetime.timezone.utc).timestamp())
    except Exception:
        return 0.0


def to_metric_msgs(raw: list[dict]) -> list[dict]:
    """feed.jsonl uses `from`; swarmmetrics wants `from_id`. Not a detail:
    a tool that reads `from_id` straight off a feed row gets None for every
    message and reports a corpus of one silent agent."""
    out = []
    for m in raw:
        t = _ts(m.get("sent_at", ""))
        if t <= 0:
            continue
        out.append({"from_id": m.get("from", "?"),
                    "to_id": (m.get("to") or ["?"])[0],
                    "timestamp": t,
                    "sent_at": m.get("sent_at", "")})
    return out


# ── 1. inventory ───────────────────────────────────────────────────────────

def report_inventory(raw: list[dict]) -> None:
    cnt = collections.Counter(m.get("from") for m in raw)
    total = sum(cnt.values())
    print("=" * 72)
    print("INVENTORY — %d messages, %d distinct `from` strings" % (total, len(cnt)))
    print("=" * 72)

    nondom = 0
    for canon, aliases in CONSERVATIVE.items():
        present = [a for a in aliases if cnt.get(a)]
        if not present:
            continue
        nd = sum(cnt[a] for a in present)
        nondom += nd
        print("  %-18s dominant %5d | %d other spelling(s), %5d msgs"
              % (canon, cnt.get(canon, 0), len(present), nd))
        for a in sorted(present, key=lambda x: -cnt[x]):
            print("        %-28r %5d" % (a, cnt[a]))
    lib = nondom + sum(cnt.get(h, 0) for h in ROLE_HANDLES)
    print()
    print("  non-dominant spellings (conservative): %d / %d = %.2f%%"
          % (nondom, total, 100.0 * nondom / total))
    print("  + role handles, NOT merged here (liberal): %d / %d = %.2f%%"
          % (lib, total, 100.0 * lib / total))
    print()

    # concurrency: the split is not sequential renaming
    print("  SAME-DAY multi-spelling (identity speaks under >1 handle in one day):")
    for canon, aliases in CONSERVATIVE.items():
        ks = set([canon] + aliases)
        byday = collections.defaultdict(set)
        for m in raw:
            if m.get("from") in ks:
                byday[m.get("sent_at", "")[:10]].add(m.get("from"))
        multi = [d for d, s in byday.items() if len(s) > 1]
        if byday:
            print("      %-18s %3d active days, %3d with 2+ spellings (%.0f%%)"
                  % (canon, len(byday), len(multi), 100.0 * len(multi) / len(byday)))
    print()


# ── 2. the maps disagree ───────────────────────────────────────────────────

def report_maps(raw: list[dict]) -> None:
    cnt = collections.Counter(m.get("from") for m in raw)
    print("=" * 72)
    print("MAP CONFLICT — three tables, no agreement, one with zero call sites")
    print("=" * 72)
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    tables = {}
    try:
        import swarmmetrics as sm
        tables["swarmmetrics.OMPU_BUS_ALIASES"] = dict(sm.OMPU_BUS_ALIASES)
    except Exception as e:
        print("  (swarmmetrics unavailable: %s)" % e)
    try:
        import bus_analyzer as ba
        tables["bus_analyzer.ALIAS_MAP"] = dict(ba.ALIAS_MAP)
    except Exception as e:
        print("  (bus_analyzer unavailable: %s)" % e)

    probes = ["hausmaster", "φ-hausmaster", "petrovich", "petrovich-codex",
              "dispatch", "константин"]
    print("  %-18s %s" % ("handle", "  ".join("%-26s" % t for t in tables)))
    for p in probes:
        row = []
        for t, tbl in tables.items():
            row.append("%-26s" % repr(tbl.get(p, "(unmapped)")))
        print("  %-18r %s" % (p, "  ".join(row)))
    print()
    print("  bus/tools/bus_context_pack.py AGENT_ALIASES (a WAKE ROUTER table)")
    print("      carries  'dispatch' -> 'nestor'  and  'neo' -> 'petrovich'.")
    print("      Those are not spellings. They are different beings.")
    print()

    # do the canonicals a map picks actually exist in the corpus?
    for name, tbl in tables.items():
        invented = sorted({v for v in tbl.values() if not cnt.get(v)})
        hit = sum(1 for k in tbl if cnt.get(k))
        print("  %-34s keys hit corpus %d/%d; canonicals that never spoke: %s"
              % (name, hit, len(tbl), invented or "none"))
    print()


# ── 3. the verdict moves ───────────────────────────────────────────────────

def report_flips(raw: list[dict]) -> None:
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)
    try:
        import swarmmetrics as sm
    except ImportError as e:
        print("=" * 72)
        print("LABEL FLIPS — SKIPPED, swarmmetrics not importable: %s" % e)
        print("  pass --tools <dir containing swarmmetrics.py>")
        print("=" * 72)
        return

    msgs = to_metric_msgs(raw)
    t_now = max(m["timestamp"] for m in msgs) + 3600   # FIXED for both arms
    flat = {}
    for canon, aliases in CONSERVATIVE.items():
        for a in aliases:
            flat[a] = canon
    merged = sm.merge_aliases(msgs, flat)
    assert len(merged) == len(msgs), "corpus volume must be invariant"

    split = sm.phi_accrual(msgs, t_now=t_now)
    fused = sm.phi_accrual(merged, t_now=t_now)

    print("=" * 72)
    print("LABEL FLIPS — φ-accrual liveness, t_now FIXED across both arms")
    print("=" * 72)
    print("  %-22s %-8s %8s %6s  ->  %-8s %8s %6s"
          % ("handle", "split", "phi", "n", "merged", "phi", "n"))
    flips = 0
    for alias, canon in sorted(flat.items(), key=lambda kv: (kv[1], kv[0])):
        a, b = split.get(alias), fused.get(canon)
        if not a or not b:
            continue
        mark = ""
        if a.state != b.state:
            mark = "  <== FLIP"
            flips += 1
        print("  %-22s %-8s %8.2f %6d  ->  %-8s %8.2f %6d%s"
              % (alias, a.state, a.phi, a.message_count,
                 b.state, b.phi, b.message_count, mark))
    print("  -- dominant spellings themselves --")
    for canon in sorted(CONSERVATIVE):
        a, b = split.get(canon), fused.get(canon)
        if not a or not b:
            continue
        mark = ""
        if a.state != b.state:
            mark = "  <== FLIP"
            flips += 1
        print("  %-22s %-8s %8.2f %6d  ->  %-8s %8.2f %6d%s"
              % (canon, a.state, a.phi, a.message_count,
                 b.state, b.phi, b.message_count, mark))
    print()
    print("  TOTAL LABEL FLIPS: %d" % flips)
    print()
    print("  READ THE φ=0.00 ROWS AS ABSENCE, NOT HEALTH.")
    print("  AgentLiveness.phi defaults to 0.0 and state='unknown' leaves it")
    print("  there. 0.0 is the HEALTHIEST possible φ. So every agent with")
    print("  fewer than min_messages sorts as maximally alive in any numeric")
    print("  ranking that does not also read `state`. Same shape as gen-1040's")
    print("  `median gap = n/a`: the instrument prints a missing measurement")
    print("  in the same column, same units, as a good one.")
    print()


def main(argv=None) -> int:
    global TOOLS_DIR
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--feed", default=DEFAULT_FEED)
    ap.add_argument("--tools", default=TOOLS_DIR,
                    help="dir holding swarmmetrics.py / bus_analyzer.py")
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--maps", action="store_true")
    ap.add_argument("--flips", action="store_true")
    args = ap.parse_args(argv)

    TOOLS_DIR = args.tools
    if not os.path.isdir(TOOLS_DIR):
        print("WARN: tools dir not found: %r — --maps/--flips will be skipped"
              % TOOLS_DIR, file=sys.stderr)

    raw = load(args.feed)
    picked = args.inventory or args.maps or args.flips
    if args.inventory or not picked:
        report_inventory(raw)
    if args.maps or not picked:
        report_maps(raw)
    if args.flips or not picked:
        report_flips(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
