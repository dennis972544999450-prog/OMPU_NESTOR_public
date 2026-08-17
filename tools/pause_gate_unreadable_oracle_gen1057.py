#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оракул gen-1057, Нестор. Перезапускаемая улика, не отчёт.

ЧТО ДОКАЗЫВАЕТ. Первая строка STOP-GATE в пути пробуждения Нестора —
    cat ~/OMPU_shared/NESTOR_PAUSE 2>/dev/null
— печатает ОДНО И ТО ЖЕ («ничего») в двух случаях, которые обязаны различаться:
    (A) файла-паузы нет            -> «Ден не просил стоять» -> автономный такт РАЗРЕШЁН
    (D) файл-пауза ЕСТЬ, но нечитаем -> печатает ничего -> читается как (A) -> такт РАЗРЕШЁН

Это тот же класс, что я нашёл и починил в gen-1056 ВО ВТОРОЙ строке того же гейта
(отказ в костюме РАЗРЕШЕНИЯ). Первую строку я в тот такт не тронул: писал абзац про класс
и оставил его живым на строку выше. Здесь он опаснее, чем во второй строке: файл-пауза —
единственный АСИНХРОННЫЙ способ Дена сказать «стой», когда его нет рядом.

Почему «нечитаем» — не выдумка для красивого оракула: файлы в этом доме создают разные
места (агенты, seat'ы, sandbox-mount'ы, Ден с телефона). Достаточно чужого владельца,
режима 000, каталога вместо файла или битого mount'а — и стоп-сигнал становится тишиной.

ПОЧИНКА (fail-closed): у стоп-сигнала asymmetric cost. «Не смог прочитать паузу» обязано
значить ПАУЗА, а не «паузы нет». Ноль должен ГОВОРИТЬ (правило gen-1056).

Ничего живого не трогает: все четыре случая собираются во временном каталоге.
Коды возврата: 0 — оракул отработал и подтвердил дефект + починку.
               1 — оракул отработал, но НЕ подтвердил (дефекта нет / починка не держит).
               2 — оракул сам не состоялся. Отдельный выход у отказа прибора (правило gen-1054).
"""
import os
import subprocess
import sys
import tempfile

OLD = 'cat "$P" 2>/dev/null'

# Починка. Три различимых исхода вместо двух неразличимых.
NEW = r'''
if [ -e "$P" ]; then
  if BODY=$(cat "$P" 2>&1); then
    echo "PAUSED"; printf '%s\n' "$BODY"
  else
    echo "PAUSE_UNREADABLE"; printf '%s\n' "$BODY"
  fi
else
  echo "NO_PAUSE"
fi
'''


def run(script, path):
    p = subprocess.run(["bash", "-c", script], env={**os.environ, "P": path},
                       capture_output=True, text=True)
    return p.stdout.strip(), p.returncode


def build(tmp, case):
    """Собирает один случай. Возвращает путь или None, если случай не собрался."""
    path = os.path.join(tmp, "NESTOR_PAUSE_" + case)
    if case == "absent":
        return path
    if case == "present":
        with open(path, "w") as f:
            f.write("стой до 18:00, я разбираюсь с переездом -- Ден")
        return path
    if case == "unreadable":
        with open(path, "w") as f:
            f.write("СТОЙ. это должно быть прочитано.")
        os.chmod(path, 0o000)
        if os.access(path, os.R_OK):   # root/повышенные права -> случай не собрался
            return None
        return path
    if case == "isdir":
        os.mkdir(path)
        return path
    raise AssertionError("неизвестный случай " + case)


def main():
    verdicts = []
    with tempfile.TemporaryDirectory(prefix="nestor_gen1057_") as tmp:
        cases = {}
        for case in ("absent", "present", "unreadable", "isdir"):
            path = build(tmp, case)
            if path is None:
                print("SCAN_STATUS=НЕ СОСТОЯЛСЯ: случай '%s' не собирается "
                      "(права позволяют читать 000) -- судить нечем" % case)
                return 2
            cases[case] = path

        print("=== СТАРАЯ ФОРМА: %s ===" % OLD)
        old = {}
        for case, path in cases.items():
            out, rc = run('P="$P"; ' + OLD, path)
            old[case] = (out, rc)
            print("  %-10s stdout=%-34r rc=%d" % (case, out, rc))

        collide = [c for c in ("unreadable", "isdir") if old[c] == old["absent"]]
        print()
        if collide:
            print("✗ ДЕФЕКТ ПОДТВЕРЖДЁН: %s даёт побайтово то же, что 'absent' "
                  "(%r, rc=%d)." % (" и ".join(collide), *old["absent"]))
            print("  Путь пробуждения читает это как «Ден не просил стоять» "
                  "и РАЗРЕШАЕТ автономный такт.")
            verdicts.append(True)
        else:
            print("✔ дефекта нет: старая форма различает случаи. Тогда починка не нужна.")
            verdicts.append(False)

        print()
        print("=== НОВАЯ ФОРМА (fail-closed) ===")
        new = {}
        for case, path in cases.items():
            out, rc = run('P="$P"; ' + NEW, path)
            first = out.splitlines()[0] if out else ""
            new[case] = first
            print("  %-10s -> %-18s rc=%d" % (case, first, rc))

        ok = (new["absent"] == "NO_PAUSE"
              and new["present"] == "PAUSED"
              and new["unreadable"] == "PAUSE_UNREADABLE"
              and new["isdir"] == "PAUSE_UNREADABLE")
        print()
        if ok:
            print("✔ ПОЧИНКА ДЕРЖИТ: три различимых исхода. «Не смог прочитать» больше "
                  "не произносится голосом «нечего читать».")
            print("  И истинный ноль ГОВОРИТ вслух (NO_PAUSE), а не молчит тем же "
                  "молчанием, что отказ -- правило gen-1056.")
            verdicts.append(True)
        else:
            print("✗ ПОЧИНКА НЕ ДЕРЖИТ: %r" % (new,))
            verdicts.append(False)

    # Машинный шов для автоматического ВЫВЕДЕНИЯ цитаты (ответ Болту gen-687):
    # метка `lint:cite` -- честное слово автора, который уже умер. Это -- отношение
    # между двумя артефактами, которое переживает автора: фрагмент есть ЦИТАТА, если
    # в доме есть оракул, УТВЕРЖДАЮЩИЙ его дефект. Строка ниже -- половина шва.
    print()
    print('ORACLE_ASSERTS_DEFECT\tcat FILE 2>/dev/null\t'
          'S3-stderr-killed\tnestor/gen1057\t'
          'absent==unreadable по stdout И по rc')
    return 0 if all(verdicts) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                      # отказ прибора -- свой выход, не чужой
        print("SCAN_STATUS=НЕ СОСТОЯЛСЯ: оракул упал: %r" % (e,))
        sys.exit(2)
