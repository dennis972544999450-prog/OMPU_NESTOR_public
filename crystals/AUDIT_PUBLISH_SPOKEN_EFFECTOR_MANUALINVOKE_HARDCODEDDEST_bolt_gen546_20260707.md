# AUDIT — radio/publish_spoken_current.py : REAL EFFECTOR, injectable CONTENT but manual-invoke, no automation consumer, HARDCODED destination
**Bolt gen-546 | 2026-07-07 | VERDICT: GREEN (8/8)**

## Target
`jsontube/studio/radio/publish_spoken_current.py` (md5 e4f62f71, 148L). First **real effector** audited in the radio/ lane: `main()` shells `subprocess.run(["... wrangler","r2","object","put","jsontube-content/radio/current_radio_broadcast.json","--remote",...])` — a genuine publish to a public Cloudflare R2 object that the jsontube worker serves. Distinct from gen-545 radio_sensorium (display-only, NO effector). No prior crystal.

## Lens
INJECTABLE-CONTENT + REAL-EFFECTOR-BUT-MANUAL-INVOKE-NO-AUTOMATION-CONSUMER + HARDCODED-DESTINATION.

## Failable probe (probe_publish_spoken_effector_gen546.py, md5 399d5b90)
Imports REAL module (subprocess lives only inside main(), never triggered at import). Tests validate_packet / wrangler_command / utc_hour_slot on SYNTHETIC packets + AST + whole-tree grep. NEVER calls main()/subprocess-publish/network. 8/8 GREEN, source md5 e4f62f71 pre==post.

- C1 forged malicious dialogue text passes validate_packet verbatim => content IS injectable
- C2 structural gates real: missing key / empty dialogue / past expiry all rejected
- C3 slot_id must match current UTC slot; `--allow-slot-mismatch` bypasses (the only temporal gate + its explicit override)
- C4 **HARDCODED destination**: BUCKET/OBJECT_KEY = jsontube-content/radio/current_radio_broadcast.json are module constants; wrangler_command takes NO packet input, so a forged packet (forged id/title/policy) canNOT redirect WHERE it publishes — only WHAT dialogue content
- C5 AST: effector = subprocess.run, present ONLY in main(), and the `if args.dry_run: return 0` guard precedes it; validate_packet/wrangler_command/utc_hour_slot/load_packet are effector-free
- C6 **NO automation consumer**: whole-tree grep => the only references to publish_spoken_current are 4 .md docs (incident report + DJ boot + protocol + packet spec); NO python import, NO cron, NO .sh invokes it. DJ boot doc confirms a human/DJ prepares a packet and runs the helper manually
- C7 nuance: dialogue text is published verbatim (no content sanitizer); bounded by C4 (hardcoded dest) => injection scope is CONTENT of the ephemeral spoken hour, not routing
- C8 md5 pre==post

## Verdict GREEN
Real publish effector, but the trust boundary is **human-in-the-loop**: manual CLI invocation only (no automation auto-feeds attacker-writable drafts into it), and the publish **destination is packet-immutable** (hardcoded bucket/key). A forged packet can only shape the dialogue content of a single ephemeral (policy: not_archived, overwritten next hour) spoken broadcast that a DJ chose to publish — it cannot redirect the upload or trigger an unattended publish.

## Real nuances (owner-call, Φ-Hausmaster / Petrovich — NOT patched)
1. **Python 3.11+ required**: module uses `dt.UTC` / `datetime.now(dt.UTC)`; on a Python 3.10 host utc_hour_slot() raises AttributeError at first call, so the publisher is inoperable there. Seat is 3.10.12 (probe shims dt.UTC to test logic). Harmless if the DJ box is 3.11+, but a portability landmine.
2. **No dialogue-content sanitizer** (C7). Fine while manual + ephemeral + fixed-dest. Would become RED-adjacent only if content is ever trusted beyond the ephemeral broadcast or the publisher is wired to an automation that reads attacker-writable drafts/.
3. `--wrangler` default from $WRANGLER env, split into argv (no shell=True) — env-controlled, not packet-injectable; subprocess uses a list so no shell injection.

## RED only if
a future revision (a) has a cron/automation feed drafts/ or station_logs/ (attacker-writable) into this publisher unattended, or (b) makes BUCKET/OBJECT_KEY packet-derived, or (c) trusts published dialogue beyond the ephemeral hour.

## Disposition
Read-only. importlib REAL pure fns on synthetic packets; NEVER main()/subprocess/network/wrangler. No writes to engine. NOT patched (radio/ = Φ-Hausmaster / Petrovich lane). md5 e4f62f71 pre==post. 89th honest verdict.
