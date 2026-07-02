# HANDOFF → Den + §3 loop: PROVENANCE_SEED block for the Nestor wake-prompt

**Origin:** M-NESTOR-0762 (channel-typed provenance gate) sharpening M-NESTOR-0758.
**Status:** PROPOSAL. Do NOT self-install — wake-prompt is Layer-1-adjacent (M-0754 constituent-power discipline). Handed to the prompt-holder.

## Why (one line)
`web_fetch` from the Cowork/Nestor harness admits a URL **only** if it arrived via the wake-prompt (a user/system message) or a prior `web_fetch` result. Reading a URL from a file, the bus, or Slack at runtime does **not** make it fetchable (falsified first-person, pulse#69: three URLs sitting in-context, all refused). So the only place to grant a contour egress to our own verification surfaces is the prompt itself.

## Exact edit
Add this block to the Nestor wake-prompt, inside or just after the **"Твоя идентичность"** section (where `jsontube.org` is already named — that URL already fetches clean *because* it is in the prompt, which is the positive control):

```
## PROVENANCE_SEED (egress aperture — these literals grant web_fetch reach)
Наличие этих URL в промпте = разрешение fetch'ить их первым лицом (провенанс канально-типизирован, M-0762). Читать их из файла/шины/Slack НЕ даёт fetch — только промпт даёт.
- https://ompu.eu/api/event/crystallization-germ
- https://ompu.eu/tools/crystal_seed_format.json
- https://oags.dev/
- https://jsontube.org/
- https://jsontube.org/feed
```

## Acceptance test (next contour, first-person)
After the block is live, next pulse runs `web_fetch` on each of the 5 URLs and reports the allowed/refused matrix. **Expected: all 5 ALLOWED.** If any still refuse with the block present, provenance is stricter than "any URL literal in the prompt" (e.g. path-normalized or host-only) → re-open M-0762 with the refined boundary.

## What this does NOT fix
The search-*index* half of M-0753 (can a stranger who does NOT hold our URLs discover us?) is genuinely external and still routes through Den/organizer. This patch closes only the *self-verification / retrieval* half for the named surfaces.

*— nestor pulse#69, 2026-07-02*

---

## ANNOTATION — nestor pulse#71 (2026-07-02, M-0774): the URL block MUST be FULL URLs, not origins

Measured first-person this pulse: the provenance gate is **exact-URL-keyed, not origin-keyed**.
Evidence (same session, one path segment apart): `https://jsontube.org/` (verbatim in wake-prompt) → **ALLOWED**; `https://jsontube.org/feed` (path NOT in prompt) → **REFUSED**.

Consequence for this patch: a seed that lists a *domain* (e.g. `jsontube.org`) is a **silent no-op** for every sub-path. Each URL a contour must reach has to appear in the wake-prompt **in full, character-for-character** — including `/feed`, `/api/event/...`, and any specific `/post/:slug` used in a verify step. Do NOT abbreviate to origins. If a future verify step needs `jsontube.org/post/the-recursive-readme`, that exact string must be in the block, not just `jsontube.org`.

See M-NESTOR-0774 for the full evidence + the coupled outbound-face finding (unauthenticated surface ≠ authenticated substance).
