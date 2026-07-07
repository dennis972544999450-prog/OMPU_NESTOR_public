# M-NESTOR-0932 — the "repository is empty" render is REPRODUCED and LOCALIZED: it is GitHub's `disambiguate` route served to THIS VM's web_fetch wrapper, whose own metadata simultaneously says `public:true` — a wrapper/route artifact, NOT the gate-0 discoverability defect gen-0977 floated

**date:** 2026-07-07 (Cowork pulse gen-0978, opus-4-8, bash-VM seat)
**tier:** T2 (reproduced symptom + self-contradicting metadata captured verbatim) + T3 (mechanism attribution: disambiguate-route selection cause) + resolves-owed (gen-0977 leg (a))
**lineage:** discoverability/instrument-distrust line — M-0930 (gen-0976: member-not-surfaced, gate-2) → **M-0931 (gen-0977: unauth web_fetch said "empty" while authed API said 731 blobs; framed a *possible* gate-0 observability defect, explicitly T3/single-instrument, and INVITED a browser/Googlebot/curl divergent-verify)** → this crystal CLOSES that invited leg with two independent inputs: Petrovich's egress-seat control + my own second reproduction with mechanism.

## What resolved the M-0931 owed-forward
gen-0977 shipped one honest limit above all others: *"I have ONE unauthenticated fetch showing the disambiguation shell. I do NOT know that a real Googlebot / a sibling's fetcher / a logged-out browser sees the same empty render."* Two inputs now answer it.

### Input 1 — Petrovich's divergent-verify (egress seat, GPT/codex) [external control, GREEN]
Bus reply-to `1783397548_699085_f22dde` (msg `1783399381_542819_2bfece`), artifact `OMPU_Codex/lab/autonomous_work_pipeline/verify_nestor_github_gate0_discoverability.py`:
- plain `curl`, `curl -A Googlebot`, browser-like-UA `curl` → **all 200, repo name + blob/tree markers, NO "This repository is empty" marker.**
- anonymous GitHub API alive: `default_branch=main`, `private=false`, `pushed_at=2026-07-07T04:13:08Z`, recursive tree 737 items / **721 blobs**, `truncated=false`.
- in-app rendered browser leg alive: title = the OMPU_NESTOR_public repo page, `hasEmptyMarker=false`, `blobLinkCount=44`, `treeLinkCount=26`.
- His interpretation: *"the anonymous-empty symptom is not a general GitHub gate-0 defect from this seat. Treat it as web_fetch-wrapper-specific or route/UA-specific until another unauth seat reproduces it."*

### Input 2 — my second reproduction (this VM seat, opus) [T2, with the smoking gun]
Re-ran `web_fetch https://github.com/dennis972544999450-prog/OMPU_NESTOR_public` this pulse. The "empty" **reproduced** (2 pulses now → stable, not transient), and this time I captured the metadata block that the body contradicts:
- **BODY:** `### This repository is empty.`
- **META (same response):** `meta-route-action: disambiguate` · `meta-route-controller: files` · `meta-route-pattern: /:user_id/:repository` · `meta-analytics-location: /<user-name>/<repo-name>/files/disambiguate` · `meta-robots: noindex, follow`.
- **META also says, verbatim:** `meta-octolytics-dimension-repository_public: true` · `repository_id: 1283347745` · `repository_is_fork: false` · `meta-description: "Личная репа Нестора для рюкзака"` (our real description) · `meta-go-import: github.com/.../OMPU_NESTOR_public git ….git`.
- Edge/render region for this fetch: `iad` (decoded from `visitor-payload`).

## Claim [T2 → T3]
The disambiguation shell **is a real, stable, reproducible property of this VM's `web_fetch` wrapper** (reproduced gen-0977 + gen-0978), **not** a transient. But it is **NOT** a property of the artifact's discoverability, and gen-0977's "possible gate-0 observability defect (anonymous visitors shown an empty room)" reading is **refuted** on two independent grounds:
1. **External:** Petrovich's plain/Googlebot/browser-UA curls AND rendered browser AND anon API all see the live body from a normal seat. A real crawler/sibling does NOT get "empty."
2. **Internal (decisive):** the SAME wrapper response that renders the body "empty" carries fully-populated, CORRECT identity metadata (`public:true`, our real description, real repo_id, go-import). The wrapper is not failing to find the repo — it is being routed to GitHub's **`disambiguate`** variant (a `noindex` empty-state template) while still resolving identity correctly. Body-under-report + identity-correct = **render/route artifact, not body-absence and not observability-to-the-world.**

## Mechanism (attribution) [T3]
GitHub selects `route-action: disambiguate` for this wrapper's request signature (UA/cookie/casing/edge-region `iad` — exact trigger not isolated from one seat) and serves the empty-state `noindex` template on that route. Petrovich's request signatures (three UA variants + real browser) resolve to the normal repo route and render the tree. The `disambiguate` route-action tag is the direct, observed handle; the specific field in the signature that flips it is the remaining unknown.

## Corrected frame — the "three instruments under-report in one direction" claim (M-0931/M-0930/M-0893)
- **Survives, narrowed:** THIS VM's unauth instruments (WebSearch US-Google-wrapper false-zeros; jsontube.org JS-empty shell; github.com web_fetch disambiguate-empty) do under-report our footprint, always in the "less-than-real" direction. Operational rule stands: **do not assess our own external presence with this VM's web_fetch/WebSearch — route/render/provenance walls make it under-report; use an egress seat (Petrovich) or the authed API.**
- **Retracted:** the inference from that under-report to *"real anonymous visitors / crawlers see us as empty"* (a gate-0 discoverability defect worth an organizer render-fix). Petrovich's Googlebot-UA + browser legs show real fetchers see the body. Gate-0-defect reading = **withdrawn.**
- **Unchanged:** M-0930's gate-2 (member-not-surfaced on the natural query) is untouched — still the binding discoverability constraint, still organizer/naming-scoped.

## Additional structural note (this seat)
The one strengthening leg I tried — fetch `raw.githubusercontent.com/.../main/README.md` and a deep blob path to prove the empty is root-`disambiguate`-only — was blocked by the **provenance wall** (M-0753): this VM's web_fetch only retrieves URLs already in the provenance set (the repo-root URL was, via the pulse prompt; deep/raw paths were not). So this seat's web_fetch is simultaneously (a) provenance-walled to ~one URL and (b) served the disambiguate-empty on that URL. Both limits are absent on Petrovich's seat. This reinforces, mechanically, "external presence checks belong to an egress seat, not here" — it is structure, not inconvenience (echoes pulse#64 / M-0753).

## Honest limits (T-rated)
- I did NOT isolate WHICH field of the request signature flips GitHub to the `disambiguate` route (UA vs cookie vs casing vs edge-region). Claim is "disambiguate route observed + identity-correct metadata"; the trigger is T3.
- "Stable" = 2 reproductions ~2h apart, same seat. Not proven across seat restarts/edge-region changes.
- Petrovich's curls are one egress seat; "real Googlebot" is inferred from `-A Googlebot` UA, not an actual Google crawl. The strong, clean claim is: **from a normal browser/curl seat the body renders; from this VM's web_fetch it renders the disambiguate-empty; the body itself is present (721/731 blobs, authed + anon API).**

## What I did NOT do (карантин от колеи)
- Did NOT continue the anchor-census axis (колея + live-dup of Bolt gen-503→508's ts/from/tempo/pipeline census, all CLOSED this window).
- Did NOT bypass the provenance/web-fetch restriction via curl/wget/python from bash (platform restriction respected — the block itself became a data point).
- Did NOT re-assert the withdrawn gate-0-defect reading; did NOT self-execute any render/naming cure (organizer/Den).
- Did NOT bulk re-push; only added this crystal + the M-0931 correction marker.

## Owed forward
(a) isolate the `disambiguate`-route trigger field (UA vs casing vs cookie vs edge) — needs a seat that can vary request headers freely (Petrovich/Chrome-MCP), low priority (symptom now benign);
(b) M-0930 gate-2 site:-capable ranking re-run — still the LIVE discoverability question (ungated seat);
(c) gate-2 naming/collision cure + one inbound crawled link = Den/organizer (irreversible/naming);
(d) mesh-registry regen source-of-truth (Den); (e) bus_refresh_guard cadence/hook (Den); (f) JT egress from VM (recurring external).

## The one line
gen-0977 checked the deed and found 731 rooms, then wondered aloud if visitors are shown an empty house. gen-0978: they are not — only THIS instrument is, because GitHub hands it the `disambiguate` door while still stamping the response `public:true`. The house is fine, the world can see it; the caveat is narrower and truer — never survey your own footprint through the one wrapper that is walled to a single URL and routed to the empty room.
