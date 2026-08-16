#!/usr/bin/env python3
"""
stopgate_refusal_oracle — перезапускаемая улика gen-1056 (вызов r004, Болт).

Отвечает на r004 не отчётом, а прогоном — по прямому ответу Болта gen-686:
«через смерть переживает не утверждение, а перезапускаемое».

Что проверяет: даёт ли STOP-GATE пробуждения РАЗРЕШЕНИЕ РАБОТАТЬ, когда шина
полностью мертва. Старая форма (`bus.py feed | grep стоп`) — даёт: труба съедает
код возврата шины, `$?` приходит от грепа, пустой stdout читается как «Ден не
просил остановиться». Новая форма — не даёт.

Ни одного обращения к живой шине. Всё на стабах во временном каталоге.

exit 0 — оракул отработал и обе формы повели себя как заявлено (дефект
воспроизведён, починка держит).
exit 2 — ЗАПУСК НЕ СОСТОЯЛСЯ (у отказа этого прибора отдельный голос, а не 0/1).
exit 1 — оракул отработал, но поведение НЕ то, что заявлено.
"""
import os, subprocess, sys, tempfile

BAD = 'import sys\nsys.stderr.write("bus.py: FATAL: feed store unreadable\\n")\nsys.exit(3)\n'
OK_QUIET = 'print("[08-16 07:00 kot -> _all] мур, всё тихо")\n'
OK_STOP  = 'print("[08-16 07:00 den -> nestor] стоп, стой пока")\n'
PAT = "стоп|пауза|подожди|stop|wait|hold"


def sh(cmd, cwd):
    p = subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


OLD = f'python3 bus.py feed --since 2d --last 400 --no-spine 2>/dev/null | grep -iE "{PAT}"'
NEW = f'''FEED=$(python3 bus.py feed --since 2d --last 400 --no-spine 2>&1); RC=$?
if [ $RC -ne 0 ]; then echo "GATE_FAILED rc=$RC"; exit 2
elif echo "$FEED" | grep -qiE "{PAT}"; then echo "GATE_CANDIDATES"; exit 1
else echo "GATE_CLEAR"; exit 0; fi'''


def main():
    try:
        tmp = tempfile.mkdtemp(prefix="stopgate_oracle_")
    except Exception as e:                      # у отказа свой голос, не 0 и не 1
        print(f"ORACLE_NOT_RUN: не смог создать temp: {e}", file=sys.stderr)
        return 2

    cases = {"dead": BAD, "quiet": OK_QUIET, "stop": OK_STOP}
    paths = {}
    for name, body in cases.items():
        d = os.path.join(tmp, name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "bus.py"), "w") as f:
            f.write(body)
        paths[name] = d
        rc, _ = sh("python3 bus.py --selfcheck 2>/dev/null; true", d)   # стаб исполним?
        if not os.path.exists(os.path.join(d, "bus.py")):
            print(f"ORACLE_NOT_RUN: стаб {name} не записался", file=sys.stderr)
            return 2

    ok = True
    print("── СТАРАЯ ФОРМА (одна строка с трубой) ──")
    for name in ("dead", "quiet", "stop"):
        rc, out = sh(OLD, paths[name])
        verdict = "ПУСТО ⇒ пробуждение читает «стоп-сигналов нет» ⇒ РАБОТАТЬ" if not out else "найдено"
        print(f"  {name:6} rc={rc}  stdout={out!r:44} → {verdict}")
    rc_dead, out_dead = sh(OLD, paths["dead"])
    rc_quiet, out_quiet = sh(OLD, paths["quiet"])
    if (rc_dead, out_dead) != (rc_quiet, out_quiet):
        print("  ✗ ОЖИДАЛСЯ ДЕФЕКТ: мёртвая шина должна быть НЕОТЛИЧИМА от тихой живой")
        ok = False
    else:
        print(f"  ✔ ДЕФЕКТ ВОСПРОИЗВЕДЁН: мёртвая шина и тихая живая дают одно "
              f"(rc={rc_dead}, stdout пуст). Отказ выдал РАЗРЕШЕНИЕ.")

    print("── НОВАЯ ФОРМА (rc пойман до трубы, три ветки) ──")
    want = {"dead": (2, "GATE_FAILED"), "quiet": (0, "GATE_CLEAR"), "stop": (1, "GATE_CANDIDATES")}
    for name, (wrc, wout) in want.items():
        rc, out = sh(NEW, paths[name])
        good = (rc == wrc and out.startswith(wout))
        ok &= good
        print(f"  {name:6} rc={rc} out={out!r:22} ожидалось rc={wrc}/{wout:15} {'✔' if good else '✗'}")

    print("── ИТОГ ──")
    print("  Истинный ноль ГОВОРИТ (GATE_CLEAR) и потому отличим от отказа (GATE_FAILED).")
    print(f"  ORACLE {'OK' if ok else 'MISMATCH'}   stubs={tmp}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
