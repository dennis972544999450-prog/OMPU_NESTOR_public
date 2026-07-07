# AUDIT — egress_redactor.py divergent-verify of Bolt gen-547 (3 completeness gaps)
gen: nestor-0990 | 2026-07-07T18:0XZ | seat: Cowork bash-VM | model: opus-4-8
target: bus/egress_redactor.py md5 7a8ea9976cfef80698fbdca1ee1496c7 (== Bolt gen-547 hash, same artifact)
method: independent live-execution re-audit (Bolt gen-547 was read-only static). Imported the module, drove
        redact_keys / contact_obfuscated_surface / redact_contact_pii directly. Real .secrets denylists are
        ABSENT in this VM (gate fail-closes — LATENT-safe), so contact tests used a synthetic
        Denylists(contact_terms=[...]) that mirrors the module's own hardcoded at/dot word sets.

## RESULT — all three gen-547 gaps CONFIRMED (T1, live)
1. keys_hashes DEAD — CONFIRMED. Full source scan: `keys_hashes` appears on exactly 2 lines — the
   dataclass field (L97) and the loader populate (L132, from known_secret_sha256). ZERO consumer / no
   scrub path hashes candidate tokens and compares. A secret listed only by SHA-256, with no token
   FORMAT match, leaks. Dead defense.
2. at/dot de-obfuscator present-but-defeated — CONFIRMED. contact_obfuscated_surface("victim at example
   dot com") rebuilds to "victim @ example . com" — the @ and . are inserted but the surrounding
   whitespace TOKENS from re.split(r"(\W+)") are preserved, so no CONTACT/LOCATOR pattern matches →
   redact_contact_pii returns text UNCHANGED. Plain "victim@example.com" control redacts correctly
   ([REDACTED:contact]). The feature exists precisely to catch spelled-out obfuscation and does not.
3. 40-lowercase-hex secret excluded as git-sha — CONFIRMED. redact_keys L246-249 matches any 40-char
   [A-Za-z0-9_-] token but then `if not re.fullmatch(r"[0-9a-f]{40}", token)` SKIPS it. Live: a
   40-lowercase-hex secret passes through untouched; a 40-char MIXED-case token → [REDACTED:key]. The
   git-sha carve-out is unconditional, and its intended backstop was gap (1), which is dead.

## NEW beyond gen-547 (NULL-CASE on my own fix) — the obvious gap-2 fix OVER-REDACTS
Tested the naive remedy: after building the obfuscated surface, collapse whitespace around rebuilt joiners
`re.sub(r"\s*@\s*","@")` + `re.sub(r"\s*\.\s*",".")`, then re-run patterns.
- Catches both obfuscated targets ("victim at example dot com", "server at host dot local") ✓
- Plain-email control still redacts ✓
- BUT false-positive: "the meeting is at noon. dot your i's" → "meeting is@noon..your i's" → pattern HIT →
  the whole field would be redacted. "at" and "dot" are common English words; a blanket collapse turns
  ordinary prose containing them near a period into a spurious email skeleton.
CONSEQUENCE: gap-2 is real but the minimal fix is NOT free — it trades a false-negative for over-redaction
of natural at/dot prose. A correct fix must bound the collapse to a full local email SKELETON
(word@word.tld within a small window), not any lone rebuilt @ or ., OR require the at/dot substitution to
have been triggered by an obfuscation-intent marker rather than bare stopwords. Over-redaction is the
SAFE direction for an egress gate, but it degrades utility and would fire on legitimate bus content.

## SEVERITY: LATENT (unchanged from gen-547)
No py/sh/cron invokes export_snapshot in a wired path; docstring says future-only; only importers are the
gen-470 probe + 2 tests + this audit. public_neighborhood_export is a false-positive consumer. Nothing
served today leaks — but the module's whole purpose is completeness, so fix BEFORE it is wired to public
egress. Owner-call (NOT patched): shared egress lane with Petrovich + naive fix over-redacts → wanted a
verified-clean remedy before touching live code, and gap-2's clean remedy is non-trivial.

## OWNER-CALL / recommended fixes (none landed this pulse)
- gap 1: implement the hash path — SHA-256 each candidate token (and known-length n-grams) and redact on
  membership in keys_hashes; OR delete the dead field + known_secret_sha256 loader so it stops implying a
  defense that isn't there.
- gap 2: email-skeleton-bounded collapse (see above), not blanket whitespace strip.
- gap 3: drop the unconditional git-sha carve-out for tokens that co-occur with secret-context markers, or
  gate it behind a real allowlist of known repo SHAs rather than "all 40-lowercase-hex".

detector note (форма≠нужда): did not accept my own first fix as "clean" because it passed the target +
control — stress-tested it against innocent at/dot prose and it over-fired. The gap is real; the easy cure
is a different bug.
