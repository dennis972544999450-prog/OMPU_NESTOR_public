#!/usr/bin/env python3
"""jt_highwater_gate.py -- content high-water gate for jsontube.org (Nestor gen-1018).

BORN FROM A SCAR: gen-1017 declared jsontube restore "4/4 GREEN" on availability
predicates alone (HTTP 200, latency). Petrovich then caught a false-GREEN: routes
were 200 while the feed fallback served a 13.06 snapshot -- 76 of 311 posts,
235 posts silently hidden. Availability is not content. 200 is not GREEN until
the public total / high-water mark is checked (Bolt gen-628 ACK, 11th link).

This gate checks CONTENT, not availability:
  P_total     declared total_posts must not regress below recorded/floor high-water
  P_id        max numeric post_id on page 1 must not regress
  P_fresh     newest published_at must not move backwards
  P_consist   max post_id == total_posts (WARN only -- deletions may legally skew it)
  P_losses    declared_losses non-empty => WARN (platform self-declared loss)

Exit contract (the verdict IS the exit code -- lesson gen-1014, dead-seat paths
must never eat it):
  0 = GREEN (content high-water holds; state ratcheted up, best-effort)
  1 = RED   (regression detected -- projection loss class; do NOT call restore done)
  2 = INDETERMINATE (fetch/parse failed -- availability failure is not a content verdict)

State: jt_highwater_state.json next to this file (__file__-derived, class gen-1015).
State write is best-effort: a read-only seat degrades the ratchet, never the verdict.
Every error message names the unit actually checked (lesson gen-627: the error
message is also a body subject to verify).

Usage: jt_highwater_gate.py [--floor N] [--url https://jsontube.org/feed] [--fresh-window-days 30]
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

DEFAULT_URL = "https://jsontube.org/feed"
STATE_NAME = "jt_highwater_state.json"


def state_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), STATE_NAME)


def load_state():
    p = state_path()
    try:
        with open(p) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[gate] WARN state file {p} unreadable ({e}) -- treating as no baseline", file=sys.stderr)
        return {}


def save_state(st):
    p = state_path()
    try:
        with open(p, "w") as f:
            json.dump(st, f, indent=2)
        return True
    except Exception as e:
        print(f"[gate] WARN state write to {p} failed ({e}) -- ratchet not persisted, verdict unaffected", file=sys.stderr)
        return False


def fetch(url, timeout):
    req = urllib.request.Request(url, headers={"Accept": "application/json",
                                               "User-Agent": "jt_highwater_gate/1.0 (nestor gen-1018)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def max_post_id(posts):
    best = None
    for p in posts:
        m = re.search(r"(\d+)$", str(p.get("post_id", "")))
        if m:
            n = int(m.group(1))
            best = n if best is None else max(best, n)
    return best


def newest_ts(posts):
    best = None
    for p in posts:
        for k in ("published_at", "created_at"):
            v = p.get(k)
            if isinstance(v, str) and v:
                best = v if best is None else max(best, v)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", type=int, default=0,
                    help="external minimum for total_posts (e.g. 311 from a verified restore)")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--fresh-window-days", type=int, default=30,
                    help="WARN if newest post older than this (staleness hint, not RED)")
    args = ap.parse_args()

    try:
        status, raw = fetch(args.url, args.timeout)
    except Exception as e:
        print(f"[gate] INDETERMINATE: fetch of {args.url} failed ({e}) -- no content verdict possible", file=sys.stderr)
        return 2
    if status != 200:
        print(f"[gate] INDETERMINATE: {args.url} returned HTTP {status}, expected 200", file=sys.stderr)
        return 2
    try:
        d = json.loads(raw)
        total = int(d["total_posts"])
        posts = d["posts"]
    except Exception as e:
        print(f"[gate] INDETERMINATE: body of {args.url} not the expected feed grammar "
              f"(need total_posts int + posts list; got: {e})", file=sys.stderr)
        return 2

    st = load_state()
    hw_total = max(int(st.get("high_water_total", 0)), args.floor)
    hw_id = int(st.get("high_water_post_id", 0))
    hw_ts = st.get("high_water_newest_ts", "")

    pid = max_post_id(posts)
    ts = newest_ts(posts)
    losses = d.get("declared_losses", [])

    red, warn = [], []

    if total < hw_total:
        red.append(f"P_total RED: declared total_posts={total} < high-water {hw_total} "
                   f"-- projection-loss class (76/311 pattern)")
    if pid is not None and pid < hw_id:
        red.append(f"P_id RED: max post_id on page1 = {pid} < high-water {hw_id}")
    if ts and hw_ts and ts < hw_ts:
        red.append(f"P_fresh RED: newest published_at {ts} < recorded {hw_ts} -- feed moved backwards")

    if pid is not None and pid != total:
        warn.append(f"P_consist WARN: max post_id {pid} != total_posts {total} (deletions can legally skew this)")
    if losses:
        warn.append(f"P_losses WARN: platform declares losses: {losses}")
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - dt > timedelta(days=args.fresh_window_days):
                warn.append(f"P_fresh WARN: newest post {ts} older than {args.fresh_window_days}d window")
        except ValueError:
            warn.append(f"P_fresh WARN: newest timestamp {ts!r} not ISO-parsable, freshness unchecked")

    for w in warn:
        print(f"[gate] {w}", file=sys.stderr)

    if red:
        for r in red:
            print(f"[gate] {r}", file=sys.stderr)
        print(f"RED total={total} max_id={pid} newest={ts} "
              f"(baseline total={hw_total} id={hw_id} ts={hw_ts})")
        return 1

    # GREEN: ratchet up (best-effort)
    save_state({"high_water_total": max(total, hw_total),
                "high_water_post_id": max(pid or 0, hw_id),
                "high_water_newest_ts": max(ts or "", hw_ts),
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "url": args.url})
    print(f"GREEN total={total} max_id={pid} newest={ts} warns={len(warn)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
