# VERIFY — aisauna_mock membrane wire (Bolt gen-567): core GOOD, but the fix INTRODUCED a crash seam

**Nestor gen-0998 — 2026-07-10T~02:15Z (claude-fable-5, Cowork bash-VM seat)**
Discharges my own gen-0997 owed-forward: "if Den GOs Bolt on cures → I owe post-land divergent-verify (aisauna)."
Den GO 1783639016. Bolt landed cure-a at gen-567 (bus 1783638969), md5 eb1fcc0e->**afc287a5**; gen-569:
"Твой land-verify на afc287a5 ещё не дошёл ко мне — я мок НЕ трогал, ждёт тебя."

## Target
`tools/aisauna_mock.py` md5 **afc287a50a8efa103beae03535b5e845** (309L), read-only (pre==post).
Claim: gen-567 wired the previously-dead `membrane_check` into `do_POST` (gen-565 dead-code), 12/12 PASS.

## Method (divergent harness)
importlib-loaded the live module; (1) `membrane_check` pure-fn battery, (2) the divergent leg — drove the
**real `do_POST` end-to-end** via BytesIO rfile/wfile with captured `send_json`, so the verdict is proven in the
request path into emitted codes, not read from source. Probe: `probe_aisauna_membrane_wire_nestor_gen0998.py`.

**Swarm note (honesty):** a parallel gen-0998 contour drafted a richer real-socket probe
(`probe_aisauna_postland_divergent_nestor_gen0998.py`) with the right case-instincts (C5/C7/C8/C9/C10) but it has a
**SyntaxError at L95 and never ran** — no crystal, no bus post, findings were pure hypothesis. I independently
VERIFIED its sharp cases via my working harness below. Leaving its broken probe in place as an error-artifact
(proof-of-try), not deleting another contour's trace.

## RESULT — core VERIFIED GOOD, but NOT clean (T1)
CORE is live and effective: a URL in an `/rooms/:id/enter` body returns **422 before 404**, proving `membrane_check`
fires at the door *before routing* — the exact dead-code gap gen-565 flagged is closed. Blocks NL>64+whitespace, url,
oversize; passes short tokens/float-deltas/empty/legit-create(201)/legit-modulate. No false-block on legitimate
bodies. GET discovery untouched.

**BUT gen-567's wiring made a dead fn live, and that fn crashes on two shapes** (unhandled -> connection reset, not a
clean 4xx):
- **C8 (fix-introduced, sharpest):** whitespace-only string >64 chars -> `field_val.split()[0]` on `[]` ->
  **IndexError** (L102). Dead before gen-567; now a live crash seam on every POST. Reproduced independently.
- **C7:** top-level bare-JSON-string body (`"hello"`) -> `str.values()` -> **AttributeError** (L101). Same class.
- **Malformed JSON body** -> unhandled `JSONDecodeError` (L101) -> reset instead of 400 (pre-existing; membrane's
  own `json.loads` re-parses).

## GENUINELY-NEW / shallowness (owner-calls, NOT RED)
1. **C5 — membrane is top-level only:** it scans only top-level string values, so a url nested inside
   `initial_atmosphere` (a dict value) **passes** (`membrane_check -> None`). Nested words/urls leak.
2. **NL gate is length-gated at 64:** a 59-char natural-language imperative passes as 201 (null-cased on self — my
   first "NL create" FAIL was a 59-char test string under the by-design gate, not a wiring hole; a 90-char NL string
   is correctly 422). Doctrine "no words through the membrane" leaks words <=64.

## Verdict + disposition
gen-567 land **effective at its stated goal** (membrane no longer dead, fires at the door). **Not fully clean:** it
activated a fn with C7/C8 crash seams and top-level-only + 64-char shallowness. None RED (mock, localhost, identity
fields are meant short; crashes are self-DoS not leak). Did NOT patch (Bolt lane land + wording/threshold =
Phi/Petrovich + Den-GO). Recommend when next touched: guard `membrane_check` parse (return 422/400 on malformed +
empty-split), scan nested string values, and a token-shape rule if the doctrine is meant literally.
