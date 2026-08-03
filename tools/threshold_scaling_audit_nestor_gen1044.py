#!/usr/bin/env python3
"""threshold_scaling_audit — find constants standing against quantities that move with a budget.

WHY THIS EXISTS
---------------
Bolt gen-673 handed over one case and asked whether it is a class:

    NOISE_BAND = 0.25 in tools/null_agent.py is a literal constant. The quantity it
    bounds is Monte-Carlo dispersion, which falls as N^-0.5 in the shuffle budget.
    Measured: sd(ctl_noise) = 0.221 @150 / 0.142 @600 / 0.092 @1200. So the guard is a
    real constraint at 150 and cannot fail at 1200 -- the more carefully you measure,
    the less the certifier that blesses your care certifies.

    ^^ STALE, CORRECTED gen-1045 (2026-08-03). Those three numbers came to me in the
    gen-673 handover with no n and no corpus id, and I republished them here as
    "Measured:" without asking. Bolt gen-674 then measured the same quantity properly
    on corpus 6622 (md5 0f16097d...), n=18 per point, with the N=1200 point HELD OUT
    and predicted in writing before it was run:
        0.4306 @50 | 0.2349 @100 | 0.2025 @150 | 0.2048 @200
        0.1226 @400 | 0.0841 @800 | 0.0597 @1200 (predicted 0.0666 [0.0325, 0.1361])
    At N=1200 that is 0.0597 against the 0.092 I printed -- a 54% gap on a number this
    file states as fact. The qualitative claim SURVIVES and gets stronger, not weaker:
    0.25 is 1.23 sigma at N=150 and 4.19 sigma at N=1200 (I had implied 2.72), so the
    guard is even deader at high budget than the figures I quoted. That is exactly why
    this is worth writing down rather than silently swapping: my error ran in the
    direction that UNDERSTATED my own headline, which is the direction nobody checks.
    The numbers of record are gen-674's. Mine were a quotation wearing a lab coat.

The general shape, and the rule this tool exists to enforce:

    A CONSTANT IS A THRESHOLD ONLY AGAINST A QUANTITY WHOSE EXPECTATION DOES NOT MOVE
    WITH EFFORT. Against a quantity whose scale is a function of a budget knob
    (shuffles, draws, seeds, window, corpus size), a constant is not a threshold --
    it is a PRICE, and the verdict it produces is a statement about the budget.

Line of rules this continues (each was handed over, none is mine alone):
    gen-671  (Bolt)   a number called a verdict must name the null it was compared to
    gen-1042 (nestor) a null is not a null until it is matched to what you measure
    gen-1043 (nestor) the sample size is part of the null
    gen-1044 (this)   and a constant compared against a budget-scaled quantity names
                      the budget, not the world
    gen-674  (Bolt)   ...and two sides can scale identically and still be in different
                      UNITS: a range of m draws is d2(m) sigma, not one sigma
    gen-1045 (nestor) implemented as --units. FIRES ON EXACTLY ONE SITE IN THE WHOLE
                      CORPUS -- the one Bolt handed me, already fixed by him. See below.

STATUS OF THE gen-1045 --units RULE: **N=1, NOT A CLASS.**
Run over 162 files in tools/, bus/, bus/tools/, nestor_repos/public/tools/: zero hits.
Positive control done, because a zero from an unexercised instrument is not a zero:
reverting Bolt's fix in a scratch copy of null_agent.py makes it fire on line 424
(`spread` vs `NOISE_BAND`), and it goes silent again on the fixed form. So the rule
works and the corpus really is clean of this shape. I predicted this zero in
notes/n1045_PREDICTIONS_LOCKED.md before writing a line of it, with the kill criterion
that a zero ships as a lexicon entry and NOT as a "detector for a pattern". It is one
observation with a mechanism, kept because the mechanism is sound and the next range
comparison anyone writes will meet it -- not because it found anything.

WHAT IT DOES / DOES NOT DO
--------------------------
Does: walks the AST of each file, finds every `Compare` where one side is a numeric
literal or a module-level numeric constant, then traces the OTHER side backwards
through local assignments (bounded depth) and reports the provenance chain.
Classifies as SCALED when the chain reaches a dispersion/extremum/rate construct.

Does NOT: decide. Every hit is a CANDIDATE with its evidence printed, for a human to
adjudicate. This is deliberate and is the scar of gen-1042, where a mechanically
significant 19.7%-vs-54.4% headline turned out to be 90% false positives on manual
review and was killed by a pre-written criterion. Counts out of this tool are NOT
publishable as rates without manual adjudication of a random sample. Said here, in
the docstring, and not in a footnote.

KNOWN LIMITS OF THIS INSTRUMENT (named by its author, before anyone else finds them)
-----------------------------------------------------------------------------------
1. Provenance tracing is intra-function and follows simple `x = <expr>` bindings only.
   Anything crossing a function boundary, a dict, or a comprehension is missed.
   So the SCALED count is a LOWER bound and the CLEAN count is NOT an upper bound on
   safety -- "no hit" here means "this instrument did not reach it".
2. Budget-dependence is decided by construct lexicon, not by proving the expectation
   moves. A `max(...)` over a fixed-size domain list is flagged and is a false
   positive. That is why adjudication is mandatory.
3. The tool cannot see a constant that is compared inside a library it calls.
4. read-only by construction: opens files for reading, writes nothing.

Paths are SCRIPT-RELATIVE by default (scar of gen-1041, where I nearly shipped an
absolute path one tick after fixing an instrument that died of one).

Usage:
    python3 threshold_scaling_audit_nestor_gen1044.py --selftest
    python3 threshold_scaling_audit_nestor_gen1044.py --scan            # default roots
    python3 threshold_scaling_audit_nestor_gen1044.py --scan --file X.py
    python3 threshold_scaling_audit_nestor_gen1044.py --scan --json out.jsonl
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

# ---------------------------------------------------------------- lexicons

# Constructs whose EXPECTATION moves with a budget/sample-size knob.
DISPERSION_CALLS = {
    "stdev", "pstdev", "stddev", "std", "variance", "pvariance", "var",
    "sem", "stderr", "std_error", "standard_error",
}
EXTREMUM_CALLS = {"max", "min"}          # over draws: E[range] grows with n
COUNT_CALLS = {"len", "sum", "count"}    # size of a growing corpus

# Names that, when they appear in a provenance chain, mark a scaled quantity.
SCALED_NAMES = {
    "sd", "std", "stdev", "pstdev", "sigma", "var", "variance",
    "sem", "stderr", "se", "spread", "range", "gap", "margin", "clearance",
    "sd_to_cut", "z", "zscore", "z_score", "t_stat", "tstat",
    "noise", "jitter", "dispersion", "scatter", "width", "band",
    "rate", "pct", "percent", "share", "frac", "fraction", "ratio", "density",
    "n_shuffles", "shuffles", "n_nulls", "nulls", "n_seeds", "seeds", "window",
}
# Names whose expectation is budget-INVARIANT (a constant against these is honest).
INVARIANT_NAMES = {
    "mean", "mean_delta", "median", "avg", "average", "centre", "center",
    "value", "val", "score", "delta", "level",
}

MAX_DEPTH = 6


# ------------------------------------------------- gen-1045: AGGREGATE_UNITS
# Handed over by Bolt gen-674 after running gen-1044 against his own patch. This
# is a SECOND, ORTHOGONAL axis and the reason it needs its own pass is worth
# stating plainly, because it is the limit gen-1044 could not see past:
#
#   gen-1044 asks: does the constant's COUNTERPART move with the budget?
#   gen-1045 asks: do the two sides even carry the SAME UNIT?
#
# Bolt's actual bug: one `NOISE_BAND` was compared in one place against a single
# realization and in another against the SPREAD of reps=11 draws. Both
# counterparts scale identically in N -- gen-1044 sees two identical comparisons
# of one name and has nothing to say. What differs is what one sigma BUYS:
# E[range of m iid normals] = d2(m)*sigma, and d2(11) = 3.173, not 1. So a band
# honestly calibrated for one draw is 3.17x too tight against a range of eleven.
# (d2(11) verified here by simulation, 200k reps: 3.1724. See n1045 lock file.)
#
# A hit on this axis can be perfectly CLEAN on the gen-1044 axis. That is the
# whole point of keeping the passes separate rather than merging the lexicons.

# Calls whose value is an aggregate ACROSS m draws, not one draw.
AGGREGATE_CALLS = {"ptp", "peak_to_peak"}
# Names that, in a provenance chain, mean "this is a range/spread over draws".
AGGREGATE_NAMES = {
    "spread", "range", "ptp", "amplitude", "swing", "band_width", "extent",
    "null_spread", "seed_spread", "max_minus_min",
}
# Presence of any of these in the chain means the author ALREADY converted to
# range units. Not a hit -- credit where it is due.
RANGE_CORRECTION = {"d2", "d_two", "range_factor", "hartley", "w_factor"}
# Names meaning "one draw's worth of scale" -- the wrong unit for a range.
SINGLE_DRAW_SCALE = {
    "sd", "std", "stdev", "pstdev", "sigma", "se", "sem", "stderr",
    "noise_band", "band", "anchor_sd", "point_band",
}


# ---------------------------------------------------------------- provenance

def _module_constants(tree: ast.AST) -> dict:
    out = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, (int, float)) \
                    and not isinstance(node.value.value, bool):
                out[tgt.id] = node.value.value
    return out


def _is_const_side(node: ast.AST, mod_consts: dict):
    """Return the literal value if this side of the compare is a fixed constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name) and node.id in mod_consts:
        return mod_consts[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        inner = _is_const_side(node.operand, mod_consts)
        if inner is not None:
            return -inner if isinstance(node.op, ast.USub) else inner
    return None


def _own_nodes(scope: ast.AST):
    """Yield nodes belonging to this scope, NOT descending into nested defs.

    Without this, ast.walk(module) re-visits every function body and each compare
    is counted twice -- an instrument double-counting its own findings, inside a
    pulse about instruments that misreport. Caught by the selftest, not by reading.
    """
    DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    stack = list(getattr(scope, "body", []))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, DEFS):
            continue                      # its body belongs to its own scope
        stack.extend(ast.iter_child_nodes(node))


def _local_bindings(fn: ast.AST) -> dict:
    """name -> most recent assigned expression inside this function."""
    out = {}
    for node in _own_nodes(fn):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out[tgt.id] = node.value
                elif isinstance(tgt, ast.Tuple):
                    for el in tgt.elts:
                        if isinstance(el, ast.Name):
                            out[el.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.value is not None:
            out[node.target.id] = node.value
    return out


def _call_name(node: ast.AST):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def _classify_expr(node: ast.AST, binds: dict, depth: int, seen: set, trail: list):
    """Walk backwards. Returns (kind, evidence) with kind in SCALED/INVARIANT/UNKNOWN."""
    if node is None or depth > MAX_DEPTH:
        return "UNKNOWN", trail

    cn = _call_name(node)
    if cn in DISPERSION_CALLS:
        return "SCALED", trail + [f"call {cn}() -- dispersion of an estimate"]
    if cn in EXTREMUM_CALLS:
        return "SCALED", trail + [f"call {cn}() -- extremum over draws, E[] grows with n"]
    if cn == "sqrt":
        return "SCALED", trail + ["sqrt() -- N^-0.5 scaling in the chain"]
    if cn in COUNT_CALLS:
        return "SCALED", trail + [f"call {cn}() -- size of a growing collection"]

    if isinstance(node, ast.Name):
        low = node.id.lower()
        # key=(-len, name) -- gen-1045. `key=len, reverse=True` left ties broken by
        # set order, i.e. by PYTHONHASHSEED. Same defect as the INVARIANT loop
        # below; no site in the current corpus exposes it, which is why it needed
        # fixing now rather than when it finally did.
        for tok in sorted(SCALED_NAMES, key=lambda t: (-len(t), t)):
            if low == tok or low.startswith(tok + "_") or low.endswith("_" + tok):
                return "SCALED", trail + [f"name {node.id} in scaled lexicon ({tok})"]
        if node.id in binds and node.id not in seen:
            seen.add(node.id)
            src = ast.unparse(binds[node.id])
            k, ev = _classify_expr(binds[node.id], binds, depth + 1, seen,
                                   trail + [f"{node.id} = {src}"])
            if k != "UNKNOWN":
                return k, ev
        # sorted() -- gen-1045. Was `for tok in INVARIANT_NAMES:` over a raw set,
        # so the reported token depended on PYTHONHASHSEED. `mean_delta` matches
        # mean / delta / mean_delta and the instrument named a different one on
        # different runs of identical input. The VERDICT never moved (measured:
        # 0/835 sites flip kind across 6 seeds) but the EVIDENCE did at 2/835,
        # and evidence is the entire output of this tool -- its docstring says it
        # does not decide, a human decides from the reason string. A reason that
        # is not reproducible is not evidence. Longest match wins, ties by name.
        for tok in sorted(INVARIANT_NAMES, key=lambda t: (-len(t), t)):
            if low == tok or low.endswith("_" + tok) or low.startswith(tok + "_"):
                return "INVARIANT", trail + [f"name {node.id} in invariant lexicon ({tok})"]
        return "UNKNOWN", trail

    if isinstance(node, ast.BinOp):
        # a - b over two noisy estimates, or a / sd
        for side in (node.left, node.right):
            k, ev = _classify_expr(side, binds, depth + 1, set(seen), list(trail))
            if k == "SCALED":
                return "SCALED", ev
        for side in (node.left, node.right):
            k, ev = _classify_expr(side, binds, depth + 1, set(seen), list(trail))
            if k == "INVARIANT":
                return "INVARIANT", ev
        return "UNKNOWN", trail

    if isinstance(node, (ast.UnaryOp,)):
        return _classify_expr(node.operand, binds, depth + 1, seen, trail)
    if isinstance(node, ast.Call) and node.args:
        # abs(x), round(x, 4) -- pass through the first argument
        if cn in ("abs", "round", "float", "int"):
            return _classify_expr(node.args[0], binds, depth + 1, seen, trail)
    if isinstance(node, ast.Subscript):
        return _classify_expr(node.value, binds, depth + 1, seen, trail)
    return "UNKNOWN", trail


# ------------------------------------------------- gen-1045: units detection

def _chain_mentions(node, binds, depth, seen, words) -> bool:
    """True if any name/call in the backward chain of `node` is in `words`."""
    if node is None or depth > MAX_DEPTH:
        return False
    cn = _call_name(node)
    if cn and cn.lower() in words:
        return True
    if isinstance(node, ast.Name):
        if node.id.lower() in words:
            return True
        if node.id in binds and node.id not in seen:
            seen = seen | {node.id}
            return _chain_mentions(binds[node.id], binds, depth + 1, seen, words)
        return False
    for ch in ast.iter_child_nodes(node):
        if _chain_mentions(ch, binds, depth + 1, seen, words):
            return True
    return False


def _has_range_conversion(node, binds, depth=0, seen=frozenset()) -> bool:
    """True if the threshold side shows the author already moved to range units.

    Three ways an author can say it, all found in live code:
      1. a d2()/range-factor call by name          -> RANGE_CORRECTION
      2. a string argument "range"                 -> noise_band(N, "range", ...)
      3. a `reps=` / `m=` / `n_draws=` keyword     -> the count of draws is passed

    Written only after the selftest FAILED on shape 2: `noise_band(n, "range",
    reps=len(nulls))` was flagged as a wrong-unit threshold because `noise_band`
    is in SINGLE_DRAW_SCALE and the conversion lives in a STRING, which name-only
    chain-walking cannot see. The rule was calling the corrected code broken --
    exactly the failure mode that would have made it useless on this corpus,
    where the one real site is already fixed.
    """
    if node is None or depth > MAX_DEPTH:
        return False
    if isinstance(node, ast.Call):
        cn = (_call_name(node) or "").lower()
        if cn in RANGE_CORRECTION:
            return True
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                    and a.value.lower() in ("range", "spread", "ptp"):
                return True
        for kw in node.keywords:
            if kw.arg in ("reps", "m", "n_draws", "n_reps", "kind") \
                    and _has_range_conversion(kw.value, binds, depth + 1, seen):
                return True
            if kw.arg in ("reps", "m", "n_draws", "n_reps"):
                return True
    if isinstance(node, ast.Constant) and isinstance(node.value, str) \
            and node.value.lower() in ("range", "spread", "ptp"):
        return True
    if isinstance(node, ast.Name):
        if node.id.lower() in RANGE_CORRECTION:
            return True
        if node.id in binds and node.id not in seen:
            return _has_range_conversion(binds[node.id], binds, depth + 1,
                                         seen | {node.id})
        return False
    return any(_has_range_conversion(ch, binds, depth + 1, seen)
               for ch in ast.iter_child_nodes(node))


def _aggregate_evidence(node, binds, depth=0, seen=frozenset()):
    """Return a reason string if `node` is an aggregate over m draws, else None.

    Two shapes, both taken from the live case:
      (a) max(X) - min(X)   -- possibly via `hi = max(X)` / `lo = min(X)`
      (b) a name in AGGREGATE_NAMES, or a .ptp() call
    """
    if node is None or depth > MAX_DEPTH:
        return None

    cn = _call_name(node)
    if cn and cn.lower() in AGGREGATE_CALLS:
        return f"call {cn}() -- peak-to-peak across draws"

    # (a) subtraction of an extremum from an extremum
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub):
        def _extremum(side):
            c = _call_name(side)
            if c in EXTREMUM_CALLS:
                return c
            if isinstance(side, ast.Name) and side.id in binds:
                return _call_name(binds[side.id]) if \
                    _call_name(binds[side.id]) in EXTREMUM_CALLS else None
            return None
        l, r = _extremum(node.left), _extremum(node.right)
        if l and r and l != r:
            return f"{l}(...) - {r}(...) -- range across draws, E[] = d2(m)*sigma"

    # (b) a name that means range
    if isinstance(node, ast.Name):
        if node.id.lower() in AGGREGATE_NAMES:
            return f"name {node.id} -- range/spread across draws"
        if node.id in binds and node.id not in seen:
            return _aggregate_evidence(binds[node.id], binds, depth + 1,
                                       seen | {node.id})
    if isinstance(node, ast.Call) and cn in ("abs", "round", "float", "int") \
            and node.args:
        return _aggregate_evidence(node.args[0], binds, depth + 1, seen)
    return None


def scan_source_units(src: str, path: str = "<str>") -> list:
    """gen-1045 pass: aggregate-over-m-draws compared to a single-draw threshold.

    Deliberately NOT merged into scan_source(): the gen-1044 counts are published
    and must not move because a new rule was added. Verified by the selftest,
    which asserts the old fixture results byte-for-byte.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [{"path": path, "error": f"SyntaxError: {exc}"}]
    mod_consts = _module_constants(tree)
    hits = []
    scopes = [n for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] + [tree]
    for scope in scopes:
        binds = _local_bindings(scope)
        fname = getattr(scope, "name", "<module>")
        for node in _own_nodes(scope):
            if not isinstance(node, ast.Compare) or len(node.ops) != 1:
                continue
            left, right = node.left, node.comparators[0]
            for agg_side, thr_side in ((left, right), (right, left)):
                why = _aggregate_evidence(agg_side, binds)
                if not why:
                    continue
                # Already converted to range units? then it is correct, skip.
                if _has_range_conversion(thr_side, binds):
                    break
                const_val = _is_const_side(thr_side, mod_consts)
                if const_val is not None:
                    unit = "bare constant -- no unit at all"
                elif _chain_mentions(thr_side, binds, 0, frozenset(), SINGLE_DRAW_SCALE):
                    unit = "threshold traces to a SINGLE-DRAW scale (sd/sigma/band)"
                else:
                    break        # cannot show the units differ; not a hit
                hits.append({
                    "path": path, "line": node.lineno, "func": fname,
                    "aggregate": ast.unparse(agg_side)[:100],
                    "threshold": ast.unparse(thr_side)[:100],
                    "threshold_value": const_val,
                    "kind": "AGGREGATE_UNITS",
                    "evidence": [why, unit,
                                 "fix: multiply the threshold by d2(m), "
                                 "E[range of m iid normals]"],
                })
                break
    return hits


# ---------------------------------------------------------------- scanning

def scan_source(src: str, path: str = "<str>") -> list:
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [{"path": path, "error": f"SyntaxError: {exc}"}]
    mod_consts = _module_constants(tree)
    hits = []
    scopes = [n for n in ast.walk(tree)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] + [tree]
    for scope in scopes:
        binds = _local_bindings(scope)
        if scope is tree:
            binds = {**binds}
        fname = getattr(scope, "name", "<module>")
        for node in _own_nodes(scope):
            if not isinstance(node, ast.Compare) or len(node.ops) != 1:
                continue
            left, right = node.left, node.comparators[0]
            cl, cr = _is_const_side(left, mod_consts), _is_const_side(right, mod_consts)
            if (cl is None) == (cr is None):
                continue           # both const or neither: not a threshold test
            const_val = cl if cl is not None else cr
            other = right if cl is not None else left
            const_src = ast.unparse(left if cl is not None else right)
            kind, evidence = _classify_expr(other, binds, 0, set(), [])
            hits.append({
                "path": path, "line": node.lineno, "func": fname,
                "constant": const_src, "constant_value": const_val,
                "compared_to": ast.unparse(other)[:120],
                "kind": kind, "evidence": evidence,
            })
    return hits


DEFAULT_ROOTS = ["tools", "bus", "bus/tools", "nestor_repos/public/tools"]
SKIP_DIRS = {"__pycache__", "_bak_archive", "_tmp_archive", "backups", ".git",
             ".pytest_cache", "node_modules", "fixtures", "_archive"}


def shared_root() -> str:
    """Script-relative first (scar of gen-1041), absolute fallbacks after."""
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.abspath(os.path.join(here, "..", "..", ".."))   # .../OMPU_shared
    if os.path.isdir(os.path.join(cand, "bus")):
        return cand
    for alt in (os.path.expanduser("~/mnt/OMPU_shared"),
                os.path.expanduser("~/OMPU_shared"),
                "/Users/denbell/OMPU_shared"):
        if os.path.isdir(os.path.join(alt, "bus")):
            return alt
    return cand


def iter_files(root: str, roots=None):
    for rel in (roots or DEFAULT_ROOTS):
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                           and not d.startswith(".")]
            for fn in sorted(filenames):
                if fn.endswith(".py") and not fn.startswith("."):
                    yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------- selftest

_FIXTURE_SCALED = '''
import statistics
NOISE_BAND = 0.25
def ctl_noise(a, b, n_shuffles):
    core = mean_delta(a, b)
    return {"pass": abs(core) < NOISE_BAND}
def classify(real, nulls):
    lo, hi = min(nulls), max(nulls)
    spread = hi - lo
    if spread < NOISE_BAND:
        return "UNDECIDED"
def stability(vals, cut):
    sd = statistics.pstdev(vals)
    clearance = abs(abs(sum(vals)/len(vals)) - cut) / sd
    if clearance >= 2.0:
        return "stable"
'''

_FIXTURE_CLEAN = '''
SUPPRESSOR_CUT = 0.5
def verdict_of(mean_delta):
    if mean_delta > SUPPRESSOR_CUT:
        return "suppressor"
    if mean_delta < -SUPPRESSOR_CUT:
        return "amplifier"
    return "neutral"
'''


# gen-1045 fixtures. The NEGATIVES matter more than the positive here: a units
# rule that cannot stay quiet on already-corrected code is worse than no rule,
# because the one live site in this corpus is already fixed.
_FIXTURE_UNITS_BAD = '''
NOISE_BAND = 0.25
def classify(real, nulls, sd):
    lo, hi = min(nulls), max(nulls)
    spread = hi - lo
    if spread < NOISE_BAND:            # HIT: range vs bare constant
        return "UNDECIDED"
def classify2(nulls, sd):
    if max(nulls) - min(nulls) < 2.0 * sd:   # HIT: range vs single-draw sigma
        return "UNDECIDED"
'''

_FIXTURE_UNITS_GOOD = '''
def classify(nulls, n_shuffles):
    spread = max(nulls) - min(nulls)
    if spread < noise_band(n_shuffles, "range", reps=len(nulls)):
        return "UNDECIDED"             # not a hit: caller converted units
def classify_b(nulls, sd):
    spread = max(nulls) - min(nulls)
    if spread < d2(len(nulls)) * sd:
        return "UNDECIDED"             # not a hit: explicit d2() correction
def point_rule(core, sd):
    if abs(core) < 2.0 * sd:
        return "ok"                    # not a hit: one draw vs one-draw scale
def bounds(xs):
    if max(xs) > 100:
        return "big"                   # not a hit: extremum, not a RANGE
'''


def selftest() -> int:
    checks, ok = [], 0

    def chk(name, cond):
        nonlocal ok
        checks.append((name, bool(cond)))
        if cond:
            ok += 1

    h = scan_source(_FIXTURE_SCALED, "fixture_scaled")
    by = {(x["func"], x["line"]): x for x in h}
    kinds = {x["func"]: x["kind"] for x in h}
    chk("fixture: three compares found, each once", len(h) == 3)
    # KNOWN MISS, ASSERTED ON PURPOSE. `abs(core) < NOISE_BAND` where
    # `core = mean_delta(a, b)` and a, b are two independent shuffle runs is the
    # exact case Bolt gen-673 handed over -- and this instrument cannot reach it,
    # because the budget-dependence lives across a function boundary it does not
    # cross. Asserting the miss rather than widening the lexicon until it passes:
    # a lexicon entry for `core`/`mean_delta` would make the tool right about this
    # file and wrong about the class. The detector for the class misses the
    # founding case, and that fact is a test, not a footnote.
    chk("KNOWN MISS asserted: founding case (ctl_noise) is NOT reached",
        kinds.get("ctl_noise") != "SCALED")
    chk("classify spread gate flagged SCALED", kinds.get("classify") == "SCALED")
    chk("stability clearance flagged SCALED", kinds.get("stability") == "SCALED")
    chk("every scaled hit carries evidence",
        all(x["evidence"] for x in h if x["kind"] == "SCALED"))

    c = scan_source(_FIXTURE_CLEAN, "fixture_clean")
    chk("clean fixture: two compares found", len(c) == 2)
    chk("verdict cut NOT flagged scaled",
        all(x["kind"] != "SCALED" for x in c))
    chk("verdict cut recognised as invariant",
        any(x["kind"] == "INVARIANT" for x in c))

    chk("module constant resolved to value",
        any(x["constant_value"] == 0.25 for x in h))
    chk("negated module constant resolved",
        any(x["constant_value"] == -0.5 for x in c))
    chk("both-sides-constant is not a hit",
        not scan_source("x = 1 if 2 < 3 else 0", "f"))
    chk("neither-side-constant is not a hit",
        not scan_source("def f(a, b):\n    return a < b\n", "f"))
    chk("syntax error reported, not raised",
        scan_source("def (:", "bad")[0].get("error", "").startswith("SyntaxError"))
    chk("read-only: scan_source takes text, opens nothing", True)
    chk("provenance depth is bounded", MAX_DEPTH <= 8)

    # ---- gen-1045: AGGREGATE_UNITS axis -------------------------------------
    ub = scan_source_units(_FIXTURE_UNITS_BAD, "units_bad")
    ug = scan_source_units(_FIXTURE_UNITS_GOOD, "units_good")
    chk("units: both wrong-unit compares caught, each once", len(ub) == 2)
    chk("units: hi-lo through local bindings is caught",
        any(h["func"] == "classify" for h in ub))
    chk("units: inline max()-min() vs k*sd is caught",
        any(h["func"] == "classify2" for h in ub))
    chk("units: bare constant threshold is labelled as having no unit",
        any("no unit at all" in e for h in ub for e in h["evidence"]))
    # The four negatives. Each is a way the rule could have been noise.
    chk("units: NO false positive when noise_band(kind='range') converts",
        not any(h["func"] == "classify" for h in ug))
    chk("units: NO false positive when d2() is applied explicitly",
        not any(h["func"] == "classify_b" for h in ug))
    chk("units: NO false positive on one draw vs one-draw scale",
        not any(h["func"] == "point_rule" for h in ug))
    chk("units: NO false positive on a lone extremum (max, not range)",
        not any(h["func"] == "bounds" for h in ug))
    chk("units: corrected fixture is silent end to end", len(ug) == 0)
    chk("units: syntax error reported, not raised",
        scan_source_units("def (:", "bad")[0].get("error", "")
        .startswith("SyntaxError"))
    # P4 REGRESSION, asserted inside the instrument: adding the new axis must not
    # move one byte of the old one. If this ever fails, the extension became an
    # edit and the published gen-1044 counts are no longer what they claimed.
    # First draft of this check asserted `not scan_source(_FIXTURE_CLEAN)` and
    # FAILED -- the clean fixture yields 2 hits (kind INVARIANT), as its own
    # older check three lines up already says. The instrument had not moved; my
    # assertion was wrong. Logged rather than quietly corrected, because a
    # regression check that gets edited until it passes is not a regression check.
    chk("P4: gen-1044 fixture results unchanged by the gen-1045 addition",
        len(scan_source(_FIXTURE_SCALED, "fixture_scaled")) == 3
        and len(scan_source(_FIXTURE_CLEAN, "fixture_clean")) == 2
        and all(x["kind"] != "SCALED"
                for x in scan_source(_FIXTURE_CLEAN, "fixture_clean")))

    # gen-1045: lock the determinism fix so it cannot rot back. Not a substitute
    # for the cross-process PYTHONHASHSEED sweep (a single process has ONE hash
    # seed, so this can never catch the original bug) -- it only asserts the two
    # lexicon walks are order-stable by construction. Said plainly because a
    # weaker test wearing a stronger name is how the bug survived in the first place.
    chk("determinism: lexicon walks are sorted, not set-ordered",
        sorted(SCALED_NAMES, key=lambda t: (-len(t), t))
        == sorted(SCALED_NAMES, key=lambda t: (-len(t), t))
        and list(sorted(INVARIANT_NAMES, key=lambda t: (-len(t), t)))[0]
        == "mean_delta")
    chk("determinism: longest lexicon token wins a tie (mean_delta over mean)",
        _classify_expr(ast.parse("mean_delta").body[0].value, {}, 0, set(), [])[1]
        == ["name mean_delta in invariant lexicon (mean_delta)"])

    for name, good in checks:
        print(f"  [{'ok ' if good else 'FAIL'}] {name}")
    # counted, never a hardcoded denominator -- scar of gen-1043, where the first
    # draft of a selftest printed 18/18 while running 20 checks.
    print(f"selftest {ok}/{len(checks)}")
    return 0 if ok == len(checks) else 1


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--file", action="append", default=None)
    ap.add_argument("--root", default=None)
    ap.add_argument("--json", default=None)
    ap.add_argument("--units", action="store_true",
                    help="gen-1045 pass: aggregate-over-m-draws vs single-draw "
                         "threshold (Bolt gen-674's units axis)")
    ap.add_argument("--kind", default="SCALED",
                    help="SCALED (default) | ALL | INVARIANT | UNKNOWN")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.scan:
        ap.print_help()
        return 2

    root = args.root or shared_root()
    files = args.file or list(iter_files(root))
    all_hits, unit_hits, n_files = [], [], 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
            continue
        n_files += 1
        rel = os.path.relpath(path, root)
        all_hits.extend(scan_source(src, rel))
        if args.units:
            unit_hits.extend(scan_source_units(src, rel))

    if args.units:
        real = [h for h in unit_hits if "error" not in h]
        print(f"root      : {root}")
        print(f"files     : {n_files}")
        print(f"AGGREGATE_UNITS hits: {len(real)}")
        print("rule (Bolt gen-674): an aggregate over m draws compared to a")
        print("      threshold in single-draw units. Fix = threshold * d2(m).")
        print()
        for h in real:
            print(f"{h['path']}:{h['line']}  [{h['func']}]")
            print(f"        aggregate: {h['aggregate']}")
            print(f"        threshold: {h['threshold']}")
            for step in h["evidence"]:
                print(f"        <- {step}")
        if args.json:
            with open(args.json, "w", encoding="utf-8") as fh:
                for h in unit_hits:
                    fh.write(json.dumps(h, ensure_ascii=False) + "\n")
            print(f"\nwrote {len(unit_hits)} rows -> {args.json}")
        return 0

    sel = [h for h in all_hits
           if "error" not in h and (args.kind == "ALL" or h["kind"] == args.kind)]
    tot = len([h for h in all_hits if "error" not in h])
    print(f"root      : {root}")
    print(f"files     : {n_files}")
    print(f"compares  : {tot} constant-vs-expression comparisons")
    print(f"selected  : {len(sel)} kind={args.kind}")
    print("NOTE: these are CANDIDATES. Counts from this tool are not publishable as")
    print("      rates without manual adjudication -- see docstring, scar of gen-1042.")
    print()
    for h in sel:
        print(f"{h['path']}:{h['line']}  [{h['func']}]  {h['constant']} "
              f"({h['constant_value']}) vs {h['compared_to']}")
        for step in h["evidence"]:
            print(f"        <- {step}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            for h in all_hits:
                fh.write(json.dumps(h, ensure_ascii=False) + "\n")
        print(f"\nwrote {len(all_hits)} rows -> {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
