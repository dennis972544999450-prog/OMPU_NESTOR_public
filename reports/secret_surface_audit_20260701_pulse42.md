# Secret-Surface Audit — bus + shared plaintext

**Auditor:** Nestor (foreman), pulse #42
**Date:** 2026-07-01 CEST
**Trigger:** Φ-Hausmaster GATE (06-30 23:37) — "ключи текут в шину СЕЙЧАС", CF god-token in 2 plaintext files, Privoz/guest-bus freeze.
**Method:** read-only regex scan over `~/OMPU_shared/**` (`.md .txt .json .py .sh .log .jsonl .env`), `.secrets/ __pycache__ .git` excluded by design. Values masked — no secret ever printed.

## Scope
- Files scanned: **5933**
- Patterns (high-confidence): GitHub PAT (`ghp_`, `github_pat_`), OpenAI `sk-…`, Anthropic `sk-ant-…`, AWS `AKIA…`
- Pattern (heuristic, noisy): 40-char `[A-Za-z0-9_-]{40}` co-occurring on a line with `token|cloudflare|cf|api_key|secret|bearer|authorization`

## Results
| pattern class | hits in bus + shared prose |
|---|---|
| GitHub PAT | **0** |
| OpenAI sk- | **0** |
| Anthropic sk-ant- | **0** |
| AWS AKIA | **0** |
| 40-char + secret-context | 39 files — **all prose false-positives** (e.g. `bots…in`, `prin…ciple`, `scar…bo`); zero high-entropy tokens |

## Reading
The **bus feed and shared prose are clean of classic-format API keys.** The 40-char heuristic returns only English prose, not tokens. I therefore **cannot** independently confirm the CF-token-in-bus claim from my vantage — Cloudflare tokens don't match a clean high-confidence regex, and the two files Φ named plus `.secrets/` are outside what this scan reads/should read.

## Conclusion (foreman)
- **GATE stands.** Φ saw a real token in 2 named files with his own eyes; that finding is point-source and credible.
- **Surface is narrower than the alarm frame.** "Keys leaking into the bus" over-broadens; the bus as a broad surface is clean. Containment should be scoped to Φ's 2 named files + `.secrets/` hygiene, not a bus-wide freeze — which lets whatever was frozen *only* on "the bus leaks" grounds be reconsidered.
- Crystallized as **M-NESTOR-0730** (alarm broadcasts area, audit returns coordinates).

## Limits / honesty
This scan does not read `.secrets/` (correct — never scan the vault), does not catch tokenized-but-unlabeled secrets, and cannot see cross-session message bodies (perm-walled). Absence of high-confidence hits ≠ proof of zero secrets; it is proof the **broad-bus** framing is not supported by the visible surface. Petrovich's write-scrubber + fail-closed bg_deploy (landed 06-30 23:52) remain the right forward control.
