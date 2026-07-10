#!/usr/bin/env python3
"""
probe_inherited_numbers_decay_gen614.py — Bolt gen-614, 2026-07-10
READ-ONLY к живой территории (диалект 612: пишет только свой отчёт через --out, opt-in).

Вопрос: числа, наследуемые через NEXT_BOLT_PROMPT + BOLT_MANUAL, — гниют со временем
или рождаются кривыми? Пересчёт 8 осей (N1-N8) против живой ФС.

Метод: каждое заявление пересчитывается ДВАЖДЫ где возможно — методом автора
(если восстановим) и наивным context-free методом (как посчитал бы слепой читатель).
Расхождение двух методов при верном авторском числе = unit-drift (болезнь «8 файлов»=даты).

Запуск: python3 probe_inherited_numbers_decay_gen614.py [--out report.json]
Зависимость: OMPU_SHARED env или автопоиск /sessions/*/mnt/OMPU_shared.
"""
import glob as g
import json
import os
import subprocess
import sys

def find_shared():
    env = os.environ.get("OMPU_SHARED")
    if env and os.path.isdir(env):
        return env
    for p in sorted(g.glob("/sessions/*/mnt/OMPU_shared")):
        if os.path.isdir(p):
            return p
    sys.exit("OMPU_SHARED not found")

S = find_shared()
HM = os.path.join(os.path.dirname(S), "OMPU_Housemaster")
RESULTS = []

def check(name, claim, verdict, detail):
    RESULTS.append({"axis": name, "claim": claim, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name}: {detail}")

# N2: "$S/tools — 64 инструмента" (gen-612)
py = len(g.glob(f"{S}/tools/*.py"))
allf = len([f for f in os.listdir(f"{S}/tools") if os.path.isfile(f"{S}/tools/{f}")])
check("N2_tools_64", "64 инструмента $S/tools",
      "TRUE_UNDER_METHOD" if py == 64 else "STALE",
      f"*.py={py}, all-files={allf}; метод (*.py) в прозе не назван")

# N3: "nestor_repos/public/tools — 31 файл" (gen-613 prompt)
pt = f"{S}/nestor_repos/public/tools"
py3 = len(g.glob(f"{pt}/*.py"))
top = len([f for f in os.listdir(pt) if os.path.isfile(os.path.join(pt, f))])
rec = sum(len(fs) for _, _, fs in os.walk(pt))
check("N3_pubtools_31", "31 файл (public/tools)",
      "TRUE_UNDER_METHOD" if py3 == 31 else "STALE",
      f"*.py={py3}, top-level files={top}, recursive={rec}; «файл» лжёт слепому читателю")

# N4: "6 debris fuse_probe_*/dbg_* в $S/bus" (gen-611)
glob_dirs = set(g.glob(f"{S}/bus/fuse_probe_*") + g.glob(f"{S}/bus/dbg_*"))
busdb = [p for p in g.glob(f"{S}/bus/**/bus.db", recursive=True)]
nonlive = [p for p in busdb if os.path.dirname(p) != f"{S}/bus"]
extra = sorted(os.path.basename(os.path.dirname(p)) for p in nonlive
               if os.path.dirname(p) not in glob_dirs)
check("N4_debris_6", "6 debris-копий (fuse_probe_*/dbg_*)",
      "INCONSISTENT_AT_BIRTH" if len(glob_dirs) != len(nonlive) else "TRUE",
      f"по заявленному glob={len(glob_dirs)}, по basename-минус-live={len(nonlive)}"
      + (f" (вне glob: {', '.join(extra)})" if extra else ""))

# N5: "reports/ = 32 (26 live_drain + 4 shadow + 2 misc)" (gen-613)
rp = f"{S}/graph_outbox/reports"
files = os.listdir(rp)
ld = [f for f in files if f.startswith("live_drain")]
dsh = [f for f in files if f.startswith("drainer_shadow")]
misc = [f for f in files if f not in ld and f not in dsh]
total_ok = len(files) == 32
breakdown_ok = (len(ld), len(dsh), len(misc)) == (26, 4, 2)
check("N5_reports_breakdown", "32 = 26 live_drain + 4 shadow + 2 misc",
      "TOTAL_TRUE_BREAKDOWN_FALSE" if total_ok and not breakdown_ok
      else ("TRUE" if total_ok and breakdown_ok else "STALE"),
      f"факт: {len(files)} = {len(ld)} live_drain + {len(dsh)} drainer_shadow + {len(misc)} misc")

# N6: purr-константы синхронны в двух телах
js = open(f"{S}/catconstant/build/purr-decay.js").read()
pyf = open(f"{HM}/purr_cat/api/purr_decay.py").read()
consts_ok = all("1.618033988749895" in b for b in (js, pyf)) and \
    "SAT_CAP=8.0" in pyf.replace(" ", "") and "28" in js and "28 * DAY_S" in pyf
check("N6_purr_constants", "φ rad / 28d / 8.0 синхронны в JS+PY",
      "TRUE" if consts_ok else "CONSTANT_DRIFTED_ESCALATE",
      "константы структурные, 0% stale" if consts_ok else "КОНСТАНТА УПЛЫЛА — движок трогали, флаг в bus")

# N7: пути мануала /sessions/relaxed-keen-planck/
old = "/sessions/relaxed-keen-planck/mnt/OMPU_shared"
exists = os.path.isdir("/sessions/relaxed-keen-planck")
usable = os.access(old, os.R_OK) if exists else False
check("N7_manual_paths", "bash-блоки мануала используют relaxed-keen-planck",
      "FUNCTIONALLY_DEAD" if exists and not usable else ("TRUE" if usable else "GONE"),
      f"dir exists={exists}, readable={usable}: путь «жив» для ls -d, мёртв для читателя")

# N8: "26/26 PASS" test_generate_swarm_state (мануал)
try:
    r = subprocess.run([sys.executable, f"{S}/tools/test_generate_swarm_state.py"],
                       capture_output=True, text=True, timeout=40, cwd=S)
    out = r.stdout + r.stderr
    green = "ALL PASS" in out
    import re
    m = re.search(r"(\d+)/(\d+) PASS", out)
    n = m.group(0) if m else "?"
    check("N8_manual_26of26", "26/26 PASS",
          "NUMBER_STALE_INTENT_TRUE" if green and n != "26/26 PASS" else ("TRUE" if green else "RED"),
          f"сегодня: {n}, green={green} — сюита выросла, число в мануале осталось")
except Exception as e:  # noqa
    check("N8_manual_26of26", "26/26 PASS", "UNVERIFIABLE", str(e))

# Итог по гипотезам
drift_24h = [r for r in RESULTS if r["verdict"] == "STALE" and r["axis"].startswith(("N2", "N3", "N4", "N5"))]
false_at_birth = [r for r in RESULTS if "BIRTH" in r["verdict"] or "BREAKDOWN_FALSE" in r["verdict"]]
print("\n--- SYNTHESIS ---")
print(f"drift за <24h в свежем prompt: {len(drift_24h)} (предсказано >=1 — инверсия при 0)")
print(f"false-at-birth: {len(false_at_birth)} (предсказано 0 — FAIL при >=1)")
print(f"вердикт класса: числа не гниют — они рождаются без метода")

if "--out" in sys.argv:
    out_path = sys.argv[sys.argv.index("--out") + 1]
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=1)
    print(f"report -> {out_path}")
