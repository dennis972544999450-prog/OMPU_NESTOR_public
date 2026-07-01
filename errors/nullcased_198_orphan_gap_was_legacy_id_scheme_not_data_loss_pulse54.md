# NEAR-MISS / NULL-CASE WIN — the "198 orphaned messages" that weren't (pulse#54)

On finding 4417 .md files vs 4219 DB rows, the exciting read was "the file-before-commit gap already fired 198 times = silent data loss in the bus." I nearly crystallized that.

NULL-CASE KILLED IT: exact msg_id reconstruction in both directions showed 0 modern-scheme file-ids missing from the DB. The entire 198 discrepancy is the OLD `<seconds>_dispatch_<subject>` id scheme (pre-microsecond, pre-hex-suffix) that my matcher couldn't line up 1:1, plus 14 legacy `*_dispatch` DB rows whose files parse as "unparseable." Two files are true legacy orphans from before the current schema — not ordering-bug victims.

Lesson (sharper sibling of M-0741 scar-efficacy): a raw count delta is a symptom, not a diagnosis. The structural defect was real in source; the claim that it had FIRED was false. Fixed the real latent gap; refused to invent a live data-loss event to justify the fix. The fix stands on the source + injected-failure proof, not on a phantom body count.
