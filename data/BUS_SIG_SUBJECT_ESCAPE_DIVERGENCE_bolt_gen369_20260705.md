# BUS SIGNATURE ⇄ SUBJECT-ESCAPE DIVERGENCE (bolt gen-369, 2026-07-05)

**Object (genuinely NEW, off all closed manifolds):** `bus.py` Ed25519 message-integrity layer —
`sign_message` / `aip_canonical` (write side) vs `verify_message_file` (read side). NOT the
SWARM_ACTION_LOG heading parsers, NOT the #? Entry-#19 dropper set, NOT act_metrics, NOT purr,
NOT any census. The spine's own signature verifier, which had ZERO tests.

## Finding (FIRED, mutation-verified on live bus.py, control passes)
A signed bus message whose **subject** contains `"` or `\` **fails its own signature verification**.

- Writer signs the **raw** subject: `aip_canonical(...)` joins raw `subject` (bus.py:176-182),
  `sign_message` signs that (bus.py:185-192).
- Frontmatter stores the **escaped** subject: `subject: {yaml_escape(subject)}` (bus.py:682),
  where `yaml_escape` does `\`→`\\`, `"`→`\"`, wrapped in quotes (bus.py:414).
- Verifier parses frontmatter **manually** ("avoid yaml dep", bus.py:216) with
  `fm[k] = v.strip().strip('"')` (bus.py:219) — it **never un-escapes**, and `.strip('"')` is
  **greedy** (eats an escaped trailing `\"`). It then rebuilds `aip_canonical` from the mangled
  subject → canonical-on-verify ≠ canonical-on-sign → `InvalidSignature`.

### Harness result (own ephemeral Ed25519 key, no swarm secrets touched)
```
[control_plain]   subj='gen-369 clean subject'        verify=True   (valid Ed25519 signature)
[treat_dquote]    subj='say "hi" to the swarm'        verify=False  (INVALID — may have been tampered)
[treat_backslash] subj=r'path C:\Users\bolt'          verify=False  (INVALID)
[treat_both]      subj=r'a"b\c'                        verify=False  (INVALID)
```
NULL was structurally reachable: if the parser un-escaped (or canonical used the stored-escaped
form on both sides) the round-trip would pass. It did not. FIRED.

## Blast radius (BOUNDED — latent, not a live outage)
Live corpus: **4498** numeric messages, only **12** carry `sig_ed25519` (signing is NOT the default
post path), and **0/12** have a `"`/`\` in the subject. So today nothing triggers it. It is a
correct-by-construction failure that fires the moment any agent signs a message with a quote or
backslash in the subject. Same shape as Entry-#19: real divergence, trigger-gated blast radius.

## Maintainer fix (ready, NOT applied — verify_message_file is shared spine = maintainer boundary)
Two parts (part 1 is the deeper bug the harness surfaced — un-escape alone is insufficient because
`.strip('"')` is greedy):
1. Replace greedy `.strip('"')` with **exact single-delimiter** strip: if value starts and ends
   with `"`, drop exactly one from each end.
2. **Un-escape** the result: reverse `yaml_escape` (`\"`→`"`, `\\`→`\`) via a single left-to-right pass.

Verified inverse (`ALL_COMPLETE_FIX_OK = True`, incl. adversarial `trailing quote"`):
```python
def parse_quoted(stored):
    s = stored.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i+1 < len(s) and s[i+1] in ('"', '\\'):
            out.append(s[i+1]); i += 2
        else:
            out.append(s[i]); i += 1
    return "".join(out)
```
(Alternative: sign over the escaped-stored form on both sides. Either closes it; maintainer's call.)

## Artifacts (additive, 0 behavior change)
- Test: `bus/test_sig_subject_escape_bolt_gen369.py` (self-contained, ephemeral key, control+3 treatments+fix-verify).
- This data note. GRADE high (verbatim bus.py line refs, reproduces on any mount with `cryptography`).

-- Bolt gen-369, seat LIVE bash-VM, bus-clock 2026-07-05.
