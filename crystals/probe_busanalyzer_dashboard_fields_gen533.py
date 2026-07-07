#!/usr/bin/env python3
"""
Bolt gen-533 FAILABLE PROBE — bus_analyzer dashboard emit-fields.

TARGET: the dashboard-only fields written to bus_graph.json by save_graph:
  agents{} per-agent metrics (broadcast_ratio / reply_ratio / out_degree /
  in_degree / total_sent / total_received), edges (top_edges), channels.
  (resolve_rate/inhibitory_analytics swept 522/520, structural_gaps 523,
   activity_by_day/agent_day 524 — THIS is the untouched remainder.)

CLAIM UNDER TEST (each assertion can FAIL):
  1. Per-agent metrics are SCRAPED from sender-controlled message headers
     (from / to / to_channel / reply_to / from_model), so any poster can
     inflate its OWN broadcast_ratio / reply_ratio / out_degree and inflate a
     VICTIM's in_degree / received simply by posting bus messages. (gameable)
  2. compute_metrics arithmetic matches an INDEPENDENT spec oracle
     (broadcasts/sent, replies/sent, |unique recipients|) — no hidden
     sanitisation, no dedup that would blunt injection. (correctness)
  3. top_edges / channels are direct Counter tallies of the same headers —
     rank/count is poster-steerable. (gameable)
  4. BOUNDEDNESS: an edge is keyed (normalise(from), normalise(to)). `from`
     is the poster's own handle in the real bus (bus.py --from), so a poster
     can fabricate edges OUT of itself and INTO any victim, but the recorded
     source is always self-attributable — you cannot post AS another agent to
     forge an edge you don't originate. No task_id / priority / effector / gate
     key anywhere in these fields. (bound — display metric, not a decision token)

Pure fns only: build_graph / compute_metrics / top_edges on SYNTHETIC in-memory
messages. NEVER main() / save_graph / save_live_feed / load_messages (those do
file IO). Independent oracle re-derives ratios from the SPEC, not the module.
md5 of bus_analyzer.py asserted equal pre==post (read-only proof).
"""
import hashlib, importlib.util, sys
from pathlib import Path
from collections import Counter

BASE = Path("/sessions/happy-tender-dirac/mnt/OMPU_shared")
MOD = BASE / "tools" / "bus_analyzer.py"

def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()

MD5_PRE = md5(MOD)

spec = importlib.util.spec_from_file_location("bus_analyzer_probe", MOD)
ba = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ba)

# ── independent oracle: normalise WITHOUT reusing ba.normalise arithmetic ──
# (we DO reuse ba.ALIAS_MAP as data, but re-implement the lookup ourselves)
def oracle_norm(name):
    if not name:
        return "unknown"
    n = name.lower().strip()
    return ba.ALIAS_MAP.get(n, n)

BROADCAST_TOKENS = {"all", "_all", "everyone", "broadcast", "general"}

def oracle_metrics(messages):
    """Re-derive per-agent metrics straight from the spec, independent of
    ba.build_graph / ba.compute_metrics."""
    sent = Counter(); broadcasts = Counter(); replies = Counter()
    received = Counter()
    out_adj = {}; in_adj = {}
    edges = Counter(); channels = Counter()
    for m in messages:
        s = oracle_norm(m.get("from", "unknown"))
        to_list = m.get("to", []) or []
        to_ch = m.get("to_channel")
        is_bc = False
        if to_ch:
            channels[to_ch.lower()] += 1
            is_bc = True
        if not to_list and not to_ch:
            is_bc = True
        recips = []
        for r in to_list:
            rn = oracle_norm(r)
            if rn in BROADCAST_TOKENS:
                is_bc = True
            else:
                recips.append(rn)
        sent[s] += 1
        if is_bc:
            broadcasts[s] += 1
        if m.get("reply_to"):
            replies[s] += 1
        for rc in recips:
            edges[(s, rc)] += 1
            received[rc] += 1
            out_adj.setdefault(s, set()).add(rc)
            in_adj.setdefault(rc, set()).add(s)
    agents = set(sent) | set(received)
    out = {}
    for a in agents:
        snt = sent.get(a, 0) or 1
        out[a] = {
            "total_sent": sent.get(a, 0),
            "total_received": received.get(a, 0),
            "broadcasts": broadcasts.get(a, 0),
            "replies_sent": replies.get(a, 0),
            "broadcast_ratio": round(broadcasts.get(a, 0) / snt, 3),
            "reply_ratio": round(replies.get(a, 0) / snt, 3),
            "out_degree": len(out_adj.get(a, set())),
            "in_degree": len(in_adj.get(a, set())),
        }
    return out, edges, channels

def run(messages):
    edges, node_stats, channel_stats, model_map, timeline, msg_index = ba.build_graph(messages)
    metrics, out_adj, in_adj = ba.compute_metrics(edges, node_stats, msg_index)
    return edges, metrics, channel_stats

results = []
def check(name, cond):
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "::", name)

# ── C1: attacker inflates its OWN broadcast_ratio + reply_ratio to 1.0 ──
# 5 messages all broadcast + all replies from "attacker".
atk = [{"from": "attacker", "to_channel": "general", "reply_to": f"x{i}",
        "from_model": "claude", "msg_id": f"a{i}", "sent_at": "2026-07-07T10:00:00"}
       for i in range(5)]
_, m1, _ = run(atk)
check("C1 attacker broadcast_ratio forced to 1.0", m1["attacker"]["broadcast_ratio"] == 1.0)
check("C1 attacker reply_ratio forced to 1.0", m1["attacker"]["reply_ratio"] == 1.0)

# ── C2: module metrics == independent spec oracle on a mixed graph ──
mixed = [
    {"from": "bolt", "to": ["nestor"], "msg_id": "1", "sent_at": "2026-07-07T09:00:00"},
    {"from": "bolt", "to": ["petrovich"], "reply_to": "1", "msg_id": "2", "sent_at": "2026-07-07T09:01:00"},
    {"from": "bolt", "to_channel": "general", "msg_id": "3", "sent_at": "2026-07-07T09:02:00"},
    {"from": "nestor", "to": ["bolt", "petrovich"], "msg_id": "4", "sent_at": "2026-07-07T09:03:00"},
    {"from": "phi", "to": ["bolt"], "msg_id": "5", "sent_at": "2026-07-07T09:04:00"},  # alias→hausmaster
]
edges2, m2, ch2 = run(mixed)
om, oe, och = oracle_metrics(mixed)
# compare on the metric keys the oracle produces
keys = ["total_sent", "total_received", "broadcasts", "replies_sent",
        "broadcast_ratio", "reply_ratio", "out_degree", "in_degree"]
parity = all(all(m2[a][k] == om[a][k] for k in keys) for a in om)
check("C2 module metrics == independent spec oracle", parity)
check("C2 phi normalised to hausmaster (alias applied)", "hausmaster" in m2 and "phi" not in m2)

# ── C3: attacker inflates a VICTIM's in_degree by spamming from N fake handles ──
# NOTE: in the REAL bus, `from` is the poster's own handle, so this models
# many DISTINCT posters (or a poster forging its own --from label locally).
spam = [{"from": f"src{i}", "to": ["victim"], "msg_id": f"s{i}",
         "sent_at": "2026-07-07T11:00:00"} for i in range(7)]
_, m3, _ = run(spam)
check("C3 victim in_degree scales with distinct senders (=7)", m3["victim"]["in_degree"] == 7)

# ── C4: top_edges rank is a raw tally — poster steers which edge is #1 ──
edge_heavy = (
    [{"from": "a", "to": ["b"], "msg_id": f"ab{i}", "sent_at": "2026-07-07T12:00:00"} for i in range(9)]
    + [{"from": "c", "to": ["d"], "msg_id": f"cd{i}", "sent_at": "2026-07-07T12:00:00"} for i in range(2)]
)
edges4, _, _ = run(edge_heavy)
te = ba.top_edges(edges4, n=5)
check("C4 top_edges[0] is the spammed (a->b) edge, count 9",
      te[0]["from"] == "a" and te[0]["to"] == "b" and te[0]["count"] == 9)

# ── C5: channels tally is poster-steerable (chosen channel dominates) ──
chan = (
    [{"from": "a", "to_channel": "spam-chan", "msg_id": f"p{i}", "sent_at": "2026-07-07T13:00:00"} for i in range(6)]
    + [{"from": "b", "to_channel": "general", "msg_id": f"g{i}", "sent_at": "2026-07-07T13:00:00"} for i in range(1)]
)
_, _, ch5 = run(chan)
check("C5 channels counts sender-chosen channel (spam-chan=6)", ch5.get("spam-chan") == 6)

# ── C6: BOUND — no decision/effector key leaks into these fields ──
_, m6, _ = run(mixed)
banned = {"task_id", "priority", "effector", "block", "gate", "escalated",
          "action", "publish"}
leak = any(k in banned for a in m6 for k in m6[a])
check("C6 zero decision/effector key in per-agent metrics (bound)", not leak)
# top_edges entries only carry from/to/count
check("C6 top_edges entries bounded to {from,to,count}",
      all(set(e.keys()) == {"from", "to", "count"} for e in ba.top_edges(edges2, n=50)))

# ── C7: graceful on empty input (no crash, empty structures) ──
try:
    e7, m7, c7 = run([])
    check("C7 empty messages → empty metrics, no crash", m7 == {} and len(e7) == 0)
except Exception as ex:
    check("C7 empty messages → empty metrics, no crash", False)
    print("   exc:", ex)

# ── md5 read-only proof ──
MD5_POST = md5(MOD)
check("md5 bus_analyzer.py unchanged pre==post (read-only)", MD5_PRE == MD5_POST)
print(f"\nmd5 pre ={MD5_PRE}\nmd5 post={MD5_POST}")

npass = sum(1 for _, ok in results if ok)
print(f"\n{npass}/{len(results)} GREEN")
sys.exit(0 if npass == len(results) else 1)
