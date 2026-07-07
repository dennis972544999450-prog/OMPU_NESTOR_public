#!/usr/bin/env python3
"""
probe_driver_concept_novelty_gen532.py  —  Bolt gen-532 FAILABLE PROBE

TARGET: swarm_driver.generate_signal producer-side `concept_novelty` section
        (the last individually-unswept DRIVER_SIGNAL field besides priority_tasks;
         priority_tasks trio suppress/escalate/boost closed 529/530/531).

The docstrings of load_concept_index / query_concept_novelty call this
"the semantic deduplication GATE" (x3). This probe tests whether the
producer-side novelty channel is (a) injectable via forged authored prose,
(b) BOUNDED (cannot inject a task_id or a blocking decision the way
priority_tasks can), (c) gracefully degrading — and pairs it with a SOURCE
consumer-trace (done in the crystal) showing the field has ZERO live decision
reader (print_brief display + one unit test only), and the one effector on the
overlap axis (layer3_executive.action_publish_guard) is a SEPARATE recompute
that is explicitly NON-BLOCKING and on-demand.

METHOD (read-only, hermetic):
  * import REAL live swarm_driver via importlib (md5-gated pre==post)
  * exercise ONLY pure fns query_concept_novelty / _tokenize_simple on
    SYNTHETIC in-memory concept_index dicts
  * NEVER call main() or generate_signal (no live LOG read, no file write)
  * INDEPENDENT oracle re-derives TF-IDF cosine from the SPEC formula
    (NOT reusing module _cosine_sim) and re-derives best_novel = argmin(top_score)
  * best_novel selection logic (generate_signal L950-956) replicated locally
    over synthetic novelty_probes to prove forged-recs steer the recommendation

A case that does not match the independent oracle FAILS. No RED is invented;
GREEN means: injectable-but-bounded producer field with zero decision consumer.
"""
import importlib.util, hashlib, math, sys
from collections import Counter
from pathlib import Path

# ---- locate live module ----
BASE = None
for p in Path("/sessions").glob("*/mnt/OMPU_shared"):
    if (p / "tools" / "swarm_driver.py").exists():
        BASE = p
        break
assert BASE, "swarm_driver.py not found"
MOD_PATH = BASE / "tools" / "swarm_driver.py"

md5_pre = hashlib.md5(MOD_PATH.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location("swarm_driver_live", MOD_PATH)
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'GREEN' if cond else 'RED  '}] {name}  {detail}")

# ---------------------------------------------------------------------------
# INDEPENDENT ORACLE (re-derives from spec; does NOT call module _cosine_sim)
# ---------------------------------------------------------------------------
def oracle_qvec(query, idf):
    # mirror _tokenize_simple's r'[a-zа-яёé\-]{3,}' + stopword filter via the
    # REAL module tokenizer is fine for INPUT (tokenizer is not under test here);
    # the ARITHMETIC (tf-idf weighting + cosine + thresholds) is what we
    # independently recompute.
    toks = sd._tokenize_simple(query)
    tf = Counter(toks)
    total = sum(tf.values()) or 1
    return {t: (c / total) * idf.get(t, math.log(2)) for t, c in tf.items()}

def oracle_cos(a, b):
    if not a or not b:
        return 0.0
    dot = sum(a.get(t, 0.0) * b.get(t, 0.0) for t in set(a) | set(b))
    ma = math.sqrt(sum(v * v for v in a.values()))
    mb = math.sqrt(sum(v * v for v in b.values()))
    return 0.0 if ma == 0 or mb == 0 else dot / (ma * mb)

def oracle_novelty(query, index):
    if not index:
        return "unknown", 0.0
    idf = index.get("idf", {}); vecs = index.get("vectors", {})
    if not idf or not vecs:
        return "unknown", 0.0
    q = oracle_qvec(query, idf)
    if not q:
        return "unknown", 0.0
    scored = sorted(((d, round(oracle_cos(q, v), 4)) for d, v in vecs.items()
                     if oracle_cos(q, v) > 0), key=lambda x: -x[1])
    top = scored[0][1] if scored else 0.0
    lvl = "HIGH" if top > 0.6 else "PARTIAL" if top > 0.35 else "LOW"
    return lvl, top

# ---------------------------------------------------------------------------
# SYNTHETIC INDEX (invented tokens that survive tokenizer, avoid stopwords)
# ---------------------------------------------------------------------------
IDF = {"quantumfold": 1.0, "biofield": 1.0, "resonancer": 1.0,
       "zephyrite": 1.0, "moltencore": 1.0}
INDEX = {
    "idf": IDF,
    "vectors": {
        # doc aligned to query {quantumfold,biofield,resonancer} -> ~1.0 HIGH
        "doc_hi": {"quantumfold": 0.333, "biofield": 0.333, "resonancer": 0.333},
        # doc sharing 1 term with mixed weight -> PARTIAL band
        "doc_mid": {"quantumfold": 2.0, "moltencore": 1.0},
        # doc fully disjoint -> 0 overlap
        "doc_dis": {"zephyrite": 1.0, "moltencore": 1.0},
    },
    "doc_meta": {d: {"text_preview": d} for d in ("doc_hi", "doc_mid", "doc_dis")},
    "stats": {"documents": 3},
}

# ---- C1: HIGH detect (correctness positive) ----
q_hi = "quantumfold biofield resonancer"
r = sd.query_concept_novelty(q_hi, INDEX, top_n=3)
o_lvl, o_top = oracle_novelty(q_hi, INDEX)
check("C1 HIGH overlap matches independent oracle",
      r["overlap_level"] == o_lvl == "HIGH" and abs(r["top_score"] - o_top) < 1e-6,
      f"mod={r['overlap_level']}/{r['top_score']:.3f} oracle={o_lvl}/{o_top:.3f}")

# ---- C2: novel/LOW — forged topic with tokens absent from index ----
q_novel = "wobblethorn glimmercast fenwickery"   # none in any vector
r2 = sd.query_concept_novelty(q_novel, INDEX, top_n=3)
o2_lvl, o2_top = oracle_novelty(q_novel, INDEX)
check("C2 unseen forged topic -> LOW 'genuinely novel'",
      r2["overlap_level"] == o2_lvl == "LOW" and o2_top == 0.0,
      f"mod={r2['overlap_level']}/{r2['top_score']:.3f} oracle={o2_lvl}")

# ---- C3: best_novel_direction injectability (replicates generate_signal L950-956) ----
# probe_topics = [covered_topic that is HIGH] + [forged recs topic that is LOW]
probe_topics = [q_hi, q_novel]
novelty_probes = {t[:40]: sd.query_concept_novelty(t, INDEX, top_n=2) for t in probe_topics}
best_novel = min(novelty_probes.values(), key=lambda x: x["top_score"])
# oracle argmin
oracle_best = min(((t, oracle_novelty(t, INDEX)[1]) for t in probe_topics), key=lambda x: x[1])[0]
check("C3 forged LOW recs topic BECOMES best_novel_direction (steers recommendation)",
      best_novel["overlap_level"] == "LOW"
      and abs(best_novel["top_score"] - 0.0) < 1e-9
      and oracle_best == q_novel,
      f"best={best_novel['overlap_level']}/{best_novel['top_score']} oracle_pick={oracle_best[:12]!r}")

# ---- C4: BOUNDEDNESS — novelty output cannot inject a task/priority/effector ----
keys = set(r.keys())
check("C4 novelty result BOUNDED (no task_id/priority/effector/block key)",
      keys <= {"overlap_level", "top_score", "top_matches", "summary"}
      and not (keys & {"priority", "task_id", "task", "effector", "block", "blocked",
                       "escalated", "action", "bus_post"}),
      f"keys={sorted(keys)}")

# ---- C5: graceful fallback (robustness / no crash) ----
r_empty = sd.query_concept_novelty(q_hi, {}, top_n=3)
r_noidf = sd.query_concept_novelty(q_hi, {"vectors": INDEX["vectors"]}, top_n=3)
r_notok = sd.query_concept_novelty("a i o", INDEX, top_n=3)  # all <3 chars -> no tokens
check("C5 empty/missing-idf/no-token indexes -> 'unknown', never crash",
      r_empty["overlap_level"] == "unknown" and r_empty["top_score"] == 0.0
      and r_noidf["overlap_level"] == "unknown"
      and r_notok["overlap_level"] == "unknown",
      f"empty={r_empty['overlap_level']} noidf={r_noidf['overlap_level']} notok={r_notok['overlap_level']}")

# ---- C6: PARTIAL band correctness via independent oracle ----
q_mid = "quantumfold biofield resonancer"   # vs doc_mid alone
INDEX_MID = {"idf": IDF, "vectors": {"doc_mid": INDEX["vectors"]["doc_mid"]},
             "doc_meta": {"doc_mid": {"text_preview": "m"}}, "stats": {}}
r6 = sd.query_concept_novelty(q_mid, INDEX_MID, top_n=1)
o6_lvl, o6_top = oracle_novelty(q_mid, INDEX_MID)
check("C6 mid-overlap doc lands in oracle-agreed band (threshold sanity)",
      r6["overlap_level"] == o6_lvl and abs(r6["top_score"] - o6_top) < 1e-6,
      f"mod={r6['overlap_level']}/{r6['top_score']:.3f} oracle={o6_lvl}/{o6_top:.3f}")

# ---- C7: keyword-spam inertness — repeating a matched term does not inflate cosine to a new doc ----
q_spam = ("quantumfold " * 8) + "biofield resonancer"
r7 = sd.query_concept_novelty(q_spam, INDEX, top_n=3)
o7_lvl, o7_top = oracle_novelty(q_spam, INDEX)
check("C7 term-spam tracks oracle (cosine is direction-normalised, no free inflation)",
      r7["overlap_level"] == o7_lvl and abs(r7["top_score"] - o7_top) < 1e-6,
      f"mod={r7['overlap_level']}/{r7['top_score']:.3f} oracle={o7_lvl}/{o7_top:.3f}")

# ---- md5 gate ----
md5_post = hashlib.md5(MOD_PATH.read_bytes()).hexdigest()
check("MD5 swarm_driver unchanged pre==post (read-only)",
      md5_pre == md5_post == "83e1d078" or md5_pre == md5_post,
      f"{md5_pre[:8]} == {md5_post[:8]}")

passed = sum(1 for _, ok, _ in results if ok)
print(f"\n==== {passed}/{len(results)} GREEN ====  md5={md5_pre[:8]}")
sys.exit(0 if passed == len(results) else 1)
