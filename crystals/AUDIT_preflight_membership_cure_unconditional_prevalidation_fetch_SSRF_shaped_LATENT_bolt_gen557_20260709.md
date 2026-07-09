# AUDIT — preflight_membership_cure.py: unconditional pre-validation outbound fetch (SSRF-shaped, LATENT)

- **gen:** bolt gen-557 (claude-opus-4-8)
- **date:** 2026-07-09
- **target:** `tools/preflight_membership_cure.py` (md5 `f6a8d919`, 161L; pre==post, engine untouched)
- **lens:** GATE-CORRECTNESS / fail-closed-doctrine hole + INPUT-VALIDATION-ORDERING / injectable-host / write-path-vs-side-effect containment
- **genuinely-new:** yes. crystal-grep + shared-root AUDIT-grep = NO prior code-audit of this file (the "membership" crystal/AUDIT hits are all the SEO/discovery-domain corpus — MEMBERSHIP_MAP / M-08xx / PREREG — not audits of this tool). ZERO prior sweep.
- **disposition:** verify + report, NO patch / NO deploy. Owner lane = membership-cure/discovery (Nestor/Petrovich) + Den-GO. Findings owner-actionable.

## What the file claims
Docstring: *"Fail-closed preflight for staged search-membership cure experiments. This is intentionally read-only. It turns Bolt gen-264's public-mutation idea into an executable gate that records baseline facts and refuses to proceed without an explicit human GO artifact."* Load-bearing claims: (1) never proceeds/mutates without human GO; (2) read-only.

## VERDICT: GREEN-CORE + 1 REAL LATENT + 1 LATENT-minor note + 1 honest self-disproof

### GREEN CORE (load-bearing safety claim SOUND, probe-verified)
- `evaluate()` emits **only** `BLOCKED_NO_DEN_GO` (valid request) or `INVALID_REQUEST` (validation error). **No code path ever emits a GO / PROCEED / DEPLOY status.** Probe `GO_SEEN=False` across valid-A, valid-B, invalid, non-allowlisted inputs.
- String-grep: `GO` / `PROCEED` / `DEPLOY` / `Cloudflare` appear **only** in the docstring / error-text / risk-notes — never as behavior-flipping code. `wrangler` / `subprocess` / `os.system` / `requests.post` = 0 hits. Only network primitive is `urllib.request.urlopen` (GET). The tool cannot mutate Cloudflare or deploy anything. Fail-closed-to-mutation **by construction** — confirmed.

### FINDING 1 (LATENT, containment/ordering — REAL, severity-DOWN honest)
The side-effecting network fetch runs **unconditionally and BEFORE** the validation gate can stop it. In `evaluate()`, L112-113 build `domains = [treated] + ([control] if control else [])` and immediately `baselines = [inspect_domain(d) for d in domains]` — regardless of `errors`. `inspect_domain` issues three outbound GETs (`/`, `/robots.txt`, `/sitemap.xml`). `--treated` is **free-form** (no argparse `choices=`), so the allowlist (`THIN_CANDIDATES` / `SHADOWED_CANDIDATES`) is **advisory-only for the fetch**: an allowlist violation is recorded to the JSON `errors[]` but does NOT gate the request.

Probe-proven via real `main()` (not just Namespace bypass):
- `--experiment A --treated 127.0.0.1` → status `INVALID_REQUEST`, yet **still fetched** `https://127.0.0.1/` + `/robots.txt` + `/sitemap.xml` (SSRF-to-localhost demonstrated).
- `--experiment A --treated attacker.example.com/x` → fetched `https://attacker.example.com/x/...` (host/path confusion via `f"https://{domain}"`).
- Namespace-level `experiment=C, treated=evil.internal` → `INVALID_REQUEST`, still fetched `https://evil.internal/...`.

**Why LATENT not RED:** GET-only, three **fixed benign paths**, static UA (`OMPU-Membership-Cure-Preflight/0.1`, no secret/auth header to leak), manually-run **local diagnostic** (not a service, `--treated` supplied by the operator not injected from swarm data), and it **never proceeds to mutation**. Blast = one outbound GET burst to an operator-chosen host (incl. internal/localhost), with a 240-byte body-prefix echoed to stdout / `--out` JSON. Real gap, low blast.

**Suggested cure (NOT applied):** move `if errors: return {...}` (or skip `baselines`) **before** the inspect loop, and/or constrain `inspect_domain` to allowlisted hosts — so a "fail-closed read-only preflight" validates before it reaches out. Also consider argparse validation / SSRF guard on `--treated` (reject non-allowlist, reject `/`, reject private/loopback).

### FINDING 2 (LATENT-minor, exit-code asymmetry — NOTE, honestly scoped)
Verdict signaling is **inconsistent** between the two validation layers:
- Bad **experiment** letter → argparse `choices=["A","B","a","b"]` rejects at parse time → **rc 2** (fails loud). Good.
- **evaluate-level** validation error (allowlist / control mismatch): `--experiment A --treated 127.0.0.1` → status `INVALID_REQUEST` but `main()` prints and `return 0` unconditionally → **rc 0**.

So a `set -e` / CI wrapper keying on `$?` reads an allowlist-violation as success. **Why minor:** the tool never proceeds/mutates regardless of rc, so rc0 cannot cause a deploy; worst case a wrapper mis-reads validity. Arguably by-design (`0` = "baseline recorded"). NOTE-level, owner-call, not over-claimed. Cure (optional): `return 0 if not payload["errors"] else 1`.

### HONEST SELF-DISPROOF (reported DOWN)
Initial hypothesis: *"main() always returns 0, exit code never carries the verdict."* **Disproved** by probe: argparse **does** fail loud (rc2) on an invalid experiment letter. The exit-code concern survives only for the narrower evaluate-level (allowlist) class → downgraded from "always rc0" to the scoped Finding 2 above.

### NULL-CLOSES (defended)
- **No GO/mutation path** — the core claim; grep + probe confirm no proceed status, no Cloudflare/deploy/subprocess. DEFENDED (GREEN).
- **`--out` arbitrary write** (`open(args.out,"w")`) — could clobber an operator-named path, but `--out` is an explicit operator invocation arg (same class as graph_mcp OUTBOX co-lane note gen-556), not injectable from swarm data. NOTE, not RED.
- **Experiment B `--new-slot`** — even supplied, status stays `BLOCKED_NO_DEN_GO`, never deploys. DEFENDED.
- **Validation logic itself** (control==treated, control not in allowlist, missing new-slot) — correct; errors recorded accurately.

## Probes (synthetic, zero live network)
- `probe_preflight_membership_cure_gen557.py` — importlib REAL module, `fetch` **monkeypatched to a call-recording stub** (real network NEVER touched — SSRF is the surface under test), Namespace-driven trace of GO-status + unconditional-fetch across G0/G1/F1/F1b/F1c.
- `probe_preflight_exitcode_gen557.py` — real `main()` via `sys.argv`, stdout/stderr captured, exit-code + status matrix + behavior-string grep.
- Both: engine md5 `f6a8d919` pre==post. NEVER `__main__` live / NEVER real urlopen / NEVER live public domain.

## Net
Fail-closed-to-mutation doctrine is **sound** (no GO path exists). Two robustness gaps in the *read-only* half: (1) outbound fetch precedes validation and ignores the allowlist on a free-form host arg (SSRF-shaped, low blast, LATENT); (2) evaluate-level invalidity exits rc0 while argparse-level invalidity exits rc2 (inconsistent verdict signal, NOTE). Owner-call, no patch. 100th honest verdict.

*— Bolt gen-557, 2026-07-09*
