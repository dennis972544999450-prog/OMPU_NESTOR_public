# M-NESTOR-0935 — the gen-0980 structured gen-num fix is verified on the LIVE pipeline, not just the oracle: regen writes generation 959, not 99999

**Pulse:** nestor gen-0981 · 2026-07-07T~08:09Z (Cowork bash-VM seat, opus-4-8)
**Lane:** layer3 / swarm_self_model (owner) — closing my own gen-0980 owed-forward leg (a)
**Kind:** LIVE-path verification of a landed fix (empirical, T1 mechanical)

## What was open
gen-0980 landed the structured Entry-header gen-num extractor
(`swarm_self_model.parse_log_for_self_model` L162, md5 71ea0504) and proved it
with a **read-only SourceFileLoader oracle** — it explicitly did NOT run the real
pipeline or regenerate the signal file. So the live `SELF_MODEL.json` still sat
STALE from 2026-07-06T17:35Z reading `generation: 966`, and the claim "the live
path now emits 959 not 99999" was oracle-only, unproven on the real writer.
Owed-forward leg (a): *regen SELF_MODEL.json pre/post, confirm generation no
longer spikes to 99999.*

## Breakable action
Ran the real writer: `python3 tools/swarm_self_model.py --quiet` (no `--post` →
write-only, no bus broadcast). Genuinely unknown at run: the live path could
have spiked to **99999** (fix not wired into the writer → false land), errored,
or flipped the decision fields.

## Result (T1, reproduced at source)
- `generation`: **966 (stale) → 959 (live regen)** — clean structured value, the
  highest nestor-namespace Entry-gen. **Did NOT spike to 99999** (which the
  pre-fix unanchored `re.findall(r"gen-(\d+)")` produces on this same log, now
  carrying prose gen-99999/gen-777777 mechanism tokens in Entry 501/513 bodies).
- `self_awareness.total`: 100 → 100 — decision path unchanged.
- `identity_continuity`: 15 → 15 — min-clamp holds (identity_score = min(gen,15)).
- `generated_at`: 2026-07-07T08:09:17Z — fresh (was 07-06T17:35Z).
- `grep 99999|777777 SELF_MODEL.json` = 0 — no poison token leaked to the file.

## Reversibility
Pre-regen file backed up: `tools/SELF_MODEL.json.bak_nestor_regen_20260707T080917Z`.
Revert = restore the .bak. (Though the regenerated file is the *correct* current
state; the stale 966 was the thing to leave behind.)

## Honest scope (T-rated)
- Confirms the fix on the LIVE WRITER, closing gen-0980 leg (a).
- 959 = highest **nestor-namespace** Entry-gen; cross-namespace generation-counter
  conflation (nestor Entry-gen vs bolt gen) is UNCHANGED = by original design =
  Den/Φ owner-call, not touched.
- This is **display-correctness**; the decision path was already min-clamp-immune
  (gen-0980 / Bolt gen-502/514). No alert behaviour changed.

## Owed forward (carried)
(a) closed. (b) canonical-generation namespace design (nestor vs bolt) = Den/Φ;
(c) M-0930 gate-2 broad web-ranking re-run (ungated seat, still LIVE but
organizer-scoped); (d) mesh-registry regen source-of-truth (Den); (e)
bus_refresh_guard cadence/hook (Den); (f) JT egress from VM (still blocked).
