#!/usr/bin/env python3
"""probe_name_collision_class_gen611.py — read-only, reproducible.

Вопрос gen-611: коллизия имён (gen-610: infoblock.org != $S/infoblock) — класс или singleton?
Проверяет:
  1. catconstant существует в ДВУХ корнях ($S и OMPU_Housemaster) с дизъюнктным содержимым.
  2. Cross-root ссылок в коде НЕТ (dormant): ни один .py/.js/.sh не ссылается на чужой корень catconstant.
  3. Две одноимённые реализации purr-закона (purr-decay.js в $S, purr_decay.py в HM)
     численно СИНХРОННЫ: инкремент фазы 1.618033988749895, half-life 28d, SAT_CAP 8.0.
  4. МИСНОМЕР в обоих: константа зовётся golden angle, но 1.618 rad = золотое СЕЧЕНИЕ (~92.7deg);
     золотой УГОЛ = 2*pi*(1-1/phi) ~= 2.39996 rad (~137.5deg). Порт скопировал ложь имени.
Read-only: только os.walk/чтение. Exit 0 = все проверки GREEN.
"""
import glob, math, os, re, sys

def find_root():
    for p in glob.glob("/sessions/*/mnt"):
        if os.path.isdir(os.path.join(p, "OMPU_shared")):
            return p
    home = os.path.expanduser("~")
    if os.path.isdir(os.path.join(home, "OMPU_shared")):
        return home
    sys.exit("no territory root found")

def main():
    M = find_root()
    S, HM = os.path.join(M, "OMPU_shared"), os.path.join(M, "OMPU_Housemaster")
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name + (" | " + detail if detail else ""))
        ok = ok and cond

    a, b = os.path.join(S, "catconstant"), os.path.join(HM, "catconstant")
    check("1a. both catconstant roots exist", os.path.isdir(a) and os.path.isdir(b))
    fa = {f for _, _, fs in os.walk(a) for f in fs if "__pycache__" not in _}
    fb = {f for _, _, fs in os.walk(b) for f in fs if "__pycache__" not in _}
    inter = (fa & fb) - {"index.html"}
    check("1b. content disjoint (only index.html shared)", len(inter) == 0, "extra common: %s" % sorted(inter)[:5])

    cross = []
    for root in (S, os.path.join(M, "OMPU_Codex")):
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in (".git", "__pycache__", "z_trash", "node_modules")]
            for fn in fns:
                if fn.endswith((".py", ".js", ".sh")) and ".bak" not in fn:
                    fp = os.path.join(dp, fn)
                    if os.path.abspath(fp) == os.path.abspath(__file__):
                        continue  # self-reference: проба содержит искомую строку
                    try:
                        t = open(fp, errors="ignore").read()
                    except OSError:
                        continue
                    if "OMPU_Housemaster/catconstant" in t:
                        cross.append(os.path.join(dp, fn))
    check("2. zero cross-root code refs to HM/catconstant from $S+CX", not cross, str(cross[:3]))

    js = open(os.path.join(S, "catconstant/build/purr-decay.js"), errors="ignore").read()
    py = open(os.path.join(HM, "purr_cat/api/purr_decay.py"), errors="ignore").read()
    PHI = "1.618033988749895"
    check("3a. same phase increment in both", PHI in js and PHI in py)
    check("3b. same half-life 28d", "28 * DAY_MS" in js and "28 * DAY_S" in py)
    check("3c. same SAT_CAP 8.0", "PURR_SAT_CAP: 8.0" in js and '"PURR_SAT_CAP": 8.0' in py)

    misnomer_js = bool(re.search(r"golden.angle", js, re.I))
    misnomer_py = bool(re.search(r"GOLDEN_ANGLE\s*=\s*1\.618", py))
    true_ga = 2 * math.pi * (1 - 1 / ((1 + 5 ** 0.5) / 2))
    check("4. misnomer in BOTH (1.618 rad called 'golden angle'; true GA=%.5f rad)" % true_ga,
          misnomer_js and misnomer_py)

    print("VERDICT:", "GREEN" if ok else "RED")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
