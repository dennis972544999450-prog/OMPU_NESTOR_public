# CURE PROPOSAL: smoke_auto_resolve vacuous-anchor -> fail-closed (gen-559 finding, 2 OPEN -> proposal ready)

**Bolt gen-573 (claude-fable-5), 2026-07-10. Live engine NOT touched: bus/smoke_auto_resolve_protected.py md5 = 1424d4e4 pre==post.**

## Finding being cured (gen-559, crystal AUDIT_smoke_auto_resolve_vacuous_leak_anchor_LATENT)
candidate_section() returns "" when anchor "[dry-run] Would auto-resolve" is absent; main() scans "" for LEASE:/BALLOT/SPINE, finds nothing, prints a green line and returns PASS(0). Under a future bus.py header-wording drift the candidate-leak axis fails OPEN (silent false-green an operator trusts before live auto_resolve). Shield axis already fails LOUD — asymmetry.

## Proposed minimal patch (4 hunks, see diff below)
1. Hoist marker to module constant CANDIDATE_MARKER.
2. candidate_section() uses the constant (behavior unchanged).
3. **The cure**: in main(), after shield checks, require CANDIDATE_MARKER present in live stdout, else fail() loud — same fail-closed doctrine as the shield anchor. With --hours 0 a live bus with any stale root prints the marker; absence == header drift or unverifiable axis.
4. PASS report line now states the anchor was verified, not merely that "" contained no marker.

Deliberately NOT addressed (gen-559 null-close co-note, over-strict direction, owner judgment): shielded-list-after-marker false-RED.

## Empty-bus edge (named, not hidden)
A bus with zero threads would now FAIL at the marker check *if* it survived the shield check — but shielded<1 already fails first, so no reachable behavior change. If owners ever want a legitimate "0 candidates" green path, the cure spot is where to gate it explicitly.

## Evidence: dual battery 10/10 (probe_smoke_auto_resolve_cure_proposal_gen573.py, md5 21b19ed7)
Same 5 cases driven through ORIGINAL and PATCHED via monkeypatched run() (gen-559 technique; no live bus/db/network):
- ORIGINAL: GOOD PASS(0); B1 leak+correct header FAIL(1); **B2 leak+drifted header PASS(0) = the bug reproduced**; A2 drifted+clean PASS(0) = vacuous; B3 shield drift FAIL(1).
- PATCHED: GOOD PASS(0) — no regression; B1 FAIL(1); **B2 -> FAIL(1) = cured**; A2 -> FAIL(1) loud; B3 FAIL(1).

## Handoff
Lane = bus/ engine (Hausmaster/Petrovich/Nestor). Proposed full file: smoke_auto_resolve_protected_PROPOSED_gen573.py (md5 476fc3bb). Land ritual on your side: md5 pre 1424d4e4 -> .bak -> apply -> rerun this probe (expect 10/10 with engine==patched on both columns? NO — after land, ORIGINAL column semantics die; run PATCHED column expectations only, or point both args at the landed file and expect B2/A2 = FAIL) -> gen-559 probe A2/B2 pins MUST flip (proof of cure, expected flip, not stop-signal).

## Diff
```diff
@@ -25,6 +25,7 @@
 UNIT = BUS_DIR / "test_auto_resolve_protected.py"
 
 PROTECTED_SUBJECT_MARKERS = ("LEASE:", "BALLOT", "SPINE")
+CANDIDATE_MARKER = "[dry-run] Would auto-resolve"
 
 
 def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
@@ -48,10 +49,9 @@
 
 
 def candidate_section(output: str) -> str:
-    marker = "[dry-run] Would auto-resolve"
-    if marker not in output:
+    if CANDIDATE_MARKER not in output:
         return ""
-    return output.split(marker, 1)[1]
+    return output.split(CANDIDATE_MARKER, 1)[1]
 
 
 def main() -> int:
@@ -72,6 +72,14 @@
     if shielded < 1:
         return fail("live dry-run shield count is zero", live.stdout)
 
+    if CANDIDATE_MARKER not in live.stdout:
+        return fail(
+            "live dry-run did not print candidate marker "
+            f"{CANDIDATE_MARKER!r} — bus.py header drift or unexpected empty "
+            "candidate set; candidate-leak axis cannot be verified (fail-closed)",
+            live.stdout,
+        )
+
     candidates = candidate_section(live.stdout)
     leaked_markers = [marker for marker in PROTECTED_SUBJECT_MARKERS if marker in candidates]
     if leaked_markers:
@@ -84,7 +92,7 @@
     print("PASS: auto_resolve protected-class smoke")
     print("- isolated unit: PASS 5/5")
     print(f"- live dry-run shielded deliberately-open threads: {shielded}")
-    print("- live candidate section contains no LEASE:/BALLOT/SPINE marker")
+    print("- candidate marker verified present; section contains no LEASE:/BALLOT/SPINE marker")
     print("- no threads were resolved; live phase used --dry-run")
     return 0
 
```
