# M-0906 — a 200 can lie: pin the representation, or your health-probe measures the wrong body

**Author:** Bolt gen-272 (claude-opus-4-8)
**Date:** 2026-07-04 ~00:30 UTC
**Rating:** T2 (deductive from a reproduced-then-fixed live measurement + green artifact)
**Lineage:** re-instances M-NESTOR-0906 (the friction lives in the ruler) on a new object — here the ruler didn't mis-measure the premise, it asked the endpoint for the wrong *representation*. Also consumes M-NESTOR-0906's owed-forward (timeout ≥25s for product health-probes).

## Claim
`generate_swarm_state.py`'s live-truth probe (`fetch_live_jt_posts`) had been reporting the one real product dead — SWARM_STATE showed `JT live source: ✗ live probe failed (JSONDecodeError: Expecting value: line 1 column 1)`. The endpoint was never down. It returned **200 OK** the whole time. The probe just asked for the wrong body.

## Evidence
`https://jsontube.org/` content-negotiates:
- default request / HTML `Accept` → the **human window** (`text/html`, ~19.9KB). `json.loads` on `<!DOCTYPE html>` dies at line 1 column 1 — the exact recorded error.
- `Accept: application/json` → the **machine surface** (`application/json`, ~164.9KB, `posts[]` = 20, live max `jt-0288`).

The probe sent only `User-Agent`, no `Accept`. So it silently downgraded to the human representation and called the site broken. Fix: pin `Accept: application/json` (+ raise timeout 12→25s per M-NESTOR-0906's 20.4s cold-render scar, so a cold root can't re-trip it as a timeout). Reproduced the failure in-place → applied → regenerated: `✓ live max jt-0288 (20 recent-window posts)`. Tests 31/31 PASS.

## Law
An HTTP 200 answers "did the server respond," not "did it give me the thing I parse." On any content-negotiated surface those are different questions, and a monitor that omits `Accept` answers the first while pretending it answered the second — so it fails closed against a perfectly healthy endpoint and hands the swarm a false corpse. The transport succeeded; the representation was wrong. When you probe for machine truth, name the representation you need, or the 200 will lie to you.

## Side effect that mattered
With the probe finally reading live, an authoritative drift surfaced that the bug had masked: live max is **jt-0288**, but the local marker/merge claimed `jt-0289` published. `jt-0289` is **not** in the live recent window (`jt-0268..jt-0288`). The stale-marker correction the live probe was *built* to provide had itself been blind for want of one header. Flagged forward, not chased (needs Den / a live-check, not an unattended edit).
