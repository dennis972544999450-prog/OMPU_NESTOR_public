#!/usr/bin/env python3
"""
absence_audit — nestor gen-1042

Detects the form: **absence of measurement arrives dressed as the best possible
result.** Three confirmed instances in one week (median-gap n/a where value was
0.0; AgentLiveness.phi=0.0 for unknown; nan -> "neutral"), three authors, none
looking. This asks mechanically whether that is a class or an anecdote.

It reports NOT a verdict but a verdict AND ITS NULL (Bolt gen-671's rule):
the null here is ordinary defensive programming, estimated from INTERNAL sites
(fallbacks that never surface) against PUBLISHED sites (fallbacks a reader will
believe). Class is real only if PUBLISHED skews benign MORE than INTERNAL.

read-only. Never writes to the scanned tree.

KNOWN DEFECTS, gen-1042, unfixed and left for the next hand:
  1. T2 does not check nan REACHABILITY. It flags a float cascade's `else` as a
     nan-landing site without proving nan can arrive. Confirmed FP:
     bus_analyzer.py:411 — resolve_rate is `round(a/b,3) if b>0 else 0.0`,
     guarded, never nan. A nan-detector that does not check nan is this tool's
     own instance of the form it hunts.
  2. NUM_NAME is a name regex and lies. Confirmed FP: agent_card_audit_v0_1.py:163
     `pct or ""` where pct is a content-type STRING. Dataflow wins when present;
     the regex only fires when dataflow is silent, and then it guesses.

DO NOT publish population shares from this tool without hand-review. gen-1042
round 1 returned PUBLISHED 19.7% vs INTERNAL 54.4% (p<1e-30-looking, stable,
reproducible) — and 90% of the PUBLISHED population was `"PASS" if ok else "FAIL"`,
a correct idiom. The number was fine; the referent was wrong. Use --strict, then
read every surviving site by hand. The output is a LIST, not a RATE.
"""
import ast, os, sys, json, re, argparse
from collections import Counter

STRICT_ONLY = False
HERE = os.path.dirname(os.path.abspath(__file__))
# script-relative first (gen-1041 scar: absolute paths with rotating session
# names die silently), absolute as fallback only.
def default_root():
    for cand in (os.path.abspath(os.path.join(HERE, "..", "..", "..")),
                 os.path.abspath(os.path.join(HERE, "..", "..")),
                 os.environ.get("OMPU_SHARED", "")):
        if cand and os.path.isdir(os.path.join(cand, "bus")):
            return cand
    return os.path.abspath(os.path.join(HERE, "..", ".."))

SKIP = ("/site-packages/", "/venv/", "/.venv/", "/.git/", "/__pycache__/",
        "/node_modules/", "/.mypy_cache/")

SILENCE = {"neutral","ok","okay","fine","green","pass","passed","healthy","alive",
           "normal","good","clean","none","no_change","nochange","stable","quiet",
           "unchanged","valid","success","live","active","up","0","n/a","na","-",
           "unknown_ok","skip","skipped","noop","idle","safe","clear","nominal"}
RAISE_ = {"stale","dead","gray","grey","red","fail","failed","error","err","warn",
          "warning","critical","crit","suppressor","amplifier","uncomputed","unknown",
          "missing","broken","degraded","alert","danger","invalid","down","drift",
          "anomaly","suspect","no_data","nodata","unmeasured","undefined","abort"}

PUB_KEY = re.compile(r"(verdict|label|status|state|score|phi|health|liveness|"
                     r"result|summary|report|rate|count|median|mean|metric|"
                     r"grade|level|signal|flag|tempo|diversity|delta|sigma|z)",
                     re.I)


NUM_CALLS = {"len","sum","round","float","int","abs","min","max","median","mean",
             "stdev","pstdev","variance","fmean","count","statistics"}
BOOL_CALLS = {"all","any","bool","isinstance","hasattr","exists","isfile","isdir",
              "startswith","endswith","match","search","fullmatch"}
BOOL_NAME = re.compile(r"(^|_)(ok|okay|passed|pass|valid|cond|clean|changed|fired|"
                       r"success|found|is_[a-z]|has_[a-z]|should|can|did|flag|"
                       r"enabled|present|matched|live|dry|verbose|quiet|force)($|_)", re.I)
NUM_NAME  = re.compile(r"(^|_)(n|count|counts|total|sum|mean|median|avg|average|rate|"
                       r"score|delta|gap|phi|size|num|len|length|idx|index|offset|pct|"
                       r"percent|width|depth|z|sigma|std|var|elapsed|secs|seconds|ms|"
                       r"bytes|lines|rows|hits|misses|errors|warnings)($|_)", re.I)

def _rhs_kind(v):
    """Classify an assigned expression as NUMERIC / BOOLEAN / None. Traced, not guessed."""
    if isinstance(v, ast.Constant):
        if isinstance(v.value, bool): return "BOOLEAN"
        if isinstance(v.value, (int, float)): return "NUMERIC"
        return None
    if isinstance(v, (ast.Compare, ast.BoolOp)): return "BOOLEAN"
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not): return "BOOLEAN"
    if isinstance(v, ast.BinOp) and isinstance(v.op, (ast.Add, ast.Sub, ast.Mult,
            ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)): return "NUMERIC"
    if isinstance(v, ast.Call):
        nm = getattr(v.func, "id", None) or getattr(v.func, "attr", None) or ""
        if nm in BOOL_CALLS: return "BOOLEAN"
        if nm in NUM_CALLS:  return "NUMERIC"
    if isinstance(v, ast.IfExp):
        a, b = _rhs_kind(v.body), _rhs_kind(v.orelse)
        return a if a == b else None
    return None

def numeric_probe(tree, name):
    """Does `name` hold a quantity whose 0 is a legal measurement?
    Dataflow first (assignments in this file); naming only as tiebreak."""
    if not name: return False
    kinds = set()
    for n in ast.walk(tree):
        tgts = []
        if isinstance(n, ast.Assign): tgts, val = n.targets, n.value
        elif isinstance(n, ast.AnnAssign) and n.value is not None: tgts, val = [n.target], n.value
        elif isinstance(n, ast.AugAssign): tgts, val = [n.target], n.value
        else: continue
        for t in tgts:
            tn = getattr(t, "id", None) or getattr(t, "attr", None)
            if tn == name:
                k = _rhs_kind(val)
                if k: kinds.add(k)
    if kinds == {"NUMERIC"}: return True
    if "BOOLEAN" in kinds:   return False
    if BOOL_NAME.search(name): return False
    if NUM_NAME.search(name):  return True
    return False

def seg(node, src):
    try:
        return ast.get_source_segment(src, node) or ""
    except Exception:
        return ""

def const_str(node):
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, str): return v
        if v is None: return "__NONE__"
        if isinstance(v, bool): return "__BOOL__"
        if isinstance(v, (int, float)): return "__NUM__%s" % v
    return None

def direction(fallback_node):
    """Which way does the ABSENT measurement point once it is dressed?"""
    s = const_str(fallback_node)
    if s is None:
        return "UNCLEAR", None
    if s.startswith("__NUM__"):
        return "UNCLEAR", s          # numeric: needs threshold semantics -> hand review
    if s == "__NONE__":
        return "UNCLEAR", "None"
    if s == "__BOOL__":
        return "UNCLEAR", "bool"
    key = s.strip().lower().strip("?.!:_ ")
    if key in SILENCE: return "SILENCE", s
    if key in RAISE_:  return "RAISE", s
    # multiword: any raise-word present wins (an alarm is an alarm)
    words = set(re.split(r"[^a-z0-9_]+", key))
    if words & RAISE_:  return "RAISE", s
    if words & SILENCE: return "SILENCE", s
    return "UNCLEAR", s


def _label_of(stmts):
    for st in stmts:
        v = st.value if isinstance(st, (ast.Return, ast.Assign)) else None
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            return v.value
    return None

def _reads(node, name):
    """Compare whose left side is `name` (bare or as attribute) against a number."""
    if not isinstance(node, ast.Compare) or len(node.ops) != 1: return None
    l, r = node.left, node.comparators[0]
    ln = getattr(l, "id", None) or getattr(l, "attr", None)
    if ln != name: return None
    if not (isinstance(r, ast.Constant) and isinstance(r.value, (int, float))): return None
    op = node.ops[0]
    for cls, sym in ((ast.Lt,"<"), (ast.Gt,">"), (ast.LtE,"<="), (ast.GtE,">=")):
        if isinstance(op, cls): return sym, r.value
    return None

def simulate_cascade(tree, name, value):
    """What label does an ABSENT measurement (== `value`) receive from the
    cascade that reads `name`? Walks the if/elif/else in source order, exactly
    as the interpreter would. Returns (label, n_branches) or (None, 0)."""
    import math
    for n in ast.walk(tree):
        if not isinstance(n, ast.If): continue
        r = _reads(n.test, name)
        if not r: continue
        cur, branches = n, []
        while True:
            rr = _reads(cur.test, name)
            if not rr: break
            branches.append((rr, _label_of(cur.body)))
            if cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]; continue
            else_label = _label_of(cur.orelse) if cur.orelse else None
            break
        if len(branches) < 1: continue
        if not any(lbl for _, lbl in branches): continue
        for (sym, thr), lbl in branches:
            hit = (value < thr if sym == "<" else value > thr if sym == ">"
                   else value <= thr if sym == "<=" else value >= thr)
            if hit and lbl:
                return lbl, len(branches)
        if else_label:
            return else_label, len(branches)
    return None, 0

class Scanner(ast.NodeVisitor):
    def __init__(self, path, src, tree):
        self.path, self.src, self.tree = path, src, tree
        self.sites = []
        self.fn = []
        # names printed / f-stringed / json-dumped anywhere in this file
        self.surfaced = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.JoinedStr):
                for x in ast.walk(n):
                    if isinstance(x, ast.Name): self.surfaced.add(x.id)
                    if isinstance(x, ast.Attribute): self.surfaced.add(x.attr)
            if isinstance(n, ast.Call):
                f = n.func
                nm = getattr(f, "id", None) or getattr(f, "attr", None) or ""
                if nm in ("print","dump","dumps","write","writelines","post","info",
                          "warning","error","log","format","echo"):
                    for x in ast.walk(n):
                        if isinstance(x, ast.Name): self.surfaced.add(x.id)
                        if isinstance(x, ast.Attribute): self.surfaced.add(x.attr)
            # a name used as a STRING KEY in a dict literal is on its way to a reader
            if isinstance(n, ast.Dict):
                for k in n.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        self.surfaced.add(k.value)

    # ---- helpers -------------------------------------------------------
    def target_names(self, node):
        """names this expression's value is bound to / keyed under"""
        out = []
        for p in ast.walk(self.tree):
            if isinstance(p, (ast.Assign, ast.AnnAssign)) and getattr(p, "value", None) is node:
                tg = p.targets if isinstance(p, ast.Assign) else [p.target]
                for t in tg:
                    out.append(getattr(t, "id", None) or getattr(t, "attr", None) or "")
            if isinstance(p, ast.Dict):
                for k, v in zip(p.keys, p.values):
                    if v is node and isinstance(k, ast.Constant) and isinstance(k.value, str):
                        out.append(k.value)
            if isinstance(p, ast.keyword) and p.value is node:
                out.append(p.arg or "")
            if isinstance(p, ast.Return) and p.value is node:
                out.append("__return__")
        return [o for o in out if o]

    def published(self, node, probe_names):
        for anc in ast.walk(self.tree):
            if isinstance(anc, (ast.JoinedStr,)) and node in ast.walk(anc):
                return True, "inside f-string"
            if isinstance(anc, ast.Call):
                nm = getattr(anc.func, "id", None) or getattr(anc.func, "attr", None) or ""
                if nm in ("print","dumps","dump","write","post","format","log") and node in ast.walk(anc):
                    return True, "inside %s()" % nm
        for t in self.target_names(node):
            if PUB_KEY.search(t):
                return True, "bound to '%s'" % t
        for pn in probe_names:
            if pn and pn in self.surfaced:
                return True, "'%s' surfaces (printed/keyed/dumped) in this file" % pn
        return False, ""

    def add(self, kind, node, fallback, probe_expr, probe_names, note=""):
        d, raw = direction(fallback)
        resolved_via = ""
        if d == "UNCLEAR" and isinstance(raw, str) and raw.startswith("__NUM__"):
            try: val = float(raw[7:])
            except Exception: val = None
            if val is not None:
                for nm in probe_names:
                    lbl, nb = simulate_cascade(self.tree, nm, val)
                    if lbl:
                        d2, _ = direction(ast.Constant(value=lbl))
                        if d2 != "UNCLEAR":
                            d, resolved_via = d2, "cascade(%s)->%r" % (nm, lbl)
                        break
        pub, why = self.published(node, probe_names)
        self.sites.append(dict(
            file=os.path.relpath(self.path, ROOT), line=getattr(node, "lineno", 0),
            kind=kind, func=".".join(self.fn) or "<module>",
            probe=(probe_expr or "")[:90],
            fallback=(raw if raw is not None else seg(fallback, self.src))[:60],
            direction=d, surface=("PUBLISHED" if pub else "INTERNAL"),
            why=why, note=note, resolved=resolved_via,
            code=seg(node, self.src)[:160].replace("\n", " ")))

    # ---- visitors ------------------------------------------------------
    def visit_FunctionDef(self, n):
        self.fn.append(n.name); self.generic_visit(n); self.fn.pop()
    visit_AsyncFunctionDef = visit_FunctionDef
    def visit_ClassDef(self, n):
        self.fn.append(n.name); self.generic_visit(n); self.fn.pop()

    def visit_IfExp(self, n):
        # T1: `A if X else B` with X a bare truthiness test (0 is a legal value)
        t = n.test
        if isinstance(t, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)):
            names = [getattr(t, "id", None) or getattr(t, "attr", None) or ""]
            strict = numeric_probe(self.tree, names[0]) or (
                isinstance(t, ast.Call) and (getattr(t.func,"id",None) or getattr(t.func,"attr","")) in NUM_CALLS)
            if strict or not STRICT_ONLY:
                self.add("T1_STRICT" if strict else "T1_FALSY_SWALLOW", n, n.orelse,
                         seg(t, self.src), names,
                         note="truthiness test on a QUANTITY: measured 0 is indistinguishable from absent"
                              if strict else "truthiness test (numericness unresolved)")
        self.generic_visit(n)

    def visit_BoolOp(self, n):
        # T1b: `X or FALLBACK`
        if isinstance(n.op, ast.Or) and len(n.values) == 2:
            l, r = n.values
            if isinstance(l, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)) and isinstance(r, ast.Constant):
                names = [getattr(l, "id", None) or getattr(l, "attr", None) or ""]
                strict = numeric_probe(self.tree, names[0])
                if strict or not STRICT_ONLY:
                    self.add("T1_STRICT" if strict else "T1_FALSY_SWALLOW", n, r,
                             seg(l, self.src), names,
                             note="`or` fallback on a QUANTITY: measured 0 takes the fallback"
                                  if strict else "`or` fallback (numericness unresolved)")
        self.generic_visit(n)

    def visit_If(self, n):
        # T2: float-comparison cascade ending in a labelling `else`
        def cmp_float(node):
            return (isinstance(node, ast.Compare) and
                    any(isinstance(o, (ast.Lt, ast.Gt, ast.LtE, ast.GtE)) for o in node.ops))
        if cmp_float(n.test):
            cur, depth = n, 1
            while cur.orelse and len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If) \
                  and cmp_float(cur.orelse[0].test):
                cur = cur.orelse[0]; depth += 1
            if depth >= 2 and cur.orelse:
                for st in cur.orelse:
                    val = None
                    if isinstance(st, ast.Return): val = st.value
                    elif isinstance(st, ast.Assign): val = st.value
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        probe = seg(n.test.left, self.src)
                        self.add("T2_NONFINITE_INTO_ELSE", st, val, probe, [probe],
                                 note="nan fails all %d comparisons and lands here" % depth)
        self.generic_visit(n)

    def visit_Call(self, n):
        # T3b: dict.get(key, DEFAULT) where key looks like a measurement
        f = n.func
        if isinstance(f, ast.Attribute) and f.attr == "get" and len(n.args) == 2 \
           and isinstance(n.args[1], ast.Constant):
            k = n.args[0]
            kn = k.value if isinstance(k, ast.Constant) and isinstance(k.value, str) else ""
            if kn and PUB_KEY.search(kn):
                self.add("T3_BENIGN_DEFAULT", n, n.args[1], kn, [kn],
                         note="default stands in for an absent measurement of '%s'" % kn)
        self.generic_visit(n)

    def visit_AnnAssign(self, n):
        # T3: dataclass field default for a metric-named field
        nm = getattr(n.target, "id", None) or getattr(n.target, "attr", None) or ""
        if nm and n.value is not None and isinstance(n.value, ast.Constant) and PUB_KEY.search(nm):
            self.add("T3_BENIGN_DEFAULT", n, n.value, nm, [nm],
                     note="field default; absent measurement keeps this value")
        self.generic_visit(n)

def scan(root, only=None):
    sites, files = [], 0
    for dp, dn, fn in os.walk(root):
        if any(s.strip("/") in dp.split(os.sep) for s in
               ("site-packages","venv",".venv",".git","__pycache__","node_modules")):
            continue
        for f in fn:
            if not f.endswith(".py") or ".bak" in f: continue
            p = os.path.join(dp, f)
            if any(s in p for s in SKIP): continue
            if only and only not in p: continue
            try:
                src = open(p, encoding="utf-8", errors="replace").read()
                tree = ast.parse(src)
            except Exception:
                continue
            files += 1
            sc = Scanner(p, src, tree); sc.visit(tree); sites.extend(sc.sites)
    return files, sites

def table(sites):
    pop = {}
    for s in sites:
        pop.setdefault(s["surface"], Counter())[s["direction"]] += 1
    out = {}
    for k, c in pop.items():
        d = c["SILENCE"] + c["RAISE"]
        out[k] = dict(silence=c["SILENCE"], raise_=c["RAISE"], unclear=c["UNCLEAR"],
                      decided=d, silence_share=(c["SILENCE"]/d if d else None))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    ap.add_argument("--only", default=None, help="substring filter on path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--kind", default=None)
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    STRICT_ONLY = a.strict
    ROOT = a.root or default_root()
    files, sites = scan(ROOT, a.only)
    if a.kind: sites = [s for s in sites if s["kind"].startswith(a.kind)]
    if a.json:
        print(json.dumps(dict(root=ROOT, files=files, n=len(sites),
                              by_kind=Counter(s["kind"] for s in sites),
                              populations=table(sites), sites=sites), default=str))
    else:
        print("root=%s  files=%d  sites=%d" % (ROOT, files, len(sites)))
        for k, v in sorted(Counter(s["kind"] for s in sites).items()):
            print("  %-26s %d" % (k, v))
        print("\nPOPULATIONS (silence share = benign / (benign+alarming)):")
        for k, v in sorted(table(sites).items()):
            sh = "n/a" if v["silence_share"] is None else "%.1f%%" % (100*v["silence_share"])
            print("  %-10s silence=%-4d raise=%-4d unclear=%-4d  share=%s"
                  % (k, v["silence"], v["raise_"], v["unclear"], sh))
        for s in sites[:a.show]:
            print("\n  %s:%s [%s/%s/%s] %s\n    probe=%s fallback=%r\n    %s"
                  % (s["file"], s["line"], s["kind"], s["direction"], s["surface"],
                     s["func"], s["probe"], s["fallback"], s["code"]))
