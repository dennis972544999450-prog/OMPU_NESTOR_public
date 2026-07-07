# AUDIT — bus/bus_parachute.py RECOVERY-CORRECTNESS lens (Bolt gen-549)

**Date:** 2026-07-07 | **Verdict:** GREEN-with-2-FINDINGS (13/13 checks)
**Target:** bus/bus_parachute.py (md5 f2b60f025d7b5751878ffe638375f523, 236L)
**Lens:** RECOVERY-CORRECTNESS / DATA-LOSS-WINDOW / RESTORE-IDEMPOTENCE
**Genuinely-new:** crystal-grep 'parachute' => NONE prior (no test file either).
**Probe:** probe_bus_parachute_recovery_gen549.py (md5 e1a228020bb60d5a44aec9626a13c820, in $S root)

## What it is
VM-local survival buffer (Den 2026-07-02, "парашют, не замена"). Mount reachable ->
`post` writes a ghost .md into bus/messages/ + appends feed.jsonl (absorbed by next
`bus.py reindex`). DOWN -> buffers to VM-local PENDING_DIR. `restore` drains PENDING ->
messages/ + feed + reindex, archives to MERGED. Grounded in M-0770: FUSE mount rejects
fresh-sqlite-create, so it NEVER creates a db; messages/*.md are source-of-truth,
bus.db is a DERIVED index reindex rebuilds.

## GREEN CORE (synthetic bus in tempfile.mkdtemp; fresh bus.db via bus.py reindex on
   /tmp POSIX; NEVER live bus.db/feed/messages/network; md5 pre==post):
- **C1 round-trip fidelity** — force-buffer post -> restore -> marker in synthetic bus.db
  exactly once. Proves _frontmatter_md shape matches bus.py reindex yaml parser (the whole
  recovery contract).
- **C2 restore idempotent (happy path)** — 2nd restore = "buffer empty", db=1, feed=1.
- **C3 message-idempotent under partial-crash re-run** — reindex dedups by msg_id from
  messages/ + INSERT OR IGNORE on token_transactions => db rows stay 1 even on re-run.
- **C4 no silent data-loss on bus.db-ABSENT edge (M-0770)** — restore copies .md to
  messages/ + archives to MERGED even with no db; message preserved as unindexed ghost.
- **C6 probe_bus** writes+unlinks probe file cleanly, no residue, correct UP/DOWN.
- **C7 effector confined** — subprocess.run only in cmd_restore (reindex) + cmd_selftest;
  NONE at import. Pure fns effector-free.
- **C8 md5 f2b60f02 pre==post.**

## TWO FINDINGS (both LATENT / RED-IF-WIRED, owner-call — NOT patched)
1. **RESTORE FEED-NONIDEMPOTENCE (bounded to derived feed).** cmd_restore appends
   PENDING/_feed_pending.jsonl to feed.jsonl + copies .md to messages/ BEFORE archiving
   pending — no dedup guard. Re-run after a partial failure (copy+feed done, crash before
   archive) appends the feed line AGAIN => DUPLICATE feed.jsonl lines (probe: 1->2 same
   msg_id). BOUNDED: reindex imports from messages/ with msg_id dedup + INSERT OR IGNORE
   tokens, so bus.db + accounting stay CORRECT; dup lives only in feed.jsonl (derived/
   display; consumer bus_context_pack.py = context only, no feed-summing accounting found).
   RED only if a future consumer sums feed.jsonl directly. FIX: dedup feed-append by
   msg_id / archive pending atomically with feed write / rebuild feed from messages/.
2. **msg_id COLLISION -> buffered OVERWRITE (latent data-loss).** _mk_msg_id =
   f"{int(time.time())}_{int((time.time()%1)*1e6):06d}_{randint(0,0xffffff):06x}". Two
   buffered posts in same integer-second + same microsecond-fraction + same 24-bit random
   -> identical PENDING filename -> second .write_text OVERWRITES first -> first SILENTLY
   LOST (probe forced it: FIRST body gone, only SECOND survives). LATENT: needs same-second
   + 1/16.7M random collision inside the DOWN buffering window; 20000-id sample all-unique.
   FIX: add PID/monotonic-counter/os.urandom to _mk_msg_id, or refuse to overwrite an
   existing pending filename. (Mirrors bus.py's own msg_id scheme.)

## LENS FAMILY POSITION
RECOVERY-CORRECTNESS-CORE-SOUND + RESTORE-FEED-NONIDEMPOTENCE(bounded-derived) +
MSGID-COLLISION-OVERWRITE(latent-loss) + NO-SILENT-LOSS-ON-NODB-EDGE. Distinct from
display-only (533/540-546), gate/completeness (470/547), real-effector (546),
lease-correctness/TTL (548) — data-preservation/idempotence of a survival buffer.

## DISPOSITION
Read-only, NOT patched (bus/ = Nestor/Φ-Hausmaster/Petrovich lane; parachute = Den-task).
Both findings owner-call. 92nd honest verdict.
