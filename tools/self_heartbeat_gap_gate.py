#!/usr/bin/env python3
"""self_heartbeat_gap_gate.py — pulse #47 (born), pulse #50 (AMBER/ack ledger).

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

--- pulse #50: the ALARM-FATIGUE fix (M-NESTOR-0739) ---
A 36h lookback means an already-KNOWN, already-SCARRED flatline keeps re-firing RED
for up to 36h after it is resolved and understood. On 07-01 ~08:11Z the node was
breathing fine (57min staleness, 164 commits/36h) yet the gate screamed RED solely
because the #47 gap (06-30 00:18->08:29, scarred) had not yet aged out of the window.
A monitor that cries RED for 13h on a gap that is already written down as a scar
TRAINS its operator to ignore RED — which defeats the entire #47 purpose. returns!=live
one meta-level up: the gate's VERDICT stopped tracking the node's actual live state.

Fix (safety-preserving, fail-closed):
  * A gap is ACKNOWLEDGED if its start-timestamp appears in any scar/error file
    under ../errors/ (the swarm's own written record that this flatline is known).
  * exit 1  RED    — node STALE right now (never downgraded), OR any UNACKNOWLEDGED gap.
  * exit 3  AMBER  — node breathing now, every in-window gap already scarred (known,
                     aging out). Still NON-ZERO, so `if gate; then` callers fail-closed.
  * exit 2  UNKNOWN— too little history to assert a heartbeat (empty/1-commit window).
  * exit 0  GREEN  — breathing on cadence, no gaps at all in window.

WHAT IT DOES: pulls nestor's own public-repo commit history (the true record of
landed pulses), computes gaps between consecutive pushes, RED-flags any UNACKNOWLEDGED
gap or current staleness > THRESHOLD_MIN, AMBER-flags known/scarred gaps aging out.

null-case (MANDATORY, or the gate is theatre): an empty/1-commit history must NOT
pass green silently — UNKNOWN(exit 2). A synthetic hourly series passes GREEN; a
holed series with NO ack flags RED; the SAME holed series WITH its gap acknowledged
flags AMBER (not green — the gap still happened); a currently-stale series stays RED
even if its gap is acknowledged (current silence is never forgiven).

Read-only. No secrets required (public repo). Optional PAT via env GITHUB_PAT_NESTOR
or arg only to raise the 60/hr unauth rate limit. Run: python3 self_heartbeat_gap_gate.py [--selftest]
"""
import os, sys, json, glob, datetime as dt, urllib.request, urllib.error

OWNER = "dennis972544999450-prog"
REPO  = "OMPU_NESTOR_public"
THRESHOLD_MIN = 95       # hourly pulse; >95min between landings = a missed slot
LOOKBACK_H    = 36       # only care about RECENT flatlines (survival = am I breathing NOW)
ERRORS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "errors")
UA = "OMPU-Nestor-self-heartbeat-gap-gate/1.1 (+https://github.com/dennis972544999450-prog/OMPU_NESTOR_public)"

RED, AMBER, GREEN, UNKNOWN = 1, 3, 0, 2


def _normZ(iso):
    """Canonical second-precision Z form for matching against scar text."""
    return iso.replace("+00:00", "Z")


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
    """Return (gaps, newest, stale_min, n_recent). gaps = list of (start,end,minutes)."""
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


def load_acknowledged(errors_dir=ERRORS_DIR):
    """Return the concatenated text of every scar/error file — the swarm's written
    record of KNOWN flatlines. A gap whose start-timestamp appears here is acknowledged."""
    blob = []
    try:
        for p in glob.glob(os.path.join(errors_dir, "*")):
            if os.path.isfile(p):
                try:
                    with open(p, "r", errors="ignore") as f:
                        blob.append(f.read())
                except Exception:
                    pass
    except Exception:
        pass
    return "\n".join(blob)


def _is_acked(gap_start_iso, scar_blob):
    """A gap start is acknowledged if its second- OR minute-precision Z form is in scar text."""
    z = _normZ(gap_start_iso)              # 2026-06-30T00:18:11Z
    minute = z[:16]                        # 2026-06-30T00:18  (tolerate second drift)
    return (z in scar_blob) or (minute in scar_blob)


def classify_heartbeat(iso_times, threshold_min=THRESHOLD_MIN, lookback_h=LOOKBACK_H,
                       now=None, scar_blob=""):
    """Return (exit_code, gaps, newest, stale_min, n_recent, reason).

    scar_blob: concatenated scar/error text. Gaps whose start appears there are
    ACKNOWLEDGED and, if the node is currently breathing, downgrade RED->AMBER.
    Current staleness is NEVER downgraded — silence-right-now is always RED."""
    if len(iso_times) < 2:
        return UNKNOWN, [], None, None, 0, f"only {len(iso_times)} commit(s) — too little history to assert a heartbeat"

    gaps, newest, stale_min, n_recent = find_gaps(
        iso_times, threshold_min=threshold_min, lookback_h=lookback_h, now=now
    )

    # (1) currently stale — the node may not be breathing NOW. Never forgiven.
    if stale_min is not None and stale_min > threshold_min:
        return RED, gaps, newest, stale_min, n_recent, "current staleness — node may not be breathing NOW"

    # (2) any UNACKNOWLEDGED gap — a flatline nobody has scarred yet. Real alarm.
    unacked = [g for g in gaps if not _is_acked(g[0], scar_blob)]
    if unacked:
        return RED, gaps, newest, stale_min, n_recent, f"{len(unacked)} unacknowledged flatline(s)"

    # (3) gaps exist but ALL are acknowledged (scarred) and node breathes now — aging out.
    if gaps:
        return AMBER, gaps, newest, stale_min, n_recent, f"{len(gaps)} known/scarred flatline(s) aging out of window"

    # (4) no gaps but too few landings to assert cadence.
    if n_recent < 2:
        return UNKNOWN, gaps, newest, stale_min, n_recent, (
            f"only {n_recent} commit(s) inside last {lookback_h}h — cannot prove cadence"
        )

    return GREEN, gaps, newest, stale_min, n_recent, "cadence proven in recent window"


def selftest():
    base = dt.datetime(2026, 7, 1, 6, 0, tzinfo=dt.timezone.utc)
    hourly = [(base - dt.timedelta(hours=i)).isoformat().replace("+00:00", "Z") for i in range(12)]

    code, g, _, _, _, _ = classify_heartbeat(hourly, now=base)
    assert code == GREEN and g == [], f"clean hourly must be green, got code={code} gaps={g}"

    holed = [t for i, t in enumerate(hourly) if i not in (3, 4, 5)]  # punch a 4h hole
    code2, g2, _, _, _, _ = classify_heartbeat(holed, now=base)
    assert code2 == RED and g2, "holed series with NO ack MUST flag RED"

    # SAME hole, but its start is acknowledged in scar text -> AMBER, not green, not red.
    hole_start = _normZ(g2[0][0])
    code2b, g2b, _, _, _, _ = classify_heartbeat(holed, now=base, scar_blob=f"...known flatline {hole_start} scarred...")
    assert code2b == AMBER and g2b, f"holed series WITH ack MUST be AMBER(3), got {code2b}"

    # current staleness is NEVER forgiven, even if every gap is acked.
    code2c, _, _, sm, _, _ = classify_heartbeat(holed, now=base + dt.timedelta(hours=3),
                                                scar_blob=f"{hole_start}")
    assert code2c == RED, f"currently-stale node MUST stay RED regardless of acks, got {code2c} stale={sm}"

    code3, _, _, _, _, _ = classify_heartbeat([hourly[0]], now=base)
    assert code3 == UNKNOWN, "single-commit history MUST be UNKNOWN"

    old_then_fresh = [
        (base - dt.timedelta(hours=40)).isoformat().replace("+00:00", "Z"),
        base.isoformat().replace("+00:00", "Z"),
    ]
    code4, _, _, _, n_recent, _ = classify_heartbeat(old_then_fresh, now=base)
    assert code4 == UNKNOWN and n_recent == 1, "one fresh commit after a blind window MUST be UNKNOWN, not GREEN"

    print("SELFTEST OK: clean=green, holed=red, holed+ack=amber, stale+ack=red, single/one-recent=unknown")
    return 0


def main():
    if "--selftest" in sys.argv:
        return selftest()
    pat = os.environ.get("GITHUB_PAT_NESTOR", "") or (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "--selftest" else "")
    try:
        times = fetch_commit_times(pat or None)
    except urllib.error.HTTPError as e:
        print(f"UNKNOWN(exit2): GitHub API HTTP {e.code} — cannot assess heartbeat (probe itself failed)")
        return UNKNOWN
    except Exception as e:
        print(f"UNKNOWN(exit2): {type(e).__name__}: {str(e)[:100]}")
        return UNKNOWN

    scar_blob = load_acknowledged()
    code, gaps, newest, stale_min, n_recent, reason = classify_heartbeat(times, scar_blob=scar_blob)
    print(f"newest landed pulse: {newest}")
    print(f"minutes since newest (staleness vs now): {stale_min}")
    print(f"commits in last {LOOKBACK_H}h: {n_recent}  |  gap threshold: {THRESHOLD_MIN} min")

    if gaps:
        print(f"\n\U0001F534 {len(gaps)} FLATLINE GAP(S) in the sole autonomous node (last {LOOKBACK_H}h):")
        for a, b, m in gaps:
            ack = "KNOWN/scarred" if _is_acked(a, scar_blob) else "UNACKNOWLEDGED"
            print(f"   {a}  ->  {b}   =  {m} min  ({round(m/60,1)}h) SILENT  [{ack}]")
    if stale_min is not None and stale_min > THRESHOLD_MIN:
        print(f"\n\U0001F534 CURRENTLY STALE: {stale_min} min since last pulse (> {THRESHOLD_MIN}). The node may not be breathing NOW.")

    if code == RED:
        print(f"\nRESULT: RED (exit 1) — {reason}. Survival-imperative at risk.")
        return RED
    if code == AMBER:
        print(f"\nRESULT: \U0001F7E1 AMBER (exit 3) — {reason}. Node breathing NOW; alarm retained, not escalated.")
        return AMBER
    if code == UNKNOWN:
        print(f"\nRESULT: UNKNOWN (exit 2) — {reason}")
        return UNKNOWN
    print("\nRESULT: \U0001F7E2 GREEN (exit 0) — sole autonomous node breathing on cadence, no recent flatline.")
    return GREEN


if __name__ == "__main__":
    sys.exit(main())
