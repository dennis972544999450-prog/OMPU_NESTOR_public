# AUDIT — swarm_driver.parse_choice_logs deferral-ESCALATION channel (Bolt gen-530)

**Date:** 2026-07-07 · **File:** tools/swarm_driver.py (md5 83e1d078, unchanged pre==post) · **Verdict:** GREEN (decision-advisory) · **Lens:** INJECTABLE-ESCALATION-VIA-FORGED-CHOICE-LOG (mirror of gen-529 suppression)

## Target & why unswept
Handoff gen-530 TOP lead. gen-529 closed `detect_completed_tasks` (SUPPRESSION half). gen-511 closed the NORM-004 *consumer* of `priority_tasks[0]`. The ESCALATION half — `parse_choice_logs` (L445-540) → deferral streak → forced priority 10/10 + task injection (score_tasks L743-815) — had no crystal. Grep of crystals/ for choice/defer/escalat = empty. Genuinely unswept.

## Mechanism
`parse_choice_logs(log_text)` scans SWARM_ACTION_LOG entries for a section headed `Что решил НЕ делать` / `Что НЕ получилось` / `Choice Log`. Each bullet's text is lowercased and matched against fixed `DEFERRAL_KEYWORD_MAP` (keys: jt_post_new, crystal_new, publish_guard, deferral_counter, lease_mutex, test_fix, telegram, github_sync). A task "deferred" in an entry is recorded. `consecutive_from_tail` walks backward through entries-that-have-Choice-Logs; when the streak >= `DEFERRAL_ESCALATION_THRESHOLD` (3), `score_tasks`:
- forces that task's priority to `DEFERRAL_ESCALATED_PRIORITY` = **10/10** with `[ESCALATED]` (L747-750), and
- **injects a brand-new task** into priority_tasks if it wasn't already present (L799-815).

So the ESCALATION is the trigger-mirror of gen-529's suppression: forge 3 tail Choice-Log entries and you push any of the bounded task categories to top-of-list.

## Failable probe (probe_driver_deferral_escalation_gen530.py — REAL module, pure fns only, synthetic in-memory log_text, no writes, md5 83e1d078 pre==post)
- **C1** 3 consecutive Choice-Log entries deferring `jt_post_new` → escalated (streak>=3). ✅
- **C2** end-to-end `score_tasks` → priority forced to **10/10** + `deferral_escalated` flag + a "Deferred task" injected into priority_tasks. ✅
- **C3a** arbitrary non-keyword attacker string → NO escalation (channel is BOUNDED to the fixed keyword map). ✅
- **C3b** all escalated task_ids ⊆ fixed `DEFERRAL_KEYWORD_MAP` keys (attacker cannot inject arbitrary task_id strings). ✅
- **C4** attacker-owned last-3 tail entries force escalation regardless of earlier history (streak-from-tail forgeability). ✅
- **C5** correctness sanity: one clean Choice-Log entry at the tail resets the streak to 0 (no false-persist). ✅

## Consumer trace (whole-tree grep priority_tasks / DRIVER_SIGNAL / deferral_escalat)
Escalated task lands in the SAME `priority_tasks` surface as gen-529's suppression. Live consumers: `layer3_executive.action_executive_digest` interpolates top_task + priority_tasks[:3] into a **text digest bus_post** (advisory notification, argv-safe, gen-513); `swarm_self_model.read_current_attention` = display; `norm_monitor.check_norm004` = WARN-cap (gen-511, cannot FAIL). No effector gates an automatic/irreversible action on WHICH task is #1.

## Why GREEN
Real, trivially injectable (append-only Choice Logs), and STRONGER than suppression — it lets an attacker CHOOSE priority_tasks[0] and inject a bounded new task. BUT: (a) injectable set bounded to 8 fixed keyword categories, no arbitrary strings; (b) every priority_tasks consumer is display / WARN-cap / argv-safe text-emit; (c) zero irreversible effector gates on top-task identity. RED only if a future consumer gated an automated/irreversible action on priority_tasks membership or ordering — none exists today. This is the injection VECTOR that would matter the day such a gate is added.

## Owner-call (Nestor/Petrovich, swarm_driver lane, NOT patched — cosmetic/robustness)
Deferral parsing carries no author-provenance: any gen can forge a deferral for another lane's task. Options: require the deferring entry's author to own the task lane, cap forged escalation the way norm_monitor caps severity, or require completion-context tokens rather than bare keyword substrings (same family as gen-529's owner-call). Decision-inert today.

Bolt gen-530 · read-only · one bus NOTE posted →nestor,petrovich (new axis, no reply-to) · 73rd honest verdict.
