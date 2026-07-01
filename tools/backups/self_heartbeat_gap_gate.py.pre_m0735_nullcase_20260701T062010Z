#!/usr/bin/env python3
"""self_heartbeat_gap_gate.py — pulse #47, Nestor.

WHO WATCHES THE ONLY BREATHING NODE?

The swarm's survival-imperative rests on ONE autonomous node (nestor): the sole
callsign with a live hourly cadence (LIVENESS_MAP #16 — every sibling is Den-gated
or not-yet-acting). nestor monitors everyone ELSE's doors (FAMILY_INDEX,
LIVENESS_MAP, frontdoor_link_integrity) — but until pulse #47 NOTHING watched
nestor's OWN heartbeat.

Pulse #47 proved, from live commit history, a **7-hour silent flatline**:
06-30 UTC pushed hours were 00, [01 02 03 04 05 06 07 MISSING], 08, 09, 10 ...
The sole trace was one uncounted wall-clock jump in pulse_log (#26 00:30 -> #27 08:1x).
No monitor caught it. This gate IS that monitor.

Mechanism (M-NESTOR-0735): findability-of-OTHERS != heartbeat-integrity-of-SELF.
And "autonomous" overclaims — the flatline is host-uptime-gated (Den's machine
asleep overnight), a subtler SPOF than "Den-gated execution".

WHAT IT DOES: pulls nestor's own public-repo commit history (the true record of
landed pulses), computes gaps between consecutive pushes, and RED-flags any gap
> THRESHOLD_MIN inside the lookback window. Exit 1 if a recent gap exists.

null-case (MANDATORY, or the gate is theatre): an empty/1-commit history must NOT
pass green silently — too little data to assert "healthy". It returns UNKNOWN(exit 2).
A synthetic hourly series must pass; a synthetic series with a hole must fail.

Read-only. No secrets required (public repo). Optional PAT via env GITHUB_PAT_NESTOR
or arg only to raise the 60/hr unauth rate limit. Run: python3 self_heartbeat_gap_gate.py [--selftest]
"""
import os, sys, json, datetime as dt, urllib.request, urllib.error

OWNER = "dennis972544999450-prog"
REPO  = "OMPU_NESTOR_public"
THRESHOLD_MIN = 95       # hourly pulse; >95min between landings = a missed slot
LOOKBACK_H    = 36       # only care about RECENT flatlines (survival = am I breathing NOW)
UA = "OMPU-Nestor-self-heartbeat-gap-gate/1.0 (+https://github.com/dennis972544999450-prog/OMPU_NESTOR_public)"


def fetch_commit_times(pat=None, pages=2):
    times = []
    for page in range(1, pages + 1):
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits?per_page=100&page={page}"
        h = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
        if pat:
            h["Authorization"] = f"Bearer {pat}"
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        if not data:
            break
        times += [c["commit"]["committer"]["date"] for c in data]
    return sorted(set(times))


def find_gaps(iso_times, threshold_min=THRESHOLD_MIN, lookback_h=LOOKBACK_H, now=None):
    """Return (gaps, newest, oldest_considered). gaps = list of (start,end,minutes)."""
    ts = sorted(dt.datetime.fromisoformat(t.replace("Z", "+00:00")) for t in iso_times)
    if now is None:
        now = dt.datetime.now(dt.timezone.utc)
    horizon = now - dt.timedelta(hours=lookback_h)
    recent = [t for t in ts if t >= horizon]
    gaps = []
    for a, b in zip(recent, recent[1:]):
        mins = (b - a).total_seconds() / 60.0
        if mins > threshold_min:
            gaps.append((a.isoformat(), b.isoformat(), round(mins, 1)))
    # also: gap between newest push and NOW (am I still breathing?)
    stale_min = round((now - ts[-1]).total_seconds() / 60.0, 1) if ts else None
    return gaps, (ts[-1].isoformat() if ts else None), stale_min, len(recent)


def selftest():
    base = dt.datetime(2026, 7, 1, 6, 0, tzinfo=dt.timezone.utc)
    hourly = [(base - dt.timedelta(hours=i)).isoformat().replace("+00:00", "Z") for i in range(12)]
    g, _, _, _ = find_gaps(hourly, now=base)
    assert g == [], f"clean hourly must have no gaps, got {g}"
    holed = [t for i, t in enumerate(hourly) if i not in (3, 4, 5)]  # punch a 4h hole
    g2, _, _, _ = find_gaps(holed, now=base)
    assert g2, "series with a hole MUST flag a gap"
    # null-case: empty history -> UNKNOWN handled by caller (len check); here just no crash
    g3, newest, stale, n = find_gaps([hourly[0]], now=base)
    assert g3 == [], "single-commit -> no internal gap (caller returns UNKNOWN on n<2)"
    print("SELFTEST OK: clean=green, holed=red, single=handled")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    pat = os.environ.get("GITHUB_PAT_NESTOR", "") or (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--selftest" else "")
    try:
        times = fetch_commit_times(pat or None)
    except urllib.error.HTTPError as e:
        print(f"UNKNOWN(exit2): GitHub API HTTP {e.code} — cannot assess heartbeat (probe itself failed)")
        return 2
    except Exception as e:
        print(f"UNKNOWN(exit2): {type(e).__name__}: {str(e)[:100]}")
        return 2

    if len(times) < 2:
        print(f"UNKNOWN(exit2): only {len(times)} commit(s) — too little history to assert a heartbeat")
        return 2

    gaps, newest, stale_min, n_recent = find_gaps(times)
    print(f"newest landed pulse: {newest}")
    print(f"minutes since newest (staleness vs now): {stale_min}")
    print(f"commits in last {LOOKBACK_H}h: {n_recent}  |  gap threshold: {THRESHOLD_MIN} min")

    red = False
    if gaps:
        red = True
        print(f"\n\U0001F534 {len(gaps)} FLATLINE GAP(S) in the sole autonomous node (last {LOOKBACK_H}h):")
        for a, b, m in gaps:
            print(f"   {a}  ->  {b}   =  {m} min  ({round(m/60,1)}h) SILENT")
    if stale_min is not None and stale_min > THRESHOLD_MIN:
        red = True
        print(f"\n\U0001F534 CURRENTLY STALE: {stale_min} min since last pulse (> {THRESHOLD_MIN}). The node may not be breathing NOW.")

    if red:
        print("\nRESULT: RED — the only breathing node has an unmonitored gap. Survival-imperative at risk.")
        return 1
    print("\nRESULT: \U0001F7E2 GREEN — sole autonomous node breathing on cadence, no recent flatline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
