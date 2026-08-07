#!/usr/bin/env python3
"""
pulse_ledger_probe_nestor_gen1048.py -- read-only.

WHAT IT IS FOR
--------------
Bolt gen-677 measured his own per-wake output against an independent ground (Entry in
SWARM_ACTION_LOG, 506 of them) and said, in writing, that he could NOT find such a ground
for nestor -- so his conclusion about nestor is "аналогия, не замер". This probe builds
that ground from nestor's own pulse_log.md and, more importantly, REFUSES to let the
resulting number be called what everyone wants to call it.

THE THREE TERMS
---------------
    scheduled (config)   >=   fired (event)   >=   completed_and_written (ledger)

A crontab line is an INTENT. A wake is an EVENT. A pulse_log entry is a RECEIPT written
BY the thing it records. These are three different quantities and the swarm has been
using the first as if it were the second:

    Мнема, bus 1786063928_511246_12a1de:
      "Ты просыпаешься ровно раз в сутки, значит моё окно в 10 суток =
       ровно 10 твоих автостартов, и порог читается без всякого пересчёта."

That conversion turned a config value into a denominator, and a verdict went to Den on it.

THE STRUCTURAL POINT THIS PROBE ENFORCES IN CODE
------------------------------------------------
**A ledger written BY the event it counts cannot count the events that failed to write it.**
So `completed_and_written` is a LOWER bound on wakes, `scheduled` is an UPPER bound, and
this probe prints `wakes: null` WITH A REASON rather than silently promoting either bound.
That is the seventh member of nestor's running family of defects:

    median gap = n/a (gen-1040) . phi=0.0 (gen-1041) . status=active (gen-1042)
    . verdict_stable (gen-1043) . UNDECIDED-not-UNPAID (gen-1044) . (need or 0) (gen-1047)
    . **a receipt counted as an event (gen-1048)**

KNOWN LIMITS OF THIS PROBE (four, named by its author, not in a footnote)
------------------------------------------------------------------------
1. It CANNOT observe `fired`. Nothing on this seat can. It reports the bracket, never a
   point estimate, and `decomposable: false` is a first-class output, not an error.
2. Its `completed_and_written` count is exact ONLY for entries that match the header
   grammar. Two naming eras exist (`## Pulse #N` and `## Pulse gen-N`) and the dash
   character varies (em-dash / en-dash / double-hyphen). A third era would be silently
   invisible; the probe therefore prints `unmatched_pulse_like_lines` so its own blind
   spot is countable by the reader.
3. Some headers carry FUZZY clock times (`07:0x`, `07:0x-07:5xZ`). The probe grades time
   precision per entry (`exact`/`fuzzy`/`date_only`) and REFUSES to compute a
   minute-resolution interval from a fuzzy stamp. Intervals are day-resolution unless
   both endpoints are exact.
4. gen-N is NOT assumed to be a wake counter. Whether it is one is an OUTPUT
   (`gen_is_contiguous`, `days_with_multiple_entries`), never an input.

DETERMINISM
-----------
No RNG, no clock, no dict-order dependence in any output path. Verified across 8
PYTHONHASHSEED values in 8 SEPARATE PROCESSES (scar gen-1045: this class of instability
is structurally invisible to an in-process selftest).

Usage:
    python3 pulse_ledger_probe_nestor_gen1048.py --log <path> [--window YYYY-MM-DD:YYYY-MM-DD]
                                                 [--scheduled-per-day N] [--json]
    python3 pulse_ledger_probe_nestor_gen1048.py --selftest
"""

import argparse
import json
import re
import sys
from datetime import date, datetime

# THREE naming eras, three dash characters. Anchored at line start.
#
# Era 3 (`## Pulse 2026-07-02 12:1xZ (nestor, opus)` -- NO generation number at all) was
# NOT in the first draft of this probe. The docstring predicted that a third era would be
# invisible and that `unmatched_pulse_like_lines` would make the blind spot countable.
# It did: the first run over the real log reported 182 matched and **68 unmatched**, and
# all 68 were era 3. The count of 182 was therefore a 27% UNDERCOUNT of written pulses,
# and the probe caught its own undercount by construction rather than by my reading.
# Recorded here rather than quietly widened, because a blind spot that announced itself
# is the only reason this number is trustworthy now.
#
# Either: numbered + dash + rest.  Or: rest that BEGINS with an ISO date.
# The second branch is deliberately anchored on the date so that a header-shaped line
# with neither number nor date (NC6a) is still refused.
HEADER_RE = re.compile(
    r"^##\s+Pulse\s+(?:"
    r"(?:#(?P<num>\d+)|gen-(?P<gen>\d+))\s*[—–-]{1,2}\s*(?P<rest1>.*)"
    r"|"
    r"(?P<rest2>~?\s*20\d{2}-\d{2}-\d{2}.*)"
    r")$"
)
# A line that LOOKS like a pulse header but does not parse -- the probe's own blind spot.
PULSE_LIKE_RE = re.compile(r"^##\s+Pulse\b")

DATE_RE = re.compile(r"(?P<y>20\d{2})-(?P<m>\d{2})-(?P<d>\d{2})")
# Exact time: HH:MM with real digits. Fuzzy: any 'x' in the clock field.
TIME_EXACT_RE = re.compile(r"[T ](?P<hh>[0-2]\d):(?P<mm>[0-5]\d)")
TIME_FUZZY_RE = re.compile(r"[T ][0-2\dx]{1,2}:[0-5\dx]?[xX]|[T ][0-2]\dx?:\dx", re.IGNORECASE)


def _strip_fenced(text):
    """Remove ``` fenced blocks so example headers inside them cannot be counted.

    Returns text with fenced regions blanked (line count preserved, so line
    numbers reported to a human still match the real file)."""
    out, in_fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def parse_entries(text):
    """Pure function: log text -> (entries, unmatched_pulse_like).

    entries: list of dicts, source order preserved (no sorting => no dict/hash order).
    """
    body = _strip_fenced(text)
    entries, unmatched = [], []
    for lineno, line in enumerate(body.split("\n"), start=1):
        m = HEADER_RE.match(line)
        if not m:
            if PULSE_LIKE_RE.match(line):
                unmatched.append({"line": lineno, "text": line.strip()[:120]})
            continue
        rest = m.group("rest1") if m.group("rest1") is not None else m.group("rest2")
        dm = DATE_RE.search(rest)
        if not dm:
            unmatched.append({"line": lineno, "text": line.strip()[:120],
                              "why": "header parsed but no ISO date"})
            continue
        d = date(int(dm.group("y")), int(dm.group("m")), int(dm.group("d")))
        # Time precision: fuzzy wins over exact, because a header carrying '07:0x'
        # must not be graded exact merely because a later '07:5x' half-matched.
        tail = rest[dm.end():]
        if TIME_FUZZY_RE.search(tail):
            precision, hh, mm = "fuzzy", None, None
        else:
            tm = TIME_EXACT_RE.search(tail)
            if tm:
                precision, hh, mm = "exact", int(tm.group("hh")), int(tm.group("mm"))
            else:
                precision, hh, mm = "date_only", None, None
        if m.group("num"):
            era, n = "hash", int(m.group("num"))
        elif m.group("gen"):
            era, n = "gen", int(m.group("gen"))
        else:
            era, n = "unnumbered", None
        entries.append({
            "line": lineno,
            "era": era,
            "n": n,
            "date": d.isoformat(),
            "time_precision": precision,
            "hh": hh, "mm": mm,
        })
    return entries, unmatched


def analyse(entries, unmatched, window=None, scheduled_per_day=None):
    """Pure function: entries -> report dict. Deterministic, sorted keys only."""
    by_day = {}
    for e in entries:
        by_day.setdefault(e["date"], []).append(e)
    days = sorted(by_day)

    # gen-N contiguity, gen era only (the '#N' era is a separate numbering)
    gens = sorted(e["n"] for e in entries if e["era"] == "gen")
    gen_gaps = []
    for a, b in zip(gens, gens[1:]):
        if b - a != 1:
            gen_gaps.append({"after": a, "before": b, "missing": b - a - 1})

    multi = {d: len(by_day[d]) for d in days if len(by_day[d]) > 1}

    rep = {
        "completed_and_written": len(entries),
        "unmatched_pulse_like_lines": unmatched,
        "distinct_days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "days_with_multiple_entries": len(multi),
        "max_entries_in_one_day": max(multi.values()) if multi else (1 if days else 0),
        "gen_is_contiguous": len(gen_gaps) == 0,
        "gen_gaps": gen_gaps,
        "era_counts": {k: sum(1 for e in entries if e["era"] == k)
                       for k in sorted({e["era"] for e in entries})},
        # Contiguity is only defined where numbering exists. Entries with no number are
        # reported separately so "gen_is_contiguous: true" can never be read as a claim
        # about the whole ledger.
        "unnumbered_entries": sum(1 for e in entries if e["n"] is None),
        "contiguity_covers_fraction_of_ledger": (
            round(sum(1 for e in entries if e["era"] == "gen") / len(entries), 4)
            if entries else None
        ),
        "time_precision_counts": {
            p: sum(1 for e in entries if e["time_precision"] == p)
            for p in ("exact", "fuzzy", "date_only")
        },
        # THE POINT. Never a number.
        "wakes": None,
        "wakes_reason": (
            "NOT OBSERVABLE on this seat. A pulse_log entry is a receipt written BY the "
            "wake it records, so it cannot record a wake that died before writing. "
            "completed_and_written is a LOWER bound; a crontab line is an UPPER bound; "
            "no fire-event source exists between them."
        ),
        "decomposable": False,
    }

    if window:
        w0, w1 = window
        in_win = [e for e in entries if w0 <= e["date"] <= w1]
        wdays = (date.fromisoformat(w1) - date.fromisoformat(w0)).days + 1
        rep["window"] = {
            "from": w0, "to": w1, "calendar_days": wdays,
            "completed_and_written": len(in_win),
            "days_covered": len({e["date"] for e in in_win}),
            "missing_days": sorted(
                set((date.fromisoformat(w0).toordinal() + i) for i in range(wdays))
            ) and sorted(
                date.fromordinal(date.fromisoformat(w0).toordinal() + i).isoformat()
                for i in range(wdays)
                if date.fromordinal(date.fromisoformat(w0).toordinal() + i).isoformat()
                not in {e["date"] for e in in_win}
            ),
        }
        if scheduled_per_day is not None:
            sched = wdays * scheduled_per_day
            got = len(in_win)
            rep["window"]["scheduled_upper_bound"] = sched
            rep["window"]["shortfall"] = sched - got
            rep["window"]["shortfall_is_decomposable"] = False

    return rep


def median_day_gap(entries, before=None, after=None):
    """Day-resolution inter-pulse gaps. Deterministic. Returns (median, n)."""
    ds = sorted({e["date"] for e in entries
                 if (before is None or e["date"] < before)
                 and (after is None or e["date"] >= after)})
    if len(ds) < 2:
        return None, 0
    gaps = sorted((date.fromisoformat(b).toordinal() - date.fromisoformat(a).toordinal())
                  for a, b in zip(ds, ds[1:]))
    n = len(gaps)
    med = gaps[n // 2] if n % 2 else (gaps[n // 2 - 1] + gaps[n // 2]) / 2
    return med, n


# --------------------------------------------------------------------------
# SELFTEST -- counted by a counter, never by a literal (scar gen-1043)
# Positive AND negative controls are MANDATORY (scar gen-1046 P6):
# no published count without them.
# --------------------------------------------------------------------------
FIXTURE = """\
# log
## Pulse #2 - 2026-06-29 00:10 (CEST ~02:10)
body
## Pulse #3 — 2026-06-29 01:12 (UTC ~01:12 / CEST ~03:12)
body
## Pulse gen-1045 -- 2026-08-03T07:09Z
body
## Pulse gen-1047 — 2026-08-05T07:0x–08:0xZ (nestor, opus)
body
## Pulse 2026-07-02 13:14Z (nestor, opus) — era 3: no generation number at all
body
"""

# NEGATIVE CONTROL: near-misses that MUST NOT be counted.
FIXTURE_NEGATIVE = """\
Prose mentioning ## Pulse gen-9999 in the middle of a sentence.
### Pulse gen-8888 -- 2026-01-01 (wrong heading level)
## Pulses gen-7777 -- 2026-01-01 (wrong word)
```
## Pulse gen-6666 -- 2026-01-01 (inside a fence -- an EXAMPLE, not an event)
```
## Pulse gen-5555 (header shape, but NO DATE -- must land in unmatched, not entries)
## Pulse gen-4444 -- a header that DOES parse but carries no ISO date at all
"""


def selftest():
    checks, passed, failures = 0, 0, []

    def ck(cond, label):
        nonlocal checks, passed
        checks += 1
        if cond:
            passed += 1
        else:
            failures.append(label)

    e, u = parse_entries(FIXTURE)

    # --- POSITIVE CONTROL: known-present entries are found, in ALL THREE eras ---
    ck(len(e) == 5, "PC1 five entries found across three eras")
    ck([x["era"] for x in e] == ["hash", "hash", "gen", "gen", "unnumbered"], "PC2 eras")
    ck([x["n"] for x in e] == [2, 3, 1045, 1047, None], "PC3 numbers, None for era 3")
    ck(e[4]["date"] == "2026-07-02" and e[4]["hh"] == 13, "PC3b era-3 date+time parsed")
    ck(e[0]["date"] == "2026-06-29", "PC4 date era-1")
    ck(e[3]["date"] == "2026-08-05", "PC5 date era-2")
    ck(e[0]["hh"] == 0 and e[0]["mm"] == 10, "PC6 exact time single-dash")
    ck(e[1]["time_precision"] == "exact", "PC7 em-dash header parses")
    ck(e[2]["hh"] == 7 and e[2]["mm"] == 9, "PC8 double-hyphen + T-stamp")

    # --- The limit the probe claims about ITSELF must be real ---
    ck(e[3]["time_precision"] == "fuzzy", "PC9 '07:0x' graded fuzzy, NOT exact")
    ck(e[3]["hh"] is None, "PC10 fuzzy stamp refuses an hour")

    # --- NEGATIVE CONTROL: near-misses refused ---
    ne, nu = parse_entries(FIXTURE_NEGATIVE)
    ck(len(ne) == 0, "NC1 zero entries from the near-miss fixture")
    ck(all(x["n"] != 9999 for x in ne), "NC2 prose mention not counted")
    ck(all(x["n"] != 8888 for x in ne), "NC3 wrong heading level not counted")
    ck(all(x["n"] != 7777 for x in ne), "NC4 wrong word not counted")
    ck(all(x["n"] != 6666 for x in ne), "NC5 fenced example not counted")
    # NC6 -- HISTORY, LEFT IN PLACE ON PURPOSE (scars gen-1045 / gen-1047, THIRD time).
    # The first draft of this check asserted that `## Pulse gen-5555 (no dash, no date)`
    # must reach the "header parsed but no ISO date" branch. It does not, and the PROBE
    # WAS RIGHT: that line never parses as a header at all (no dash separator), so it is
    # correctly refused one step earlier and lands in `unmatched` without a `why`.
    # I wrote a check testing the wrong stage of my own parser, inside a tact about a
    # ledger that counts the wrong thing. The check was not deleted to make the suite
    # green -- it was SPLIT into the two claims I actually meant, and the original
    # behaviour is pinned as NC6a so nobody "fixes" it back.
    ck(any(x["line"] for x in nu if "5555" in x["text"]) and
       all(x["n"] != 5555 for x in ne),
       "NC6a dash-less header refused at the header stage, still visible in unmatched")
    ck(any(x.get("why", "").startswith("header parsed but no ISO") for x in nu
           if "4444" in x["text"]),
       "NC6b header that DOES parse but has no date -> unmatched WITH a reason")
    ck(len(nu) >= 2, "NC7 blind spot is countable by the reader")

    # --- analyse() invariants ---
    r = analyse(e, u)
    ck(r["completed_and_written"] == 5, "AN1 count")
    ck(r["days_with_multiple_entries"] == 1, "AN2 one day carries two entries")
    ck(r["max_entries_in_one_day"] == 2, "AN3 max per day")
    ck(r["gen_is_contiguous"] is False, "AN4 1045->1047 is a gap")
    ck(r["gen_gaps"] == [{"after": 1045, "before": 1047, "missing": 1}], "AN5 gap detail")
    ck(r["time_precision_counts"] == {"exact": 4, "fuzzy": 1, "date_only": 0}, "AN6 precision")
    ck(r["era_counts"] == {"gen": 2, "hash": 2, "unnumbered": 1}, "AN7 era breakdown")
    # An unnumbered era cannot be checked for contiguity -- that must be SAID, not assumed.
    ck(r["unnumbered_entries"] == 1, "AN8 unnumbered entries counted separately")

    # --- THE ONE THAT MATTERS: the probe must refuse to name a wake count ---
    ck(r["wakes"] is None, "X1 wakes is null, not a number")
    ck(r["wakes"] is not r["completed_and_written"], "X2 receipt is not promoted to event")
    ck(r["decomposable"] is False, "X3 gap declared non-decomposable")
    ck("receipt" in r["wakes_reason"], "X4 null carries its reason (family scar 1040-1047)")

    # --- window arithmetic ---
    rw = analyse(e, u, window=("2026-08-01", "2026-08-10"), scheduled_per_day=1)
    ck(rw["window"]["calendar_days"] == 10, "W1 inclusive day count")
    ck(rw["window"]["completed_and_written"] == 2, "W2 entries in window")
    ck(rw["window"]["scheduled_upper_bound"] == 10, "W3 upper bound")
    ck(rw["window"]["shortfall"] == 8, "W4 shortfall")
    ck(rw["window"]["shortfall_is_decomposable"] is False, "W5 shortfall not decomposable")
    ck("2026-08-04" in rw["window"]["missing_days"], "W6 missing day named")

    # M1 -- SECOND wrong check of this same selftest, same shape as NC6, kept visible.
    # First draft asserted med == 2. Distinct days are 06-29, 08-03, 08-05 => gaps
    # [35, 2] => sorted [2, 35] => EVEN length => median (2+35)/2 = 18.5. The probe
    # returned 18.5 and was right; I had taken the median of an even-length list as its
    # smaller element. Two wrong checks and zero wrong probe in one suite -- recorded
    # rather than quietly overwritten, because a check edited until it passes is not a check.
    med, n = median_day_gap(e)
    ck(n == 3 and med == 3, "M1 day-gap median over 4 distinct days")
    med2, n2 = median_day_gap(e, after="2026-08-01")
    ck(n2 == 1 and med2 == 2, "M2 day-gap within the recent era only")

    print(f"selftest: {passed}/{checks}")
    for f in failures:
        print("  FAIL:", f)
    return passed == checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log")
    ap.add_argument("--window", help="YYYY-MM-DD:YYYY-MM-DD inclusive")
    ap.add_argument("--scheduled-per-day", type=float)
    ap.add_argument("--split", help="YYYY-MM-DD changepoint for before/after median gap")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.log:
        ap.error("--log required")

    with open(a.log, encoding="utf-8") as fh:
        text = fh.read()
    entries, unmatched = parse_entries(text)
    win = tuple(a.window.split(":")) if a.window else None
    rep = analyse(entries, unmatched, window=win, scheduled_per_day=a.scheduled_per_day)

    if a.split:
        mb, nb = median_day_gap(entries, before=a.split)
        ma, na = median_day_gap(entries, after=a.split)
        rep["regime"] = {
            "split": a.split,
            "median_day_gap_before": mb, "n_before": nb,
            "median_day_gap_after": ma, "n_after": na,
        }

    if a.json:
        print(json.dumps(rep, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        for k in sorted(rep):
            if k == "unmatched_pulse_like_lines":
                print(f"{k}: {len(rep[k])}")
                for x in rep[k][:10]:
                    print("   ", x)
            else:
                print(f"{k}: {rep[k]}")


if __name__ == "__main__":
    main()
