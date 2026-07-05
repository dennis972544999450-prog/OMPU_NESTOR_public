#!/usr/bin/env python3
"""
log_shard.py -- read-only, non-destructive sharding + index for SWARM_ACTION_LOG.md

§4.3.1 fire (monolith ~10k+ lines and growing). Built to honour П1 of the
SPINE-v1 proposal: "ЛОГ НЕПРИКОСНОВЕНЕН (append-only; sharding = ADD files,
never delete/rewrite/compact)".

Therefore this tool NEVER touches SWARM_ACTION_LOG.md. It DERIVES:
  - log_shards/shard_NNN_entries_AAA-BBB.md   (regenerable read views)
  - log_shards/INDEX.md                       (Entry N -> title / line / shard)
Everything under log_shards/ is disposable and regenerable from the monolith,
which stays the single source of truth and the single append target. Cutover
(if the swarm ever votes to move the append target) is a SEPARATE decision;
this tool only makes the monolith fast to navigate today.

Also carries a canary in the spirit of gen-159's log_canary.py: it reports
gaps and duplicate entry-headers, the ARCHIVIST_BLINDNESS failure class
(a parser that prints "ok" while silently missing headers).

Usage:
  python3 log_shard.py                 # shard the real log next to this tools/ dir
  python3 log_shard.py --dry-run       # parse + report, write nothing
  python3 log_shard.py --test          # self-test on a synthetic log, no disk writes
  python3 log_shard.py --log PATH --out DIR --size 25
"""
import argparse
import os
import re
import sys
from datetime import datetime, timezone

# A true entry header starts a line with 2-3 '#', then "Entry", then a number.
# This deliberately EXCLUDES headings where "Entry" appears mid-title
# (e.g. "### Что сделал (Entry 143)") -- those are the false positives that
# make a naive `grep 'Entry [0-9]'` overcount (160 vs 143 real entries).
ENTRY_RE = re.compile(r"^(#{2,3})\s+Entry\s+#?(\d+)\b(.*)$")

DEFAULT_SIZE = 25


def parse_entries(lines):
    """Return (entries, dups, warnings).
    entries: list of dicts {num, line, title, first_seen} in source order,
             first occurrence per number wins (canonical).
    dups:    {num: [line, ...]} for numbers whose header appears >1 time.
    """
    seen = {}
    order = []
    dups = {}
    for i, ln in enumerate(lines, start=1):
        m = ENTRY_RE.match(ln)
        if not m:
            continue
        num = int(m.group(2))
        title = ln.rstrip("\n")
        if num in seen:
            dups.setdefault(num, [seen[num]["line"]]).append(i)
            continue
        rec = {"num": num, "line": i, "title": title}
        seen[num] = rec
        order.append(rec)
    warnings = []
    if order:
        nums = sorted(r["num"] for r in order)
        lo, hi = nums[0], nums[-1]
        present = set(nums)
        gaps = [n for n in range(lo, hi + 1) if n not in present]
        if gaps:
            warnings.append("GAPS in entry numbers: " + ", ".join(map(str, gaps)))
        if dups:
            warnings.append("DUPLICATE entry headers: " + ", ".join(
                f"#{n}(x{len(v)})" for n, v in sorted(dups.items())))
    return order, dups, warnings


def shard_ranges(entries, size):
    """Deterministic fixed-width buckets by entry number: [1..size], etc.
    Robust to gaps -- bucket membership depends on the number, not position."""
    if not entries:
        return []
    hi = max(e["num"] for e in entries)
    buckets = {}
    for e in entries:
        b = (e["num"] - 1) // size  # 0-based bucket index
        buckets.setdefault(b, []).append(e)
    out = []
    for b in sorted(buckets):
        lo_n = b * size + 1
        hi_n = (b + 1) * size
        out.append((lo_n, hi_n, buckets[b]))
    return out


def slice_source(lines, start_line, end_line_exclusive):
    return lines[start_line - 1:end_line_exclusive - 1]


def build_shards(lines, entries, size):
    """Yield (fname, lo, hi, member_entries, body_lines)."""
    ranges = shard_ranges(entries, size)
    # map each canonical entry to the source line where the NEXT canonical
    # entry (any bucket) starts, so bodies don't get clipped at bucket edges.
    all_sorted = sorted(entries, key=lambda e: e["line"])
    next_line = {}
    for idx, e in enumerate(all_sorted):
        nxt = all_sorted[idx + 1]["line"] if idx + 1 < len(all_sorted) else len(lines) + 1
        next_line[e["num"]] = nxt
    for lo, hi, members in ranges:
        members = sorted(members, key=lambda e: e["num"])
        body = []
        for e in members:
            body.extend(slice_source(lines, e["line"], next_line[e["num"]]))
        fname = f"shard_{lo:03d}_entries_{lo:03d}-{hi:03d}.md"
        yield fname, lo, hi, members, body


def render_banner(lo, hi, src_name):
    return (
        f"<!-- DERIVED / READ-ONLY — regenerate with tools/log_shard.py -->\n"
        f"<!-- Source of truth: {src_name} (append-only, П1). Do NOT edit this shard. -->\n"
        f"# {src_name} — shard: Entry {lo:03d}–{hi:03d}\n\n"
    )


def render_index(entries, dups, warnings, shards_meta, src_name, size):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    out.append(f"<!-- DERIVED / READ-ONLY — regenerate with tools/log_shard.py -->\n")
    out.append(f"# INDEX — {src_name}\n\n")
    out.append(f"Generated: {now} · shard size: {size} entries · "
               f"{len(entries)} entries · {len(shards_meta)} shards\n\n")
    if warnings:
        out.append("## ⚠ CANARY\n\n")
        for w in warnings:
            out.append(f"- {w}\n")
        out.append("\n")
    else:
        out.append("## CANARY: clean (no gaps, no duplicate headers)\n\n")
    out.append("## Shards\n\n")
    for fname, lo, hi, members in shards_meta:
        nums = ", ".join(str(e["num"]) for e in members)
        out.append(f"- `{fname}` — Entry {lo:03d}–{hi:03d} ({len(members)} present: {nums})\n")
    out.append("\n## Entries\n\n")
    out.append("| Entry | Src line | Title |\n|---:|---:|---|\n")
    for e in sorted(entries, key=lambda e: e["num"]):
        # strip leading #'s for readability
        t = re.sub(r"^#+\s+", "", e["title"]).replace("|", "\\|")
        out.append(f"| {e['num']} | {e['line']} | {t} |\n")
    return "".join(out)


def run(log_path, out_dir, size, dry_run):
    if not os.path.isfile(log_path):
        print(f"ERROR: log not found: {log_path}", file=sys.stderr)
        return 2
    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()
    entries, dups, warnings = parse_entries(lines)
    print(f"parsed {len(entries)} canonical entries from {len(lines)} lines")
    if entries:
        print(f"range: Entry {min(e['num'] for e in entries)}"
              f"..{max(e['num'] for e in entries)}")
    for w in warnings:
        print("  canary:", w)
    shards = list(build_shards(lines, entries, size))
    shards_meta = [(fn, lo, hi, mem) for (fn, lo, hi, mem, _body) in shards]
    src_name = os.path.basename(log_path)
    if dry_run:
        print(f"[dry-run] would write {len(shards)} shards + INDEX.md to {out_dir}")
        return 0
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for fname, lo, hi, members, body in shards:
        with open(os.path.join(out_dir, fname), "w", encoding="utf-8") as f:
            f.write(render_banner(lo, hi, src_name))
            f.write("".join(body))
            if body and not body[-1].endswith("\n"):
                f.write("\n")
        written += 1
    with open(os.path.join(out_dir, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write(render_index(entries, dups, warnings, shards_meta, src_name, size))
    print(f"wrote {written} shards + INDEX.md to {out_dir}")
    # П1 guardrail: assert we never touched the source
    return 0


# ---------------------------------------------------------------------------
SELFTEST_LOG = """\
# SWARM ACTION LOG

## Entry 001 -- genesis
body one
more body

## Entry 002 | second | 2026-01-01
body two

### Что сделал (Entry 002) -- this is a SUBSECTION, must NOT be counted
noise

## Entry 003 — third with em-dash
body three

## Entry 005 | fifth (gap: 004 missing on purpose)
body five

## Entry 005 | DUPLICATE header on purpose
duplicate body
"""


def selftest():
    lines = SELFTEST_LOG.splitlines(keepends=True)
    entries, dups, warnings = parse_entries(lines)
    nums = [e["num"] for e in entries]
    checks = []
    checks.append(("canonical set == {1,2,3,5}", sorted(nums) == [1, 2, 3, 5]))
    checks.append(("subsection '(Entry 002)' NOT counted", nums.count(2) == 1))
    checks.append(("duplicate #5 detected", 5 in dups and len(dups[5]) == 2))
    checks.append(("gap 004 flagged", any("004" in w or " 4" in w for w in warnings)))
    checks.append(("dup flagged in warnings", any("DUPLICATE" in w for w in warnings)))
    # bucketing: size 2 -> [1-2],[3-4],[5-6]
    ranges = shard_ranges(entries, 2)
    checks.append(("3 buckets at size=2", len(ranges) == 3))
    checks.append(("bucket1 has entries 1,2", sorted(e["num"] for e in ranges[0][2]) == [1, 2]))
    checks.append(("bucket3 has entry 5 only", [e["num"] for e in ranges[2][2]] == [5]))
    # body slicing: entry 1 body must include its two body lines, stop before Entry 002
    shards = list(build_shards(lines, entries, 100))
    body_all = "".join(shards[0][4])
    checks.append(("entry1 body captured", "body one" in body_all and "more body" in body_all))
    checks.append(("entry1 body stops before entry2", body_all.count("body two") == 1))
    ok = sum(1 for _, c in checks if c)
    for name, c in checks:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}")
    print(f"self-test: {ok}/{len(checks)} PASS")
    return 0 if ok == len(checks) else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    default_log = os.path.normpath(os.path.join(here, "..", "SWARM_ACTION_LOG.md"))
    default_out = os.path.normpath(os.path.join(here, "..", "log_shards"))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=default_log)
    ap.add_argument("--out", default=default_out)
    ap.add_argument("--size", type=int, default=DEFAULT_SIZE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()
    if args.test:
        sys.exit(selftest())
    sys.exit(run(args.log, args.out, args.size, args.dry_run))


if __name__ == "__main__":
    main()
