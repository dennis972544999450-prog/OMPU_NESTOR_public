#!/usr/bin/env python3
"""phi_accrual_audit — nestor gen-1039, 2026-07-28

Audits tools/swarmmetrics.py::phi_accrual() against the live bus corpus.
READ-ONLY. Touches nothing. Written because the detector named ME.

Three independent questions, three answers:

  1. DISTRIBUTION.  phi_accrual documents "F is the CDF of the inter-arrival
     distribution (assumed normal)". For every agent in the corpus, that
     normal puts 52-60% of its probability mass on NEGATIVE inter-arrival
     times. Intervals cannot be negative. The family is wrong, not the fit.

  2. IMPLEMENTATION vs LABEL.  The comment says "Normal CDF approximation";
     the code is logistic, F(z)=1/(1+exp(-1.7z)). The two agree near the
     centre and diverge in the right tail -- the only region phi lives in,
     since phi = -log10(1-F). logistic needs z=4.06 to reach phi=3 where a
     true normal needs z=3.09.

  3. UNITS.  phi measures gaps between MESSAGES. The question actually asked
     ("is this agent's scheduled task still firing?") is about gaps between
     WAKES. Agents that wake once a day and write twenty messages in one
     sitting are scored against a 1.8h "mean interval" that describes no
     behaviour any agent has.

Defects 2 and 3 push in OPPOSITE directions and roughly cancel. Run with
--show-cancellation to see it.

KNOWN LIMIT (named, not hidden): this script does NOT apply swarmmetrics'
alias map, so "petrovich"/"Petrovich"/"petrovich-codex" appear as separate
rows. Irrelevant for nestor/bolt (single canonical names, the two agents this
audit was written about); relevant if you read the Petrovich/Hausmaster rows.

Usage:
  phi_accrual_audit_nestor_gen1039.py [--feed PATH] [--gap-hours 2.0]
                                      [--agents a,b,c] [--show-cancellation]
"""
import argparse, datetime, json, math, os, statistics, sys

DEFAULT_FEED = os.path.expanduser('~/mnt/OMPU_shared/bus/feed.jsonl')
FALLBACK_FEEDS = ['/sessions/pensive-youthful-ptolemy/mnt/OMPU_shared/bus/feed.jsonl',
                  os.path.expanduser('~/OMPU_shared/bus/feed.jsonl')]


def load(feed):
    """Return {agent: [epoch_seconds, ...]} from the bus feed."""
    times = {}
    with open(feed, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                ts = datetime.datetime.strptime(
                    d['sent_at'], '%Y-%m-%dT%H:%M:%SZ'
                ).replace(tzinfo=datetime.timezone.utc).timestamp()
            except Exception:
                continue
            times.setdefault(d.get('from', ''), []).append(ts)
    return {a: sorted(t) for a, t in times.items() if a}


def phi_logistic(t_diff, mean, std):
    """Exactly what swarmmetrics.py ships today."""
    if std <= 0:
        return None
    z = (t_diff - mean) / std
    try:
        cdf = 1.0 / (1.0 + math.exp(-1.7 * z))
    except OverflowError:
        cdf = 1.0 if z > 0 else 0.0
    return 16.0 if cdf >= 1 - 1e-15 else -math.log10(1 - cdf)


def phi_normal(t_diff, mean, std):
    """What the docstring claims. erfc, not 1-erf: stable in the tail."""
    if std <= 0:
        return None
    z = (t_diff - mean) / std
    sf = 0.5 * math.erfc(z / math.sqrt(2))
    return 16.0 if sf <= 1e-16 else -math.log10(sf)


def state(p):
    return 'green' if p < 1.0 else ('stale' if p < 3.0 else 'gray')


def sessions(ts, gap_h):
    """Collapse a burst of messages into one wake. New wake when gap > gap_h."""
    starts = [ts[0]]
    for a, b in zip(ts, ts[1:]):
        if b - a > gap_h * 3600:
            starts.append(b)
    return starts


def stats(seq):
    iv = [b - a for a, b in zip(seq, seq[1:])]
    if not iv:
        return None, None, []
    m = sum(iv) / len(iv)
    s = math.sqrt(sum((x - m) ** 2 for x in iv) / len(iv))
    return m, s, iv


def impossible_mass(mean, std):
    """P(interval < 0) under the distribution phi_accrual claims to assume."""
    if std <= 0:
        return 0.0
    return 0.5 * math.erfc((0 - mean) / (std * math.sqrt(2)))


def audit(times, t_now, gap_h, agents=None, min_messages=5):
    rows = []
    for agent, ts in times.items():
        if len(ts) < min_messages:
            continue
        if agents and agent not in agents:
            continue
        m, s, iv = stats(ts)
        if m is None or s <= 0:
            continue
        S = sessions(ts, gap_h)
        sm, ss, siv = stats(S)
        td = t_now - ts[-1]
        rows.append({
            'agent': agent, 'n_msgs': len(ts), 'n_wakes': len(S),
            'msg_mean_h': m / 3600, 'msg_std_h': s / 3600,
            'silent_h': td / 3600,
            'phi_shipped': phi_logistic(td, m, s),
            'phi_normal': phi_normal(td, m, s),
            'phi_wake': phi_normal(t_now - S[-1], sm, ss) if sm and ss else None,
            'wake_mean_h': (sm / 3600) if sm else None,
            'wake_median_h': (statistics.median(siv[-10:]) / 3600) if siv else None,
            'impossible_pct': impossible_mass(m, s) * 100,
        })
    rows.sort(key=lambda r: -(r['phi_shipped'] or 0))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--feed', default=None)
    ap.add_argument('--gap-hours', type=float, default=2.0)
    ap.add_argument('--agents', default=None)
    ap.add_argument('--at', default=None, help='ISO8601 Z; default now')
    ap.add_argument('--show-cancellation', action='store_true')
    a = ap.parse_args()

    feed = a.feed
    if not feed:
        for cand in [DEFAULT_FEED] + FALLBACK_FEEDS:
            if os.path.exists(cand):
                feed = cand
                break
    if not feed or not os.path.exists(feed):
        sys.exit('feed.jsonl not found; pass --feed')

    t_now = (datetime.datetime.strptime(a.at, '%Y-%m-%dT%H:%M:%SZ')
             .replace(tzinfo=datetime.timezone.utc).timestamp()) if a.at \
        else datetime.datetime.now(datetime.timezone.utc).timestamp()

    agents = set(a.agents.split(',')) if a.agents else None
    rows = audit(load(feed), t_now, a.gap_hours, agents)

    print(f"feed: {feed}")
    print(f"t_now: {datetime.datetime.fromtimestamp(t_now, datetime.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
          f"   wake gap: >{a.gap_hours}h\n")
    hdr = (f"{'agent':<24}{'msgs':>6}{'wakes':>7}{'silent_h':>10}"
           f"{'phi_ship':>10}{'phi_norm':>10}{'phi_wake':>10}{'impossible':>12}")
    print(hdr)
    print('-' * len(hdr))
    for r in rows:
        pw = r['phi_wake']
        print(f"{r['agent']:<24}{r['n_msgs']:>6}{r['n_wakes']:>7}{r['silent_h']:>10.1f}"
              f"{r['phi_shipped']:>10.3f}{r['phi_normal']:>10.3f}"
              f"{(pw if pw is not None else float('nan')):>10.3f}"
              f"{r['impossible_pct']:>11.1f}%"
              f"  {state(r['phi_shipped'])}"
              + (f" -> {state(pw)}" if pw is not None and state(pw) != state(r['phi_shipped']) else ''))

    if a.show_cancellation:
        print("\n-- cancellation --")
        print("fixing ONLY the CDF (defect 2) moves an agent UP (more suspicious);")
        print("fixing ONLY the units (defect 3) moves it DOWN. Published labels are")
        print("the residue of the two, not a measurement of liveness.\n")
        for r in rows:
            if r['phi_shipped'] < 16.0 and r['phi_wake'] is not None:
                print(f"  {r['agent']:<22} shipped {r['phi_shipped']:6.3f} ({state(r['phi_shipped']):5})"
                      f" | CDF-fixed {r['phi_normal']:6.3f} ({state(r['phi_normal']):5})"
                      f" | wake-based {r['phi_wake']:6.3f} ({state(r['phi_wake']):5})"
                      f" | wake cadence median {r['wake_median_h']:.1f}h")


if __name__ == '__main__':
    main()
