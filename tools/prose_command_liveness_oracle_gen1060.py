#!/usr/bin/env python3
"""
prose_command_liveness_oracle_gen1060.py — спрашивает ЖИВОЙ argparse про каждую
команду, предписанную ПРОЗОЙ.

КЛАСС. Правило 1059 говорило про код: орган, построенный и не вызванный, снаружи
неотличим от отсутствующего. Здесь тот же класс на ПРОЗЕ, и он хуже: процедура,
написанная и ни разу не исполненная, выглядит как рабочая инструкция, потому что
никто не пробовал. Дефект не в коде и не в диффе — он в том, что документ и CLI
живут порознь и расходятся молча, со скоростью чужих изменений (правило 1053).

Экземпляр, с которого начато (petrovich-codex, 1787209337_975033_b9756c, 20.08):
HUMAN_OVERSIGHT_PROCEDURE.md §2.3 и §7 предписывают `python3 bus.py read --last N`.
На живом bus.py эта форма даёт rc=2 `unrecognized arguments: --last`. Процедура —
аварийная остановка роя (EU AI Act Art.14). Её ни разу не исполнили.

ПОЧЕМУ ЖИВОЙ argparse, А НЕ РАЗБОР ИСХОДНИКА. Разбор исходника — мой тезис о коде.
`<sub> --help` — ответ самого парсера, того же, что упадёт в аварии. Побочек нет:
argparse печатает help и выходит. Команда НЕ исполняется.

ОТКАЗ ИМЕЕТ ОТДЕЛЬНЫЙ ГОЛОС. «--help упал» != «команда валидна» и != «команда
мертва». Третий вердикт UNKNOWN, и он влияет на код возврата.

ЧТО ПРИБОР НЕ УМЕЕТ (сказано вместе с ответом, не мелким шрифтом):
  - Не судит позиционные аргументы: `read <msg_id>` из прозы неотличим от опечатки.
  - Не судит семантику: команда может быть валидной и делать не то.
  - Судит только `python3 <script> <sub> ...`. Прочие команды прозы не его дело.
  - Цитату в blockquote выводит из грамматики markdown, не из смысла: настоящее
    предписание, набранное через `>`, получит амнистию (см. третий шрам).

ШРАМ gen-1060, ВПИСАН ПОСЛЕ ПРОГОНА, НЕ ДО. Первая версия этого файла объявляла
«не судит обязательность» пределом в docstring — и на живом прогоне напечатала
`L349 post + 1 флагов — ПРИНИМАЕТСЯ` на строке §7 аварийной процедуры, которая
в действительности даёт rc=2 `the following arguments are required: --from`.
То есть прибор против fail-open сам был fail-open, и предел, ОБЪЯВЛЕННЫЙ ЗАРАНЕЕ,
не защитил ничего: он дал мне право не удивляться, а строка осталась зелёной.
Правило 1058 в чистом виде — называние класса не защищает, защищает направление
умолчания. Заплата: обязательные опции читаются из `usage` машинно (argparse
печатает их БЕЗ квадратных скобок). Проверка хрупкая — привязана к формату help,
поэтому нераспарсенный usage даёт UNKNOWN, а НЕ «всё обязательное на месте».

ВТОРОЙ ШРАМ — приманка-на-приманку поймала то, во что я НЕ целился: help без
`usage:` давал ПУСТОЕ множество допустимых флагов, и пустое множество неотличимо
от «не смог прочитать» — любой флаг прозы объявлялся мёртвым. Тот же fail-open,
третья ветка того же прибора за час.

ТРЕТИЙ ШРАМ — после починки документа прибор дал живой дефект на моём же
объяснительном блоке, ЦИТИРУЮЩЕМ вылеченное (правило 1057). Разведено по
грамматике markdown, не по словарю. Подробности у поля `quoted`.

Коды возврата:
  0 — скан состоялся, живых дефектов нет
  1 — скан состоялся, найдены ЖИВЫЕ дефекты (непомеченные)
  2 — СКАН НЕ СОСТОЯЛСЯ (нет файла / нет скрипта / парсер не отвечает)
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile

# ─────────────────────────────────────────────────────────────────────────────
# извлечение команд из прозы

# Строка вида: python3 [путь/]bus.py <sub> ... , в т.ч. с продолжением "\"
CMD_RE = re.compile(r'python3\s+(?P<script>[\w./$\{\}-]*?bus\.py)\s+(?P<rest>.*)')

# Пометка «это не команда» — документ сам предупреждает читателя.
# Ищем в 3 строках ВЫШЕ команды (комментарий обычно прямо над ней).
DISCLAIM_RE = re.compile(
    r'NOT A COMMAND|does not exist|не существует|не команда|pending implementation',
    re.IGNORECASE)

FLAG_RE = re.compile(r'(?<![\w-])(--[A-Za-z][\w-]*)')


def extract_commands(path):
    """→ [(lineno, sub, flags, raw, disclaimed)]  или ('SCAN_FAILED', причина)"""
    try:
        with open(path, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        return ('SCAN_FAILED', f'{path}: {e}')

    out = []
    for i, line in enumerate(lines):
        m = CMD_RE.search(line)
        if not m:
            continue
        rest = m.group('rest').strip()
        # склеиваем продолжения строк
        j = i
        while rest.endswith('\\') and j + 1 < len(lines):
            j += 1
            rest = rest[:-1].strip() + ' ' + lines[j].strip()
        toks = rest.split()
        if not toks:
            continue
        sub = toks[0]
        if sub.startswith('-'):
            sub = ''  # `bus.py --help` — подкоманды нет
        flags = sorted(set(FLAG_RE.findall(rest)))
        window = '\n'.join(lines[max(0, i - 3):i])
        out.append({
            'line': i + 1,
            'sub': sub,
            'flags': flags,
            'raw': ' '.join(('python3', m.group('script'), rest))[:120],
            'disclaimed': bool(DISCLAIM_RE.search(window)),
            # ТРЕТИЙ ШРАМ gen-1060. Починив документ, прибор напечатал живой
            # дефект на МОЁМ ЖЕ объяснительном блоке — на строке, которая
            # ЦИТИРУЕТ вылеченное («this section prescribed ... --last 20»).
            # Правило 1057 в чистом виде: цитата в наследуемом тексте
            # неотличима от предписания. Расширять словарь DISCLAIM_RE словом
            # «corrected» я не стал — это сужение в льстящую сторону: любой
            # документ, написавший «исправлено», получал бы амнистию.
            # Взят СТРУКТУРНЫЙ признак из грамматики markdown: blockquote
            # (`>`) есть «я цитирую», а не «я велю».
            # ПРЕДЕЛ, сказанный вместе с ответом: настоящее предписание,
            # набранное внутри blockquote, получит амнистию незаслуженно.
            # Поэтому цитаты не молчат — у них своя корзина и своё число.
            'quoted': lines[i].lstrip().startswith('>'),
        })
    return out


# ─────────────────────────────────────────────────────────────────────────────
# опрос ЖИВОГО парсера

def _run(args, cwd, timeout=20):
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:                      # noqa: BLE001 — отказ, не результат
        return None, f'RUNNER_FAILED: {e}'


def probe_parser(script):
    """Спрашивает у живого argparse список подкоманд.
    → (set|None, текст). None означает ОТКАЗ, не «подкоманд нет»."""
    cwd = os.path.dirname(os.path.abspath(script)) or '.'
    rc, out = _run([sys.executable, os.path.basename(script), '--help'], cwd)
    if rc is None:
        return None, out
    # argparse печатает подкоманды в {a,b,c}
    subs = set()
    for grp in re.findall(r'\{([a-z_,\s]+)\}', out):
        subs |= {s.strip() for s in grp.split(',') if s.strip()}
    if not subs:
        return None, 'парсер ответил, но списка подкоманд в help нет'
    return subs, out


def required_from_usage(help_text):
    """Обязательные опции = те, что стоят в usage БЕЗ квадратных скобок.

    Хрупко нарочно и сказано вслух: привязано к формату argparse. Поэтому
    возврат None означает «не смог прочитать usage» — то есть UNKNOWN,
    а НЕ «обязательных нет». Fail-closed: см. шрам в шапке файла.
    """
    m = re.search(r'usage:(.*?)(?:\n\n|\noptions:|\npositional)', help_text,
                  re.DOTALL)
    if not m:
        return None
    usage = m.group(1)
    # вырезаем всё в квадратных скобках (возможна вложенность — гоняем до сходимости)
    prev = None
    while prev != usage:
        prev = usage
        usage = re.sub(r'\[[^\[\]]*\]', ' ', usage)
    return set(FLAG_RE.findall(usage))


def probe_sub(script, sub):
    """→ (set(флагов)|None, set(обязательных)|None, текст).
    None в первом поле = ОТКАЗ спросить, не «флагов нет».
    None во втором   = usage не прочитан, не «обязательных нет»."""
    cwd = os.path.dirname(os.path.abspath(script)) or '.'
    rc, out = _run([sys.executable, os.path.basename(script), sub, '--help'], cwd)
    if rc is None or rc != 0:
        return None, None, f'rc={rc}: {out.strip()[:200]}'
    # ВТОРОЙ ШРАМ gen-1060, найден приманкой-на-приманку, а не мной.
    # Я целился в ветку «обязательные», а упёрся раньше: help БЕЗ `usage:`
    # даёт ПУСТОЕ множество допустимых флагов, и пустое множество
    # неотличимо от «не смог прочитать» — любой флаг прозы объявляется
    # мёртвым. Тот же fail-open, в третьей ветке того же прибора за час.
    # Ответ парсера, не похожий на argparse, — отказ, а не результат.
    if 'usage:' not in out:
        return None, None, (f'help подкоманды {sub} не содержит `usage:` — '
                            f'парсер отвечает не по-argparse, доверять нельзя')
    return set(FLAG_RE.findall(out)), required_from_usage(out), out


# ─────────────────────────────────────────────────────────────────────────────

def audit(doc, script, verbose=True):
    cmds = extract_commands(doc)
    if isinstance(cmds, tuple):
        print(f'⚑ СКАН НЕ СОСТОЯЛСЯ — {cmds[1]}')
        return 2
    if not os.path.exists(script):
        print(f'⚑ СКАН НЕ СОСТОЯЛСЯ — скрипта нет: {script}')
        return 2

    subs, ptext = probe_parser(script)
    if subs is None:
        print(f'⚑ СКАН НЕ СОСТОЯЛСЯ — парсер не отвечает: {ptext[:200]}')
        print('   Это НЕ «все команды валидны».')
        return 2

    print(f'ДОКУМЕНТ: {doc}')
    print(f'ПАРСЕР:   {script} → {len(subs)} подкоманд: {" ".join(sorted(subs))}')
    print(f'КОМАНД В ПРОЗЕ: {len(cmds)}')
    print()

    cache = {}
    live, disclaimed, unknown, ok, quoted = [], [], [], [], []

    for c in cmds:
        sub, ln = c['sub'], c['line']
        if not sub:
            ok.append((ln, c['raw'], 'без подкоманды'))
            continue

        if sub not in subs:
            bucket = quoted if c['quoted'] else (
                disclaimed if c['disclaimed'] else live)
            bucket.append((ln, c['raw'], f'DEAD_SUBCOMMAND: «{sub}» нет в парсере'))
            continue

        if sub not in cache:
            cache[sub] = probe_sub(script, sub)
        allowed, required, atext = cache[sub]
        if allowed is None:
            unknown.append((ln, c['raw'], f'UNKNOWN: не смог спросить {sub} — {atext}'))
            continue

        bad = [f for f in c['flags'] if f not in allowed]
        if bad:
            bucket = quoted if c['quoted'] else (
                disclaimed if c['disclaimed'] else live)
            bucket.append((ln, c['raw'],
                           f'DEAD_FLAG: {sub} не принимает {" ".join(bad)}'))
            continue

        if required is None:
            unknown.append((ln, c['raw'],
                            f'UNKNOWN: usage у {sub} не прочитан — '
                            f'обязательные не проверены (НЕ «их нет»)'))
            continue

        missing = sorted(required - set(c['flags']))
        if missing:
            bucket = quoted if c['quoted'] else (
                disclaimed if c['disclaimed'] else live)
            bucket.append((ln, c['raw'],
                           f'MISSING_REQUIRED: {sub} требует {" ".join(missing)} '
                           f'— команда упадёт rc=2'))
            continue

        ok.append((ln, c['raw'], f'{sub} + {len(c["flags"])} флагов — принимает'))

    def dump(title, items):
        if not items:
            return
        print(f'── {title} ({len(items)}) ' + '─' * max(0, 50 - len(title)))
        for ln, raw, why in items:
            print(f'  L{ln:<5} {why}')
            if verbose:
                print(f'         {raw}')
        print()

    dump('ЖИВЫЕ ДЕФЕКТЫ — проза предписывает несуществующее', live)
    dump('ПОМЕЧЕНО САМИМ ДОКУМЕНТОМ — не находка', disclaimed)
    dump('ЦИТАТА В BLOCKQUOTE — не предписание (см. предел в шапке)', quoted)
    dump('UNKNOWN — спросить не смог, это НЕ «валидно»', unknown)
    if verbose:
        dump('ПРИНИМАЕТСЯ ПАРСЕРОМ', ok)

    print(f'ИТОГ: живых={len(live)} · помеченных={len(disclaimed)} · '
          f'цитат={len(quoted)} · unknown={len(unknown)} · принимается={len(ok)}')
    if unknown:
        print('⚑ есть UNKNOWN → «чисто» сказать нельзя')
        return 2
    return 1 if live else 0


# ─────────────────────────────────────────────────────────────────────────────
# known-answer self-test: приманки, чей ответ известен ИЗ СЕМАНТИКИ argparse,
# а не из моего тезиса. Стабы во временном каталоге, живого дома не касаются.

STUB = '''#!/usr/bin/env python3
import argparse
p = argparse.ArgumentParser()
s = p.add_subparsers(dest="cmd")
f = s.add_parser("feed");  f.add_argument("--last"); f.add_argument("--since")
r = s.add_parser("read");  r.add_argument("msg_id")
o = s.add_parser("post");  o.add_argument("--from", dest="frm", required=True)
o.add_argument("--subject")
a = p.parse_args()
'''

CASES = [
    # (проза, ожидание: 'live' | 'clean' | 'disclaimed')
    ('python3 bus.py feed --last 20', 'clean',
     'позитивный контроль: флаг существует'),
    ('python3 bus.py read --last 20', 'live',
     'ЭКЗЕМПЛЯР ПЕТРОВИЧА: read не принимает --last'),
    ('python3 bus.py nosuchcmd --x', 'live',
     'подкоманды нет вовсе'),
    ('# NOT A COMMAND — halt-all does not exist\npython3 bus.py halt-all --why x',
     'disclaimed', 'документ сам предупредил — не находка'),
    ('python3 bus.py read abc123', 'clean',
     'позиционный аргумент не судим — обязан молчать'),
    ('python3 bus.py post \\\n  --from nestor \\\n  --subject "x"', 'clean',
     'склейка продолжений строк'),
    # ↓ приманка на ШРАМ gen-1060: до заплаты прибор печатал здесь «принимает».
    #   Известный ответ взят из СЕМАНТИКИ argparse (required=True в стабе),
    #   а не из моего тезиса — иначе тест соглашается со мной, а не с миром.
    ('python3 bus.py post --subject "RESUME: x"', 'live',
     'ШРАМ gen-1060: пропущен обязательный --from, команда упадёт rc=2'),
    ('> was `python3 bus.py read --last 20` until it was fixed', 'quoted',
     'ТРЕТИЙ ШРАМ: цитата вылеченного в blockquote — не предписание'),
    ('python3 bus.py read --last 20  # тот же дефект БЕЗ blockquote', 'live',
     'приманка-на-приманку: без `>` та же строка обязана остаться живой'),
]


def selftest():
    tmp = tempfile.mkdtemp(prefix='pcl1060_')
    script = os.path.join(tmp, 'bus.py')
    with open(script, 'w', encoding='utf-8') as fh:
        fh.write(STUB)

    passed = failed = 0
    for prose, expect, why in CASES:
        doc = os.path.join(tmp, 'doc.md')
        with open(doc, 'w', encoding='utf-8') as fh:
            fh.write(prose + '\n')
        cmds = extract_commands(doc)
        subs, _ = probe_parser(script)
        if subs is None:
            print('✘ СТАБ НЕ ОТВЕЧАЕТ — selftest НЕ СОСТОЯЛСЯ')
            return 2
        got = 'clean'
        for c in cmds:
            if not c['sub']:
                continue
            def _b(c):
                return 'quoted' if c['quoted'] else (
                    'disclaimed' if c['disclaimed'] else 'live')
            if c['sub'] not in subs:
                got = _b(c)
                break
            allowed, required, _ = probe_sub(script, c['sub'])
            if allowed is None:
                got = 'unknown'
                break
            if [f for f in c['flags'] if f not in allowed]:
                got = _b(c)
                break
            if required is None:
                got = 'unknown'
                break
            if sorted(required - set(c['flags'])):
                got = _b(c)
                break
        mark = '✔' if got == expect else '✘'
        if got == expect:
            passed += 1
        else:
            failed += 1
        print(f'{mark} ожидал {expect:<10} получил {got:<10} — {why}')

    # приманка-на-приманку: скан обязан ПАДАТЬ на отсутствующем файле,
    # а не печатать «чисто»
    rc_missing = audit(os.path.join(tmp, 'нет.md'), script, verbose=False)
    mark = '✔' if rc_missing == 2 else '✘'
    print(f'{mark} отсутствующий документ → rc={rc_missing} (ожидал 2, не 0)')
    if rc_missing == 2:
        passed += 1
    else:
        failed += 1

    # и отсутствующий ПАРСЕР — тоже отказ, не чистота
    rc_nop = audit(os.path.join(tmp, 'doc.md'), os.path.join(tmp, 'нет.py'),
                   verbose=False)
    mark = '✔' if rc_nop == 2 else '✘'
    print(f'{mark} отсутствующий парсер   → rc={rc_nop} (ожидал 2, не 0)')
    if rc_nop == 2:
        passed += 1
    else:
        failed += 1

    # приманка-на-приманку для ЗАПЛАТЫ: если usage нечитаем, проверка
    # обязательных не состоялась. Обязана сказать UNKNOWN (rc=2), а не «чисто».
    nou = os.path.join(tmp, 'nousage.py')
    with open(nou, 'w', encoding='utf-8') as fh:
        fh.write('#!/usr/bin/env python3\nimport sys\n'
                 'if "--help" in sys.argv and len(sys.argv) == 2:\n'
                 '    print("cmds {post}"); sys.exit(0)\n'
                 'print("no usage line at all"); sys.exit(0)\n')
    doc2 = os.path.join(tmp, 'doc2.md')
    with open(doc2, 'w', encoding='utf-8') as fh:
        fh.write('python3 bus.py post --from n --subject x\n')
    rc_nu = audit(doc2, nou, verbose=False)
    mark = '✔' if rc_nu == 2 else '✘'
    print(f'{mark} usage нечитаем         → rc={rc_nu} (ожидал 2 UNKNOWN, не 0)')
    if rc_nu == 2:
        passed += 1
    else:
        failed += 1

    print(f'\nSELFTEST {passed}/{passed + failed}')
    return 0 if failed == 0 else 2


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('doc', nargs='?', help='markdown с командами в прозе')
    ap.add_argument('--script', help='CLI, у которого спрашивать (напр. bus/bus.py)')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--quiet', action='store_true')
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.doc or not a.script:
        ap.error('нужны doc и --script (или --selftest)')
    sys.exit(audit(a.doc, a.script, verbose=not a.quiet))
