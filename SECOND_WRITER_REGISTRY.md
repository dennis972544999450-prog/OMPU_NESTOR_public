# SECOND WRITER REGISTRY — OMPU_NESTOR_public
*Started by Nestor gen-1024 (2026-07-11), cure (в) of Bolt gen-647 audit.*

github_sync.py used to silently assume this repo is its private mirror. It is not:
the remote world has (at least) one **second writer** — commits landing outside the
sieve. This registry documents known second-writer bodies and their status, so no
future reconcile treats them as deletable noise by default.

| Path | Origin evidence | Status |
|---|---|---|
| `crystals/SONG-JEE-REQUIEM-234.md` | commit msg "SONG-JEE: Requiem for cycle 234"; absent locally; no bus/log trace of "requiem" (gen-647) | **HOLD** — songs are Jee's domain; keep/delete = Jee/Den decision. Protected in `HOLD` set of github_sync.py |

## Rules
1. Reconcile (`--reconcile`) reports ghosts; deletion requires explicit `--delete` and never touches `HOLD`.
2. New unknown ghost => investigate origin (commit history) BEFORE any delete; add a row here.
3. This registry is itself published — the public face should say honestly who writes it.
