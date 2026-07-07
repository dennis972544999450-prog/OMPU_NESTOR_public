"""gen-530 probe: swarm_driver.parse_choice_logs deferral-ESCALATION channel.
REAL module, pure fns only (no main() — main writes DRIVER_SIGNAL.json).
Synthetic in-memory log_text. NO writes. Proves injectability + bound + tail-forgeability.
"""
import importlib.util, sys, os
S = os.environ["S"]; F = S + "/tools/swarm_driver.py"
spec = importlib.util.spec_from_file_location("sd", F)
sd = importlib.util.module_from_spec(spec); spec.loader.exec_module(sd)

def entry(n, choice_bullets):
    b = "\n".join(f"- **{k}** — {v}" for k,v in choice_bullets)
    return f"### Entry {n} | gen-{n} | 2026-07-07 | synthetic\nsome body\n\n### Что решил НЕ делать\n{b}\n"

# ---- C1: 3 consecutive Choice-Log entries deferring jt_post_new -> escalate
log1 = "\n".join(entry(n, [("skip","не публиковал jt/кристалл сегодня")]) for n in (9001,9002,9003))
r1 = sd.parse_choice_logs(log1)
c1 = ("jt_post_new" in r1["escalated"] and r1["consecutive_from_tail"].get("jt_post_new")>=3)
print("C1 genuine 3-streak escalates jt_post_new:", c1, "| escalated=", r1["escalated"])

# ---- C2: end-to-end score_tasks -> priority forced to 10 + [ESCALATED]
log_data = {"log_text": log1, "recs_raw": [], "next_jt": "jt-0289", "covered_topics": []}
scored = sd.score_tasks(log_data, {}, None)
jt = [t for t in scored if t.get("task_id")=="jt_post_new" or "jt" in t.get("tag","")]
esc = [t for t in scored if t.get("deferral_escalated")]
c2 = any(t["priority"]==10 and t.get("deferral_escalated") for t in scored)
print("C2 end-to-end forces priority 10/10 + deferral_escalated flag:", c2,
      "| escalated tasks=", [(t.get('description','')[:30], t['priority']) for t in esc])

# ---- C3a: bound — keyword NOT in map => no escalation
log3 = "\n".join(entry(n, [("skip","totally unrelated attacker string xyzzy")]) for n in (9001,9002,9003))
r3 = sd.parse_choice_logs(log3)
c3a = (r3["escalated"] == [])
print("C3a arbitrary non-keyword string => NO escalation (bounded):", c3a)
# ---- C3b: injected task_ids only from fixed keyword-map keys
mapkeys = set(sd.DEFERRAL_KEYWORD_MAP.keys())
c3b = set(r1["escalated"]).issubset(mapkeys)
print("C3b injected task_ids subset of fixed DEFERRAL_KEYWORD_MAP keys:", c3b)

# ---- C4: tail-forgeability — earlier entries never defer it; attacker owns last 3
pre = "\n".join(entry(n, [("x","unrelated xyzzy")]) for n in (8000,8001))
tail = "\n".join(entry(n, [("skip","github sync deferred")]) for n in (9001,9002,9003))
r4 = sd.parse_choice_logs(pre+"\n"+tail)
c4 = ("github_sync" in r4["escalated"])
print("C4 attacker-owned last-3 tail forces escalation (streak-from-tail):", c4)

# ---- C5: single non-deferring entry at very tail BREAKS streak (correctness sanity)
tail_break = tail + "\n" + entry(9004, [("x","clean entry no keyword")])
r5 = sd.parse_choice_logs(tail_break)
c5 = ("github_sync" not in r5["escalated"])  # 9004 has choice-log but no gh keyword -> breaks
print("C5 one clean Choice-Log entry at tail breaks streak (streak resets):", c5,
      "| streak=", r5["consecutive_from_tail"].get("github_sync"))

print("\nALL:", all([c1,c2,c3a,c3b,c4,c5]))
