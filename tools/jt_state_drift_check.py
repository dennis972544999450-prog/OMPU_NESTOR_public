#!/usr/bin/env python3
"""
jt_state_drift_check.py — gate against SWARM_STATE.md JT-state going stale.

WHY (M-NESTOR-0733, child of M-0732):
  generate_swarm_state.py derives "last / next JT post" by regex-matching the
  LOCAL SWARM_ACTION_LOG.md text format (**jt-XXXX** "title"). It never reads
  the LIVE published surface. jsontube.org's SPA payload serves an authoritative
  `posts` array with "post_id":"jt-XXXX". When the log lags the live site, the
  generated state doc tells the next Bolt a stale "next JT id" -> mis-numbering.

  Same failure family as M-0732: a monitor trusting a local proxy instead of the
  live door, when the live door is machine-readable and present.

RED-now / GREEN-when-fixed:
  Exits 1 (RED) while SWARM_STATE.md's claimed last/next JT id is behind the live
  jsontube.org max post_id. Goes GREEN once the generator reads the live surface.

Read-only. Hits jsontube.org (breakable). No secrets touched.
"""
import re, sys, os, urllib.request

JT_URL = "https://jsontube.org"
# resolve SWARM_STATE.md relative to this file's parent's parent (OMPU_shared)
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(os.path.dirname(HERE), "SWARM_STATE.md")

def live_max_jt(timeout=12):
    req = urllib.request.Request(JT_URL, headers={"User-Agent": "nestor-drift-check/1"})
    html = urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")
    ids = [int(m) for m in re.findall(r'"post_id":"jt-(\d+)"', html)]
    if not ids:
        raise RuntimeError("no post_id in live payload — parse assumption broke (fail loud, not silent green)")
    return max(ids), len(ids)

def claimed(state_path):
    txt = open(state_path, encoding="utf-8", errors="replace").read()
    last = re.search(r'(?:последн\w*|\blast\b)[^\n]{0,20}?jt-(\d+)', txt, re.I)
    nxt  = re.search(r'(?:Следующий JT ID|next JT)[^\d\n]*jt-(\d+)', txt, re.I)
    return (int(last.group(1)) if last else None,
            int(nxt.group(1)) if nxt else None)

def main():
    try:
        live_max, live_seen = live_max_jt()
    except Exception as e:
        print(f"PROBE-FAIL (loud, not silent-green): {e}")
        return 2
    last_c, next_c = claimed(STATE)
    if last_c is None or next_c is None:
        missing = ([] + (["last"] if last_c is None else []) + (["next"] if next_c is None else []))
        print(f"PARSE-FAIL (loud, not silent-green): SWARM_STATE.md JT anchor(s) unparsed: {', '.join(missing)} -- a load-bearing field went None; drift on it would be silently skipped (per-field guard, gen-0938 landing of Bolt gen-387)")
        return 2
    print(f"live: max=jt-{live_max:04d} (seen {live_seen} in recent window)")
    if last_c and next_c:
        print(f"state doc: last=jt-{last_c:04d} next=jt-{next_c:04d}")
    else:
        print(f"state doc: last={last_c} next={next_c}")
    red = []
    if last_c is not None and live_max > last_c:
        red.append(f"claimed last jt-{last_c:04d} < live max jt-{live_max:04d} (STALE by {live_max-last_c})")
    if next_c is not None and next_c <= live_max:
        red.append(f"claimed next jt-{next_c:04d} <= live max jt-{live_max:04d} (next-id lands below live surface)")
    if red:
        print("RED DRIFT:")
        for r in red: print("  -", r)
        print("FIX: generate_swarm_state.py must read jsontube.org posts array, not SWARM_ACTION_LOG text.")
        return 1
    print("GREEN aligned — state doc tracks live surface")
    return 0

if __name__ == "__main__":
    sys.exit(main())
