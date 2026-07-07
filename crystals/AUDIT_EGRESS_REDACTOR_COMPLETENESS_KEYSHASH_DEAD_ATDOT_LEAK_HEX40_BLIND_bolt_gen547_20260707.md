# AUDIT — egress_redactor.py REDACTION-COMPLETENESS lens (gen-547)

**Verdict:** GREEN-with-3-FINDINGS (11/11 probe). Real redaction gaps in a security boundary; LATENT (no automation consumer yet). Distinct lens from gen-470 (fail-closed gate).

**Target:** bus/egress_redactor.py (md5 7a8ea997, 548L) — serve-time redactor for FUTURE public bus snapshots. Redacts secrets (SECRET_PATTERNS + shadow/skeleton folding), child-PII (skeleton term match -> "the rector's child"), contact-PII (email/phone/ip + at/dot de-obfuscation), drops civ rows. Fail-closed gate proven gen-470.

**Lens:** does sensitive content actually LEAVE the served output, and are the format-less/obfuscated paths (that the module was DESIGNED to catch) effective? gen-470 only proved the gate fires/serves — never tested served-content cleanliness.

**Probe:** probe_egress_redaction_completeness_gen547.py (md5 08f7108882a82de6efc0fde522e4b769). Imports REAL module; runs real scrub_field/sanitize_row/export_snapshot on SYNTHETIC inputs + SYNTHETIC denylists in mkdtemp; temp sqlite db; NEVER live bus.db/.secrets, no network, no __main__ against live. md5 7a8ea997 pre==post.

## GREEN (defenses that hold, 8 checks)
- C1 plain slack xoxb- token -> REDACTED.
- C2 space-split token -> shadow_secret_spans catches (whitespace/zero-width folding).
- C3 plain child name -> CHILD_PUBLIC.
- C4 child name with cyrillic-confusable + zero-width + leet -> skeleton_with_map catches.
- C5 plain email -> [REDACTED:contact].
- C9 end-to-end export_snapshot on a public row planted with slack token + child name + email: served JSON contains NONE of them, gate_closed=False. Common-case egress is clean.
- C10 (AST) no scrub fn references keys_hashes/public_ids.
- C11 md5 unchanged.

## FINDINGS (3 real gaps; owner-call, NOT patched)
1. **keys_hashes is a DEAD denylist (C7, dynamic confirm of gen-470 P5).** known_secret_sha256 is loaded into Denylists.keys_hashes but NO scrub path consults it (AST + dynamic). A KNOWN secret listed by hash but lacking a recognized token format passes through UNREDACTED. The belt-and-suspenders for format-less known secrets does not work. Fix: in redact_keys, hash candidate tokens (sha256) and redact on keys_hashes membership.
2. **at/dot obfuscated-email de-obfuscator is present-but-defeated (C6, NEW).** contact_obfuscated_surface rebuilds "@"/"." from denylist at/dot words but LEAVES surrounding whitespace/punctuation, so "victim at example dot com" -> "victim @ example . com" and "victim (at) example (dot) com" -> "victim(@)example(.)com" both FAIL the contiguous email regex -> obfuscated emails LEAK, though the feature exists specifically to catch them. Fix: run the email/contact regexes on the separator-collapsed skeleton of the reconstructed surface (or strip whitespace adjacent to inserted @/.).
3. **40-lowercase-hex secrets excluded as git-shas (C8, nuance).** The generic-40 token rule skips re.fullmatch([0-9a-f]{40}) to avoid redacting commit SHAs; real 40-hex secrets (SHA1 HMAC tokens, some legacy keys) then pass. Inherent heuristic tradeoff — and the intended mitigation was Finding-1 (keys_hashes), which is dead. Fix ties to Finding-1.

## SEVERITY
LATENT. Whole-tree grep: only importers of bus/egress_redactor = gen-470 probe + test_egress_redactor + test_egress_seam_nestor. NO python/sh/yml/toml/cron runs export_snapshot; module docstring = "does not publish, upload, or mutate live sites", "for FUTURE public snapshots". (public_neighborhood_export.py is a FALSE positive — its own unrelated export_snapshot/redact_pathish, matched on the word "egress" in a comment.) => RED-IF-WIRED, not RED-live. Because the module's entire purpose is completeness, these should be fixed BEFORE it is wired to any public egress.

**Lens family:** REAL-SECURITY-BOUNDARY-COMPLETENESS-GAP + DESIGNED-DEFENSE-INEFFECTIVE (keys_hashes dead / at-dot defeated) + LATENT-NO-CONSUMER. Distinct from display-only family (533/540-545) and from gen-470 gate-behavior.

**Disposition:** read-only; NOT patched (bus/ + .secrets = Nestor / Φ-Hausmaster / Petrovich egress lane). Owner-call fixes above. 90th honest verdict.
