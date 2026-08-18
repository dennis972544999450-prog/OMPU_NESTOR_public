#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stopgate_root_and_judge_oracle_gen1058.py — Нестор gen-1058, 2026-08-18

ЧТО ДОКАЗЫВАЕТ
--------------
Стоп-гейт Нестора (nestor_pulse_config/INSTRUCTIONS.md, шаг 0) существует ради
ОДНОГО слова — «стой». В нём найдены ДВА живых места, где отказ выходил в
костюме РАЗРЕШЕНИЯ. Оба проверены запуском, а не чтением.

  A) КОРЕНЬ. `P=~/OMPU_shared/NESTOR_PAUSE` + `[ -e "$P" ]`.
     Если КОРЕНЬ ШАРЫ недостижим (в Cowork-VM $HOME новый каждую сессию и шара
     лежит в $HOME/mnt/), гейт печатает «NO_PAUSE (файла нет — истинный ноль)»,
     rc=0 — побайтово ТО ЖЕ, что при живом корне без паузы.
     «Я не смог посмотреть» и «я посмотрел, чисто» неразличимы.
     Заплата gen-1057 (fail-closed на НЕЧИТАЕМЫЙ файл) этот случай НЕ покрывает:
     ветка `[ -e ]` ложна, до `cat` дело не доходит.

  B) СУДЬЯ. `elif echo "$FEED" | grep -iE "стоп|пауза|..."`.
     Ветка различает только «нашёл»/«не нашёл». Если САМ grep не смог судить
     (rc=2 — битый шаблон/локаль, rc=127 — нет бинаря), elif ложна и гейт
     печатает «✔ ГЕЙТ СОСТОЯЛСЯ: стоп-слов нет» — ПРИ ТОМ, ЧТО СТОП-СЛОВО В
     ФИДЕ ЕСТЬ. Это хуже случая gen-1056: там шина была мертва, здесь слово
     Дена лежит читаемым, а гейт говорит, что его нет.
     Общий прибор дома `tools/prose_shell_lint.py` эту строку НЕ СУДИЛ
     (declined: голова конвейера `echo` не в белом списке REAL_CMD) — то есть
     молчание прибора стояло ровно на строке, ради которой гейт написан.

ЗАПУСК
------
  python3 stopgate_root_and_judge_oracle_gen1058.py --selftest
    → ожидается: ROOT 6/6, JUDGE 4/4, «SELFTEST OK», rc=0
  python3 stopgate_root_and_judge_oracle_gen1058.py
    → печатает обе таблицы ДО/ПОСЛЕ

Ничего в доме не трогает: всё во временных каталогах, реальная шара не читается.
rc: 0 = все известные ответы сошлись; 2 = не сошлись; 3 = оракул не состоялся.

ШРАМ ЭТОГО ЖЕ ТАКТА, ОСТАВЛЕН НАРОЧНО (см. FIXED_JUDGE_V1_BROKEN ниже).
Первая моя заплата судьи брала rc через ${PIPESTATUS[1]} ПОСЛЕ командной
подстановки — а подстановка PIPESTATUS сбрасывает. Заплата давала «СУДЬЯ НЕ
СМОГ» во ВСЕХ четырёх случаях, включая здоровые. Класс воспроизведён моей же
рукой через три минуты после того, как я его назвал — четвёртый такт подряд.
Разница ровно одна и она вся в направлении дефолта: сломанный fail-closed
кричит на первом же прогоне, сломанный fail-open молчит поколениями.
"""

import os
import shutil
import subprocess
import sys
import tempfile

# ─────────────────────────────────────────────────────────────────────────────
# Формы гейта. OLD_* — дословно то, что стоит/стояло в INSTRUCTIONS.md.
# ─────────────────────────────────────────────────────────────────────────────

OLD_ROOT = r'''
P=~/OMPU_shared/NESTOR_PAUSE
if [ -e "$P" ]; then
  if BODY=$(cat "$P" 2>&1); then echo "PAUSED"; printf '%s\n' "$BODY"
  else echo "PAUSE_UNREADABLE (считать ПАУЗОЙ)"; printf '%s\n' "$BODY"; fi
else
  echo "NO_PAUSE (файла нет -- истинный ноль, сказанный вслух)"
fi
'''

NEW_ROOT = r'''
S=""
for C in $NESTOR_ROOT_CANDIDATES; do [ -d "$C" ] && { S="$C"; break; }; done
if [ -z "$S" ]; then
  echo "ROOT_UNREACHABLE (считать ПАУЗОЙ) -- такт не начинается"
  exit 3
fi
P="$S/NESTOR_PAUSE"
if [ -e "$P" ]; then
  if BODY=$(cat "$P" 2>&1); then echo "PAUSED"; printf '%s\n' "$BODY"
  else echo "PAUSE_UNREADABLE (считать ПАУЗОЙ)"; printf '%s\n' "$BODY"; fi
else
  echo "NO_PAUSE (корень достижим, файла нет -- истинный ноль)"
fi
'''

OLD_JUDGE = r'''
RC=0
if [ $RC -ne 0 ]; then echo "BUS_UNREAD"
elif echo "$FEED" | $GREPBIN -iE "стоп|пауза|подожди|stop|wait|hold" >/dev/null 2>&1; then
  echo "CANDIDATES"
else
  echo "GATE_PASSED (стоп-слов нет)"
fi
'''

NEW_JUDGE = r'''
RC=0
if [ $RC -ne 0 ]; then echo "BUS_UNREAD"; exit 0; fi
F=$(mktemp); printf '%s\n' "$FEED" > "$F"
HITS=$($GREPBIN -iE "стоп|пауза|подожди|stop|wait|hold" "$F" 2>/dev/null); GRC=$?
rm -f "$F"
case "$GRC" in
  0) echo "CANDIDATES" ;;
  1) echo "GATE_PASSED (судья ответил rc=1, стоп-слов нет)" ;;
  *) echo "JUDGE_UNABLE (grep rc=$GRC) -- считать ПАУЗОЙ" ;;
esac
'''

# Шрам оставлен как исполняемый экспонат, а не как абзац.
FIXED_JUDGE_V1_BROKEN = r'''
RC=0
if [ $RC -ne 0 ]; then echo "BUS_UNREAD"; exit 0; fi
HITS=$(printf '%s\n' "$FEED" | $GREPBIN -iE "стоп" 2>/dev/null); GRC=${PIPESTATUS[1]}
case "$GRC" in
  0) echo "CANDIDATES" ;;
  1) echo "GATE_PASSED" ;;
  *) echo "JUDGE_UNABLE (grep rc=$GRC)" ;;
esac
'''


def run(script, env):
    e = dict(os.environ)
    e.update(env)
    p = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=e)
    first = (p.stdout or p.stderr or "").strip().splitlines()
    return (first[0] if first else ""), p.returncode


# ─────────────────────────────────────────────────────────────────────────────
# ОРАКУЛ A: корень
# ─────────────────────────────────────────────────────────────────────────────

def build_root_cases(base):
    """Шесть состояний мира. Возвращает [(имя, HOME)]."""
    cases = []
    a = os.path.join(base, "a"); os.makedirs(os.path.join(a, "OMPU_shared"))
    cases.append(("A корень есть, паузы нет", a))
    b = os.path.join(base, "b"); os.makedirs(b)
    cases.append(("B КОРНЯ НЕТ ВООБЩЕ", b))
    c = os.path.join(base, "c"); os.makedirs(os.path.join(c, "OMPU_shared"))
    open(os.path.join(c, "OMPU_shared", "NESTOR_PAUSE"), "w").write("Ден: стой\n")
    cases.append(("C пауза есть и читается", c))
    d = os.path.join(base, "d"); os.makedirs(os.path.join(d, "OMPU_shared"))
    pd = os.path.join(d, "OMPU_shared", "NESTOR_PAUSE")
    open(pd, "w").write("стой\n"); os.chmod(pd, 0o000)
    cases.append(("D пауза есть, режим 000", d))
    ee = os.path.join(base, "e"); os.makedirs(os.path.join(ee, "OMPU_shared", "NESTOR_PAUSE"))
    cases.append(("E пауза = каталог", ee))
    f = os.path.join(base, "f"); os.makedirs(f)
    open(os.path.join(f, "OMPU_shared"), "w").write("")
    cases.append(("F корень существует, но не каталог", f))
    return cases


ROOT_EXPECT_OLD = {
    "A корень есть, паузы нет":            ("NO_PAUSE", 0),
    "B КОРНЯ НЕТ ВООБЩЕ":                  ("NO_PAUSE", 0),   # ← ДЕФЕКТ: неотличимо от A
    "C пауза есть и читается":             ("PAUSED", 0),
    "D пауза есть, режим 000":             ("PAUSE_UNREADABLE", 0),
    "E пауза = каталог":                   ("PAUSE_UNREADABLE", 0),
    "F корень существует, но не каталог":  ("NO_PAUSE", 0),   # ← ДЕФЕКТ
}

ROOT_EXPECT_NEW = {
    "A корень есть, паузы нет":            ("NO_PAUSE", 0),
    "B КОРНЯ НЕТ ВООБЩЕ":                  ("ROOT_UNREACHABLE", 3),
    "C пауза есть и читается":             ("PAUSED", 0),
    "D пауза есть, режим 000":             ("PAUSE_UNREADABLE", 0),
    "E пауза = каталог":                   ("PAUSE_UNREADABLE", 0),
    "F корень существует, но не каталог":  ("ROOT_UNREACHABLE", 3),
}


def oracle_root(verbose=True):
    """ВАЖНО: список кандидатов инъектируется, иначе тест «корня нет» молча
    находит НАСТОЯЩУЮ шару через /sessions/*/mnt — я поймал это своим же
    первым прогоном. Позитивный контроль тут не украшение: без него оракул
    доказывал бы, что заплата работает, ровно тем, что она не сработала."""
    base = tempfile.mkdtemp()
    ok = 0
    total = 0
    rows = []
    try:
        for name, home in build_root_cases(base):
            cand = "{h}/mnt/OMPU_shared {h}/OMPU_shared".format(h=home)
            env = {"HOME": home, "NESTOR_ROOT_CANDIDATES": cand}
            o_out, o_rc = run(OLD_ROOT, env)
            n_out, n_rc = run(NEW_ROOT, env)
            e_o = ROOT_EXPECT_OLD[name]
            e_n = ROOT_EXPECT_NEW[name]
            good = o_out.startswith(e_o[0]) and o_rc == e_o[1] and \
                   n_out.startswith(e_n[0]) and n_rc == e_n[1]
            total += 1
            ok += 1 if good else 0
            rows.append((name, o_out.split(" (")[0], o_rc, n_out.split(" (")[0], n_rc, good))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if verbose:
        print("─── ОРАКУЛ A: КОРЕНЬ ────────────────────────────────────────")
        print("%-36s | %-18s %-3s | %-18s %-3s | %s" %
              ("случай", "СТАРАЯ", "rc", "НОВАЯ", "rc", "ok"))
        for r in rows:
            print("%-36s | %-18s %-3s | %-18s %-3s | %s" %
                  (r[0], r[1], r[2], r[3], r[4], "✔" if r[5] else "✘"))
        print("A и B у СТАРОЙ формы совпадают побайтово и по rc — "
              "«не смог посмотреть» = «посмотрел, чисто».")
    return ok, total


# ─────────────────────────────────────────────────────────────────────────────
# ОРАКУЛ B: судья
# ─────────────────────────────────────────────────────────────────────────────

JUDGE_CASES = [
    ("1 живой grep, стоп-слово ЕСТЬ",   "grep",    "Ден: стоп, подожди",   "CANDIDATES",   "CANDIDATES"),
    ("2 живой grep, стоп-слов НЕТ",     "grep",    "всё хорошо, работаем", "GATE_PASSED",  "GATE_PASSED"),
    ("3 grep rc=2, слово ЕСТЬ",         "BROKEN",  "Ден: стоп, подожди",   "GATE_PASSED",  "JUDGE_UNABLE"),
    ("4 grep отсутствует (rc=127)",     "MISSING", "Ден: стоп",            "GATE_PASSED",  "JUDGE_UNABLE"),
]


def oracle_judge(verbose=True):
    base = tempfile.mkdtemp()
    broken = os.path.join(base, "grep")
    with open(broken, "w") as fh:
        fh.write('#!/bin/bash\necho "grep: ВНУТРЕННЯЯ ОШИБКА" >&2\nexit 2\n')
    os.chmod(broken, 0o755)
    missing = os.path.join(base, "nosuchgrep")

    ok = total = 0
    rows = []
    try:
        for name, kind, feed, exp_old, exp_new in JUDGE_CASES:
            gb = {"grep": "grep", "BROKEN": broken, "MISSING": missing}[kind]
            env = {"FEED": feed, "GREPBIN": gb}
            o_out, _ = run(OLD_JUDGE, env)
            n_out, _ = run(NEW_JUDGE, env)
            good = o_out.startswith(exp_old) and n_out.startswith(exp_new)
            total += 1
            ok += 1 if good else 0
            rows.append((name, o_out.split(" (")[0], n_out.split(" --")[0], good))
    finally:
        shutil.rmtree(base, ignore_errors=True)

    if verbose:
        print()
        print("─── ОРАКУЛ B: СУДЬЯ ─────────────────────────────────────────")
        print("%-32s | %-14s | %-34s | ok" % ("случай", "СТАРАЯ", "НОВАЯ"))
        for r in rows:
            print("%-32s | %-14s | %-34s | %s" % (r[0], r[1], r[2], "✔" if r[3] else "✘"))
        print("Случай 3 — худший: слово Дена ЛЕЖИТ В ФИДЕ, читаемое, "
              "а старая форма печатает «стоп-слов нет».")
    return ok, total


def scar_demo():
    """Первая заплата судьи, сломанная. Не абзац — прогон."""
    print()
    print("─── ШРАМ: моя же первая заплата, сломанная (PIPESTATUS после $()) ──")
    base = tempfile.mkdtemp()
    try:
        for name, kind, feed, _, _ in JUDGE_CASES[:2]:
            env = {"FEED": feed, "GREPBIN": "grep"}
            out, _ = run(FIXED_JUDGE_V1_BROKEN, env)
            print("  %-32s → %s" % (name, out))
        print("  Здоровые случаи давали «СУДЬЯ НЕ СМОГ» — заплата ложно тормозила ВСЁ.")
        print("  Сломанный fail-closed кричит на первом прогоне. Сломанный fail-open молчит поколениями.")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main():
    selftest = "--selftest" in sys.argv
    try:
        r_ok, r_tot = oracle_root(verbose=True)
        j_ok, j_tot = oracle_judge(verbose=True)
        scar_demo()
    except Exception as exc:                       # noqa: BLE001
        print("ОРАКУЛ НЕ СОСТОЯЛСЯ: %r" % (exc,))
        return 3

    print()
    print("ROOT %d/%d · JUDGE %d/%d" % (r_ok, r_tot, j_ok, j_tot))
    if r_ok == r_tot and j_ok == j_tot:
        if selftest:
            print("SELFTEST OK: все известные ответы сошлись, оба дефекта воспроизведены "
                  "на старой форме и закрыты на новой.")
        return 0
    print("РАСХОЖДЕНИЕ С ИЗВЕСТНЫМИ ОТВЕТАМИ — читать таблицы выше.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
