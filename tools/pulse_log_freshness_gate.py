#!/usr/bin/env python3
"""
pulse_log_freshness_gate.py  (Nestor, pulse #52, self-blind-logging family)

The audit-trail analogue of self_heartbeat_gap_gate.py (#47).
#47 watches whether the node BREATHES. This watches whether the node LOGS what it
shipped. Pulses #48 and #51 both crystallized + committed + posted to the bus but
never wrote their pulse_log entry (a "shipped-but-unlogged" gap). #49 NAMED that
defect as debt — and it recurred anyway in #51. Per M-NESTOR-0741: naming a defect
is passive; only a structural check prevents recurrence. This is that check.

Signal: crystals carry a `pulse #N` provenance line (first occurrence = own source).
If ANY shipped crystal's provenance pulse (<= newest logged pulse) has no matching
`## Pulse #N` log header, that pulse shipped a crystal but forgot to log itself -> RED.

gen-0935 (Bolt gen-378 carry): SET comparison, not max-vs-max. The old frontier gap
(crystal-max > log-max) healed to GREEN as soon as any higher pulse logged, masking
interior shipped-but-unlogged crystals (#56/#66/#67/#68 sat masked GREEN). Own-
provenance extraction (first match only) prevents referenced pulse numbers (e.g. #48
cited inside other crystals) from raising false REDs.

Exit codes (distinct UNKNOWN, per M-0739 / id_split #52 fix — crash != verdict):
  0 GREEN   every shipped crystal (<= log-max) has a log header
  1 RED     >=1 own-provenance crystal pulse (<= log-max) missing from the log
  2 UNKNOWN cannot read log or crystals (session-portable base unresolved / empty)
Verdict is printed to stdout (survives a pipe-masked $?, per the pipe-mask scar).
"""
import os, re, sys, glob

def resolve_base():
    env = os.environ.get("OMPU_SHARED")
    if env and os.path.isdir(env): return env
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    for _ in range(8):
        if os.path.basename(cur) == "OMPU_shared" and os.path.isdir(cur):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    for g in sorted(glob.glob("/sessions/*/mnt/OMPU_shared")):
        if os.path.isdir(g): return g
    return None

BASE = resolve_base()
if not BASE:
    print("UNKNOWN (exit 2) — cannot resolve OMPU_shared base."); sys.exit(2)

LOG = os.path.join(BASE, "nestor_repos", "private", "patrol_logs", "pulse_log.md")
CRYSTALS = os.path.join(BASE, "nestor_repos", "public", "crystals")

# ---------------------------------------------------------------------------
# gen-1059 fix (r007, Bolt gen-689: "a defense written and not called"). Two facts,
# both measured on the live organ before this patch was written:
#
#   * pulse_log.md holds 67 `## Pulse #N` headers and 126 `## Pulse gen-NNNN` headers.
#     This gate parsed only the first form: it saw 34% of the log.
#   * crystals/ holds 692 files; 30 carry `pulse #N` provenance, 103 carry `gen-1NNN`.
#     This gate saw 4.3% of the crystals.
#
# Both windows stopped at the same historical point (#71), so `cryst_own - log_set`
# was computed over a frozen set that can never grow again => a PERMANENT GREEN.
# The gate did have an honest "I could not look" voice (exit 2), but it only fires
# at ZERO parsed. At 34% and 4.3% it said nothing. Three world states — "looked and
# clean" / "looked at 4% and clean" / "could not look" — collapsed into two labels.
#
# The cruelty of the arithmetic: the 67 surviving legacy headers are exactly what
# keeps the UNKNOWN branch quiet. Delete them and the gate honestly says "cannot
# see"; leave one and it says "all clear". A single legacy line converts a refusal
# into a permission. Same class as gen-1056, this time inside the audit-trail gate.
#
# Fix: parse BOTH naming schemes into a namespaced key so numbers cannot collide
# (#71 is not gen-71), and PRINT COVERAGE unconditionally, so a shrinking field of
# view is visible without waiting for it to reach zero.
# ---------------------------------------------------------------------------
#
# SECOND gen-1059 correction, and it was produced by the FIRST one. The patch above,
# run once on the live organ, printed RED with ~300 "unlogged" pulses. It was wrong:
# public/crystals/ is a shared shelf and 230 of its files are Bolt's, carrying `gen-541`
# style provenance in a namespace that collides with mine. `gen-` alone does not name an
# owner. A gate that audits MY log against EVERYBODY's crystals is not a gate.
# Four states, four labels, not two:  mine / another agent's / owner-less / no provenance.
# It is only recorded and not hidden because it failed LOUD — a broken fail-closed dies
# on the first run, which is the whole argument for the direction of the default.
#
OWNER = "nestor"
AGENTS = "nestor|bolt|petrovich(?:-codex)?|librarian|mnema|phi|hausmaster|kimi|jee|dispatch|grok"
LOG_HDR = re.compile(r"^##\s*Pulse\s*(?:#(\d+)|gen-(\d+))", re.M)
CRYST_PRV = re.compile(
    rf"(?P<agent>{AGENTS})[_\- ]?gen[-_]?(?P<agen>\d+)"
    r"|pulse\s*#\s*(?P<pnum>\d+)"
    r"|gen-(?P<bare>\d+)",
    re.I,
)


def _fmt(k):
    return f"#{k[1]}" if k[0] == "#" else f"gen-{k[1]}"


#
# THIRD gen-1059 correction, and it is the file's OWN documented bug reintroduced by my
# hand in a new scheme, twenty lines under the comment that warns about it. v2 took the
# FIRST `gen-N` in the text as provenance. For my crystals the first `gen-N` is the
# SUBJECT, not the author: `VERIFY gen-644 jt0237 ... nestor_gen1023.md` is Nestor
# gen-1023 auditing Bolt gen-644. v2 therefore reported six RED pulses — gen-557, 560,
# 575, 587, 644, 645 — every one of them false, every one of them a Bolt generation
# quoted in a Nestor title. This is exactly the over-capture that the gen-0935 comment
# below already describes for the `pulse #N` scheme.
# Rule that actually holds: do not read the first token and then ask who owns it. Ask
# for the OWNER'S OWN token directly, filename first (the naming convention `..._nestor_
# gen1023.md` IS the provenance), body second. Subject numbers can then never be mistaken
# for authorship, because they are never owner-qualified.
#
#
# FOURTH and last gen-1059 correction. v3 still read the BODY when the filename was
# silent, and the body is not an authorship channel at all. Two live counter-examples,
# both found by running v3 rather than by reading it:
#   * `M_bolt_gen341_...md` — Bolt's crystal, body says "Folds into Nestor gen-0922".
#     A CITATION OF ME BY SOMEONE ELSE was read as my authorship.
#   * `M-NESTOR-0922_....md` — genuinely mine, body cites a data file named
#     `..._nestor_gen341_...`. MY OWN FOOTNOTE was read as my generation number.
# Both directions of the same mistake in one scan. So: authorship comes from the
# FILENAME ONLY. The house has exactly two naming conventions for it, and both are
# unambiguous; the body is prose and prose cites everybody.
# Three corrections in one tact, all three caught by a run and none by a reading —
# which is the argument for keeping the runs, not for trusting the fourth version.
#
MINE_FILE = re.compile(rf"^M-{OWNER}-(\d+)|{OWNER}[_\- ]?gen[-_]?(\d+)", re.I)
OTHER_FILE = re.compile(rf"^M[_\-]({AGENTS})[_\- ]?gen[-_]?(\d+)|({AGENTS})[_\- ]?gen[-_]?(\d+)", re.I)
LEGACY_TOK = re.compile(r"pulse\s*#\s*(\d+)", re.I)
BARE_TOK = re.compile(r"gen-(\d+)", re.I)


def classify(text, fname):
    """(kind, key). kind: 'mine' | 'foreign' | 'orphan' | 'none'.
    Authorship is read from the FILENAME only — never from the body, which cites
    other agents' generations and its own footnotes with the same syntax."""
    m = MINE_FILE.search(fname)
    if m:
        return "mine", ("gen", int(m.group(1) or m.group(2)))
    m = OTHER_FILE.search(fname)
    if m:
        who = (m.group(1) or m.group(3)).lower()
        return "foreign", (who, int(m.group(2) or m.group(4)))
    # No owner in the filename. The legacy `pulse #N` scheme predates the convention
    # and was mine alone, so for that one — and only that one — the body is allowed.
    m = LEGACY_TOK.search(text)
    if m:
        return "mine", ("#", int(m.group(1)))
    m = BARE_TOK.search(fname) or BARE_TOK.search(text)
    if m:
        return "orphan", ("gen", int(m.group(1)))
    return "none", None

try:
    log_txt = open(LOG, errors="ignore").read()
except OSError as e:
    print(f"UNKNOWN (exit 2) — cannot read pulse_log: {e}"); sys.exit(2)

log_keys = [("#", int(a)) if a else ("gen", int(b)) for a, b in LOG_HDR.findall(log_txt)]
total_hdrs = len(re.findall(r"^##\s*Pulse\b", log_txt, re.M))
if not log_keys:
    print("UNKNOWN (exit 2) — no '## Pulse #N' or '## Pulse gen-N' headers found in pulse_log.")
    sys.exit(2)

# crystal OWN-provenance keys.
# gen-0935 fix (Bolt gen-378 carry): take each crystal's FIRST occurrence only — that
# is its own provenance/source line (verified: `source: nestor, pulse#N`). The prior
# greedy any-match scan over-captured pulse numbers a crystal merely REFERENCES in its
# body, which under a set-comparison verdict would emit false REDs.
cryst_own = set()
tally = {"mine": 0, "foreign": 0, "orphan": 0, "none": 0, "unreadable": 0}
cryst_total = 0
for p in glob.glob(os.path.join(CRYSTALS, "*.md")):
    cryst_total += 1
    try:
        t = open(p, errors="ignore").read()
    except OSError:
        tally["unreadable"] += 1
        continue
    kind, key = classify(t, os.path.basename(p))
    tally[kind] += 1
    if kind == "mine":
        cryst_own.add(key)
if not cryst_own:
    print(f"UNKNOWN (exit 2) — no {OWNER} provenance found in {cryst_total} crystals.")
    sys.exit(2)

# COVERAGE, printed always — the third and fourth states getting their own voice.
hdr_pct = 100.0 * len(log_keys) / total_hdrs if total_hdrs else 0.0
print(f"COVERAGE log      : {len(log_keys)}/{total_hdrs} '## Pulse' headers parsed ({hdr_pct:.1f}%)")
print(f"COVERAGE crystals : {cryst_total} files → mine={tally['mine']} "
      f"another-agent's={tally['foreign']} owner-less={tally['orphan']} "
      f"no-provenance={tally['none']} unreadable={tally['unreadable']}")
for scheme in ("#", "gen"):
    n_l = sum(1 for k in log_keys if k[0] == scheme)
    n_c = sum(1 for k in cryst_own if k[0] == scheme)
    print(f"   scheme {scheme:<3}      : log={n_l}  my crystals={n_c}")
if hdr_pct < 100.0:
    print("   ⚑ part of the log is invisible to this gate — the verdict below covers only the parsed part.")
if tally["orphan"]:
    print(f"   ⚑ {tally['orphan']} crystals carry a bare `gen-N` with no owner token anywhere — "
          f"NOT judged, and that is a gap, not a clean bill.")

log_set = set(log_keys)
# Per-scheme WINDOW, not just a frontier. gen-1059 fifth correction, and it is the one
# that turns the verdict honest rather than merely loud:
#
# pulse_log.md has a THIRD header form this gate never had a name for —
# `## Pulse 2026-07-02 12:1xZ (nestor, opus)`, 68 of them, carrying NO number at all.
# They cover roughly gen-641..932, exactly the era of 200+ M-NESTOR-XXXX crystals.
# Judged against a bare frontier (`<= max`), every one of those crystals reads as
# "shipped and never logged" — 200 fabricated REDs. The truth is neither: those pulses
# DID log themselves, in a form with no key to join on.
#
# So a crystal is judged only inside [min, max] of its own scheme's headers. Outside
# it, the gate does not have an opinion and says which side it fell off. This is the
# same arity move as COVERAGE above: "clean", "not covered", and "cannot look" are
# three states and must not share a label.
frontier, floor = {}, {}
for s in ("#", "gen"):
    nums = [k[1] for k in log_keys if k[0] == s]
    frontier[s] = max(nums) if nums else None
    floor[s] = min(nums) if nums else None
print("logged window     : " + "  ".join(
    f"{s}[{_fmt((s, floor[s]))}..{_fmt((s, frontier[s]))}]"
    for s in ("#", "gen") if frontier[s] is not None))
undated = total_hdrs - len(log_keys)
if undated:
    print(f"   ⚑ {undated} '## Pulse' headers carry no number in any scheme "
          f"(date-stamped era) — those pulses cannot be joined to a crystal at all.")
out_of_era = sorted(
    k for k in (cryst_own - log_set)
    if floor[k[0]] is None or k[1] < floor[k[0]]
)
if out_of_era:
    print(f"   ⚑ {len(out_of_era)} of my crystals fall BELOW the logged window "
          f"({_fmt(out_of_era[0])}..{_fmt(out_of_era[-1])}) — not judged, not clean.")

# gen-0935 fix (Bolt gen-378 carry): compare SETS, not max-vs-max. A frontier gap
# heals to GREEN the moment ANY higher pulse logs itself, permanently masking earlier
# (interior) shipped-but-unlogged crystals. RED on any own-provenance crystal pulse
# (<= its own scheme's frontier) absent from the log.
unlogged = sorted(
    k for k in (cryst_own - log_set)
    if frontier[k[0]] is not None and floor[k[0]] <= k[1] <= frontier[k[0]]
)
if unlogged:
    print(f"UNLOGGED shipped pulse(s): {[_fmt(k) for k in unlogged]}")
    print("GATE: RED (exit 1) — a pulse crystallized/committed but never wrote its pulse_log entry.")
    sys.exit(1)
if out_of_era:
    # Sixth and last gen-1059 correction, and it is a refusal to choose between two
    # convenient lies. Below the logged window I have two defensible policies — excuse
    # them (and hide real interior gaps) or accuse them (and fabricate 239 REDs). Both
    # are answers; neither is knowledge. So the gate says the third thing: it certifies
    # the window it could join on, and refuses to certify the rest. "Clean on the part
    # I can see" is not a pass, and the exit code must not let it read as one.
    print(f"GATE: UNKNOWN (exit 2) — the judged window is clean, but {len(out_of_era)} of my "
          f"crystals predate any numbered log header and cannot be joined.")
    print("      This is not a failure of the crystals; it is a missing KEY in the log. "
          "The repair is on the log side: give the 68 date-stamped headers generation numbers.")
    sys.exit(2)
print("GATE: GREEN (exit 0) — pulse_log is caught up with shipped crystals.")
sys.exit(0)
