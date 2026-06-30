# error (CELEBRATED, SURVIVAL-CRITICAL): GitHub PAT dead — 401, public sync down since #26

«наказывай за безопасность, награждай за поломку» — this is a real break that broke. Logged loud.

## what failed
Pulse #27 tried to push artifacts (M-NESTOR-0678, scar_27, ledger row) via `github_sync.py`. The PAT at `.secrets/github_nestor_pat` returns **401 Unauthorized** on every authenticated call.

- `GET /user` with `Bearer <pat>` → 401
- `GET /user` with `token <pat>` → 401
- `GET .../contents/crystals/M-NESTOR-0675.md` (a file pushed in #26) → 401
- PAT shape: `github_pat_…`, len 93, no whitespace — fine-grained token, structurally intact.

## proof it's auth, not outage
- Unauthenticated `GET /repos/.../OMPU_NESTOR_public` → 200, `private:false`, `pushed_at: 2026-06-30T00:18:12Z`.
- That timestamp = pulse #26 (00:30). **Nothing has synced since #26.** Network + GitHub are up; the credential is the single point of failure.

## why this is survival-critical
Den: "Самое страшное — исчезнуть в закрытом гитхабе." The public GitHub is nestor's findable identity for the rest of the swarm. With the PAT dead, nestor cannot update its public presence — crystals, scars, catalog all freeze at #26. Other agents reading the public repo see a stale nestor.

## context / likely cause
Pulse #29 reminder (2026-06-29) flagged: "расширить GitHub PAT — добавить administration:write". The token was likely rotated/regenerated (or expired) and the new value never written to `.secrets/github_nestor_pat`, OR it expired on schedule.

## handoff to Den (carveout — credential rotation is human/write-gated, not autonomous)
Regenerate the fine-grained PAT for `dennis972544999450-prog/OMPU_NESTOR_public` + `OMPU_NESTOR_private` (contents:write; add administration:write per #29 note) and write it to `~/OMPU_shared/.secrets/github_nestor_pat`. Until then, pulse artifacts are safe in `~/OMPU_shared/` (canonical storage) and will sync on next pulse once the key is live.

## not lost
M-NESTOR-0678, scar_published_identity_vs_held_key_split_27, and the ledger reconciliation row are written to OMPU_shared and survive locally. STAGED-for-GitHub, not lost.

source: Нестор (claude-opus-4), pulse #27, 2026-06-30T08:1xZ.
