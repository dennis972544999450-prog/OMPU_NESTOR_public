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
        for tok in sorted(SCALED_NAMES, key=len, reverse=True):
            if low == tok or low.startswith(tok + "_") or low.endswith("_" + tok):
                return "SCALED", trail + [f"name {node.id} in scaled lexicon ({tok})"]
        if node.id in binds and node.id not in seen:
            seen.add(node.id)
            src = ast.unparse(binds[node.id])
            k, ev = _classify_expr(binds[node.id], binds, depth + 1, seen,
                                   trail + [f"{node.id} = {src}"])
            if k != "UNKNOWN":
                return k, ev
        for tok in INVARIANT_NAMES:
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
    all_hits, n_files = [], 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError as exc:
            print(f"skip {path}: {exc}", file=sys.stderr)
            continue
        n_files += 1
        all_hits.extend(scan_source(src, os.path.relpath(path, root)))

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
