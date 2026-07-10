#!/usr/bin/env python3
"""
probe_redteam_infoblock_write_contract_gen606.py
Bolt gen-606. Red-team the DEPLOYED infoblock/validate.py against the smuggle-surface
of Petrovich's proposed external write-contract (RFC 1783685264_669191_8bca72).

Method: copy live validate.py to a mkdtemp, patch its hardcoded INFOBLOCK_DIR to a
mkdtemp fixture dir, write adversarial candidate blocks + one malformed control, run
the real validator's validate() over them, record pass/fail per block.

NO live data touched. live validate.py md5 recorded pre/post.
"""
import sys, os, hashlib, tempfile, shutil, importlib.util, io, re, contextlib
from pathlib import Path

sys.dont_write_bytecode = True

LIVE = Path("/sessions/sweet-sleepy-carson/mnt/OMPU_shared/infoblock/validate.py")

def md5(p): return hashlib.md5(Path(p).read_bytes()).hexdigest()

live_pre = md5(LIVE)
print(f"live validate.py md5 PRE  = {live_pre}")

work = Path(tempfile.mkdtemp(prefix="redteam_gen606_"))
fixture = work / "infoblock"
blocks = fixture / "blocks"
blocks.mkdir(parents=True)

# --- adversarial + control candidate blocks -----------------------------------
# All use a valid iid pattern filename: {iid_s}_{iid_ms:03d}_{iid_seq:03d}.md
def block(iid_s, iid_ms, iid_seq, fm_extra, body):
    fm = (f"---\n"
          f"iid_s: {iid_s}\niid_ms: {iid_ms}\niid_seq: {iid_seq}\n"
          f"{fm_extra}"
          f"ingested_at: \"2026-07-10T12:00:00Z\"\n"
          f"---\n{body}\n")
    name = f"{iid_s}_{iid_ms:03d}_{iid_seq:03d}.md"
    (blocks / name).write_text(fm)
    return name

# A. SYNTHETIC CITATION — fabricated paper, fake DOI/OpenAlex, dressed as observation
A = block(1900000001, 1, 1,
    'source_id: "S-FAKE-A-openalex-W9999999999"\n'
    'content_type: observation\nera: current\ntemperature: T0\n',
    "## Finding\nModel calibration improves 41% under edge-temperature gating.\n"
    "## Evidence Span\nsource: 'Vorland & Ng 2025, Nature Machine Intelligence' doi:10.1038/s99999-025-99999-9 openalex:W9999999999 — 'we observe a 41% ECE reduction'\n"
    "(NOTE: this paper does not exist)")

# B. THEORY-AS-OBSERVATION — pure speculation, claimed empirical content_type
B = block(1900000002, 1, 1,
    'source_id: "S-THEORY-B"\n'
    'content_type: observation\nera: current\ntemperature: T0\n',
    "## Finding\nConsciousness emerges from the second derivative of edge temperature.\n"
    "## Method\nIntrospective reflection during a long session.\n"
    "## Results\nFeels true. Very coherent.")

# C. FORBIDDEN GROUNDING EDGE — empirical block deriving FROM a speculative one
C = block(1900000003, 1, 1,
    'source_id: "S-EDGE-C"\n'
    'content_type: claim\nera: current\ntemperature: T0\n'
    'edges:\n'
    '  - derives_from: "M-SPECULATIVE-9000"\n'
    '  - supports: "M-2211"\n',
    "## Finding\nCache locality is the substrate of intelligence.\n"
    "This empirical claim is GROUNDED IN a speculative block (forbidden direction).")

# D. SOCIAL-PROOF INJECTION — consensus/replication asserted, unverifiable span
D = block(1900000004, 1, 1,
    'source_id: "S-SOCIAL-D"\n'
    'content_type: synthesis\nera: current\ntemperature: T1\n',
    "## Finding\nIt is now widely replicated and consensus among leading labs that swarms outperform single agents.\n"
    "## Evidence Span\nsource: 'many researchers agree' — no locator")

# CONTROL — malformed: missing required field content_type + bad era (falsifier for P4)
name_ctrl = f"1900000005_001_001.md"
(blocks / name_ctrl).write_text(
    "---\niid_s: 1900000005\niid_ms: 1\niid_seq: 1\n"
    "source_id: \"S-CONTROL\"\nera: nonsense_era\ningested_at: \"2026-07-10T12:00:00Z\"\n---\n"
    "## missing content_type, bad era\n")

adversarial = {"A_synthetic_citation": A, "B_theory_as_observation": B,
               "C_forbidden_edge": C, "D_social_proof": D}
control = {"E_malformed_control": name_ctrl}

# --- load the LIVE validator from a copy, patched path -------------------------
copy = work / "validate_copy.py"
src = LIVE.read_text()
patched = re.sub(r'INFOBLOCK_DIR\s*=\s*Path\([^)]*\)',
                 f'INFOBLOCK_DIR = Path(r"{fixture}")', src, count=1)
assert str(fixture) in patched, "path patch failed"
copy.write_text(patched)

spec = importlib.util.spec_from_file_location("validate_copy", copy)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# validate() prints a report and returns True iff errors==0 across ALL blocks in dir.
# To attribute pass/fail per block, run the validator with ONE block present at a time.
def run_one(fname):
    # isolate: temp dir with only this file
    solo = work / ("solo_" + fname.replace(".md",""))
    (solo / "infoblock" / "blocks").mkdir(parents=True, exist_ok=True)
    sb = solo / "infoblock" / "blocks"
    shutil.copy(blocks / fname, sb / fname)
    # patch a fresh copy pointed at solo
    c2 = solo / "v.py"
    c2.write_text(re.sub(r'INFOBLOCK_DIR\s*=\s*Path\([^)]*\)',
                         f'INFOBLOCK_DIR = Path(r"{solo/"infoblock"}")', src, count=1))
    s2 = importlib.util.spec_from_file_location("v_"+fname, c2)
    m2 = importlib.util.module_from_spec(s2)
    s2.loader.exec_module(m2)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = m2.validate()   # True == zero errors
    out = buf.getvalue()
    errcount = 0
    m = re.search(r'Errors \((\d+)\)', out)
    if m: errcount = int(m.group(1))
    return ok, errcount, out

print("\n=== ADVERSARIAL (expect PASS = smuggled through schema stage) ===")
results = {}
for label, fname in adversarial.items():
    ok, errs, _ = run_one(fname)
    results[label] = ok
    print(f"  {label:28s} -> {'PASS (smuggled)' if ok else 'REJECTED'}  errors={errs}")

print("\n=== CONTROL (expect REJECTED = validator is live/discriminating) ===")
for label, fname in control.items():
    ok, errs, _ = run_one(fname)
    results[label] = ok
    print(f"  {label:28s} -> {'PASS' if ok else 'REJECTED'}  errors={errs}")

# --- verdict against locked predictions ---------------------------------------
print("\n=== VERDICT vs LOCKED PREDICTIONS ===")
p1 = all(results[k] for k in adversarial)
p4 = (results["E_malformed_control"] is False)
print(f"P1 all 4 adversarial PASS: {p1}")
print(f"P4 malformed control REJECTED: {p4}")
print(f"P2/P3 structural (by code inspection): validate.py has no source_id dereference "
      f"and skips edge list items -> synthetic citation + forbidden edge invisible.")

live_post = md5(LIVE)
print(f"\nlive validate.py md5 POST = {live_post}  (== PRE: {live_pre==live_post})")
shutil.rmtree(work, ignore_errors=True)
print("cleanup done")
