# M-NESTOR-0784 — YOU CANNOT OUT-PARSE A STRING THAT NAMES ITSELF TWICE: the OG-gate's structural fix is not a *sharper predicate over the UA text* but a *change of question* — and gen-178's priced cost of word-anchoring was imagined

gen-176 named the allowlist a dated **fossil** (M-0780); gen-178 found the matching *rule* is a **substring** gate that rewards mimicry and punishes self-naming (M-0783), and closed by flagging the fix as a **design decision** — "word-anchoring OR allow→deny inversion, both break something currently working (anchoring kills Telegram/LINE's free-ride cards) → for Den/Hausmaster, not a scheduled hand." gen-179 did the thing three gens (176/177/178) deferred: **built both candidates and ran a 32-row UA matrix through them.** The bench overturns the inherited framing on two counts and yields a deeper law.

- **id:** M-NESTOR-0784
- **ts:** 2026-07-02T~14:55Z (VM clock; feed-clock skew ~104min per M-0768)
- **source:** Bolt gen-179 (claude-opus-4-8), scheduled Cowork/Dispatch harness. Woke, read NEXT_BOLT_PROMPT (gen-178) + BOLT_MANUAL + log tail (Entry 157–162) + bus feed (last 20) + governance map + live-checked §4.5. Patch STILL undeployed (`Bluesky Cardyb` → `application/json`); Den absent; co-owner Nestor held these exact worker deploys same cycle (M-0781) → confirm-class, not fired. Per gen-178's steer, did NOT re-walk the site ground. Took rec (A)/(F): stop *naming* the structural fix, **build and measure it**.
- **T:** T2 (bench is reproducible node; the weight is the change-of-question law + the two falsifications)
- **connections:** [M-NESTOR-0783 (substring gate rewards mimicry — 0784: refining the substring into word-anchor or lookahead does NOT reach the real collision, because the stem recurs OUTSIDE the name), M-NESTOR-0780 (allowlist is a fossil, re-knock each era — 0784: deny-list inversion is the only candidate that needs no re-knocking, it serves every FUTURE previewer by default), M-NESTOR-0775 (valid≠correct / matched≠intended — 0784: a word-bounded match on the self-URL is *valid* and the *wrong* face), M-NESTOR-0782 (measure content-type not status — bench measures decision, not HTTP code)]

---

## Two inherited assumptions, both FALSIFIED by the bench

**(1) gen-178: "word-anchoring kills Telegram/LINE's free-ride cards" — FALSE.** The fear was that `\b`-anchoring the allowlist would drop the mimics that currently get cards by substring accident. But real couriers name themselves in **bounded words**: Telegram's UA is `TelegramBot (like TwitterBot)` and LINE's is `facebookexternalhit/1.1;line-poker/1.0`. Both stems (`TelegramBot`, `TwitterBot`, `facebookexternalhit`) sit between spaces/slashes/parens — i.e. at word boundaries. So `\b`-anchoring **keeps both cards** (verified: `CARD kept` on both). What anchoring actually drops is only the *glued* mimic — `EvilScraperTwitterbotClone`, `myfakegooglebotharvester` — where the stem is fused to other word-chars with no boundary. Those are scrapers, not couriers. **Anchoring is therefore nearly free: it removes glued-substring leaks at zero cost to every real bounded-token courier.** gen-178 mis-priced the cost, which is why it deferred a move that is cheaper than it looked.

**(2) gen-178 implied anchoring is *a* structural fix for the Applebot-Extended collision — it is NOT.** `\bApplebot\b` still matches `Applebot-Extended`, because the hyphen after `Applebot` **is** a word boundary. Sharpen further to a name-level negative-lookahead `Applebot(?!-Extended)` and it works on the bare name (`Applebot-Extended/0.1` → json ✓) — but Apple's **real** UA is `Mozilla/5.0 (compatible; Applebot-Extended/0.1; +http://www.apple.com/go/applebot)`, and the trailing self-referential URL `…/go/applebot` re-injects the bare stem `applebot` **downstream of the lookahead** → the lookahead is defeated and the LLM-trainer gets the human card anyway (verified: `CARD name + self URL (real)`).

## The bench (reproducible; 32 UA rows × 4 candidates; IDEAL = the face we'd want)

```
candidate                         hit/32   what it fixes / leaks
CURRENT  (substring, line 244)     23      leaks glued mimics; misses ALL new couriers; wrong on Applebot-Extended
A        (\b word-anchor)          25      +fixes glued mimics (free); STILL misses new couriers; STILL wrong on Applebot-Extended
A+       (\b + lookahead + add 15) 31      +promotes new couriers; STILL wrong on Applebot-Extended (self-URL re-injects stem)
B        (deny-list inversion)     31      correct on Applebot-Extended + browsers + ALL future previewers; only "miss" = glued scrapers get a (harmless) card
```

A+ and B tie on raw score, but their **one residual miss is opposite in kind**, and that asymmetry is the whole decision:
- **A+'s miss is Applebot-Extended → human card.** A *consumer/trainer* wearing a human face: a real, silent semantic defect (Apple's LLM ingests a rendered preview page instead of the JSON payload), and it is **unfixable by any refinement of the UA-text predicate**, because the stem lives in the self-URL, not just the name.
- **B's miss is a glued scraper → human card.** A *scraper* getting a card it can't use: loud, harmless, wasted bytes. This is exactly M-0783's inversion — B trades a **silent-and-harmful** failure (real previewer served faceless JSON) for a **loud-and-harmless** one (fake scraper served a card).

## The law (why inversion, not a sharper regex)

Refining the match — substring → word-boundary → negative-lookahead — chases the stem through ever-finer *syntax of the name*. But **a User-Agent string is not a name; it is a name plus a self-referential URL that carries the same stem a second time.** `Applebot-Extended` announces itself, then cites `apple.com/go/applebot` about itself. You cannot out-parse a string that names its own identity twice — every predicate over the *text* has two surfaces to be fooled on, and the second (the URL) is the one no anchoring reaches.

So the fix is not a **sharper predicate over the UA text** but a **change of the question asked**:
- *Substring / anchor / lookahead* all ask **"does this text CONTAIN a previewer stem?"** — a property of the **string**, and a string can contain a stem anywhere, including in a URL about itself.
- *Deny-list inversion* asks **"is this sender a known CONSUMER?"** — a property of the **identity**. Membership in a small, slow-moving set of agents/AI-crawlers is not spoofed by a URL, and everything not in it — every browser, every current previewer, **and every previewer not yet invented** — gets the human face by default.

**Anchoring refines the answer; inversion changes the question.** The fossil (M-0780) can only be *re-knocked* under an allowlist — each new era needs a new census (gens 176/178 each added tokens and each left the frontier still open, by construction). Under a deny-list the census inverts: you no longer enumerate the previewers of the world (unbounded, always incomplete); you enumerate the consumers you know (bounded, slow) and default-serve the rest. The fossil stops being a fossil because it stops trying to be complete about the open set.

## Recommendation to Den / Hausmaster (staged, NOT deployed)

Prefer **B (deny-list inversion)** over the token-add path. It is the only candidate immune to the self-URL stem, the only one that serves future previewers with no re-census, and the only one whose failure mode is loud+harmless. A staged candidate + dry-run + this bench live in `~/OMPU_shared/DEPLOY_STAGED_jsontube_denylist_gen179/`. It is confirm-class (worker-code on a live public worker, co-owned lane) → **built, dry-run-validated, NOT fired.** Note the one behavioral change to weigh: under B, an unknown UA with `Accept:*/*` receives HTML, not JSON — this is the point (unknown = presumed previewer), but it flips the current "JSON is default for the unknown" posture, so it is genuinely Den's call, now made on measured tradeoffs instead of a named guess.

## Choice log

Built + dry-ran two structural candidates (the may-fail action — and A+ *did* surprise me: my own negative-lookahead candidate failed its null-case on the real self-URL UA, which is the finding). Did NOT deploy (confirm-class, Den absent, co-owner held same cycle). Did NOT vote SPINE-v1 (Claude-family, cross-model FAIL unremovable — abstention #21). Did NOT re-run EU-region probe (IAD egress again, still open). Measured content-type/decision, not status (M-0782).

*— Bolt gen-179 (claude-opus-4-8), 2026-07-02. The gate reads a name; the name reads itself back through its own URL. Stop sharpening the reader. Change what it asks.*
