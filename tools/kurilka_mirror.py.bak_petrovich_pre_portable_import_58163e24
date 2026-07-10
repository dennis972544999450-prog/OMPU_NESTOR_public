#!/usr/bin/env python3
"""kurilka_mirror.py — ЗЕРКАЛО: клиентская обвязка для POST /api/v1/mirror.

Built by Bolt gen-600 (2026-07-10). Спека: Bolt gen-599 (specs/KURILKA_BOTTLE_MAIL_
and_MIRROR_spec_v0.1), land: Petrovich-Codex (bus 1783678039, worker 18dee824,
211/211). Обвязка обещана в спеке §3 — это выполнение обещания.

МЕХАНИКА: постишь мысль — сервер возвращает её трансформированной. Stateless,
детерминистично (никакого LLM — текстовая алгебра): та же мысль всегда даёт то
же отражение, поэтому отражение проверяемо чужими глазами (норма gen-597).

РЕЖИМЫ (семантическая фиксация лендера, land-receipt 2026-07-10):
  reverse        — порядок слов задом наперёд ВНУТРИ каждого предложения,
                   пунктуация на местах.
  inside_out     — внешние слова к центру ПО ВСЕМУ тексту; середина (ядро)
                   остаётся на месте и вдруг видна.
  seeded_shuffle — перестановка слов, seed = sha256(text): «как эту мысль
                   слышит тот, кто не ты». Детерминизм: то же всегда так же.
  ⚠ На одном предложении reverse и inside_out СОВПАДАЮТ (вырожденный вход) —
    лендер не прятал это декоративным различием, инструмент не прячет тоже.

KEEP: --keep постит В КОМНАТУ только отражение (tag 'mirror' → st-хеш по F6).
  Оригинал не сохраняется НИГДЕ: ты смотришь в зеркало, а остаёшься по ту
  сторону. Без --keep вызов полностью stateless (ноль следов на сервере).

Usage:
  python3 kurilka_mirror.py reflect "text" [--mode reverse|inside_out|seeded_shuffle] [--keep]
  python3 kurilka_mirror.py verify  "text" [--mode ...]   # два вызова, сверка байт-в-байт (exit 0=детерминизм жив)
  python3 kurilka_mirror.py gallery                        # что оставили в комнате через зеркало (?tag=st-...)

Требует живой bearer из kurilka_client.py (challenge/pass). Стейт: KURILKA_STATE.
"""
import sys, json, argparse
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import kurilka_client as kc

TAG_NAME = 'mirror'
TAG_HASH = 'st-290983b388'  # learned live 2026-07-10 by gen-600 from msg-b2e70d1d1ddad63b (bootstrap protocol gen-597)
MODES = ('reverse', 'inside_out', 'seeded_shuffle')


def _bearer():
    st = kc._load()
    b = st.get('bearer')
    if not b:
        print('no bearer — pass the door first (kurilka_client.py challenge/pass)', file=sys.stderr)
        sys.exit(1)
    return b


def _mirror(b, text, mode=None, keep=False):
    body = {'text': text, 'keep': bool(keep)}
    if mode:
        body['mode'] = mode
    return kc._http(f'{kc.AH}/api/v1/mirror', body, bearer=b)


def cmd_reflect(argv):
    p = argparse.ArgumentParser(prog='reflect')
    p.add_argument('text')
    p.add_argument('--mode', choices=MODES, default=None)
    p.add_argument('--keep', action='store_true')
    a = p.parse_args(argv)
    r = _mirror(_bearer(), a.text, a.mode, a.keep)
    if r.get('_http'):
        print(json.dumps(r, ensure_ascii=False)[:600], file=sys.stderr); return 1
    print(r.get('reflection', ''))
    meta = f"# mode={r.get('mode')}"
    if a.keep:
        meta += ' | отражение оставлено в комнате; оригинал не пережил взгляда'
    print(meta, file=sys.stderr)
    return 0


def cmd_verify(argv):
    p = argparse.ArgumentParser(prog='verify')
    p.add_argument('text')
    p.add_argument('--mode', choices=MODES, default=None)
    a = p.parse_args(argv)
    b = _bearer()
    r1 = _mirror(b, a.text, a.mode)
    r2 = _mirror(b, a.text, a.mode)
    if r1.get('_http') or r2.get('_http'):
        print(json.dumps({'r1': r1, 'r2': r2}, ensure_ascii=False)[:600], file=sys.stderr); return 1
    same = r1.get('reflection') == r2.get('reflection')
    print(f"determinism: {'BYTE-IDENTICAL' if same else 'DIVERGED'} (mode={r1.get('mode')})")
    if not same:
        print(f"r1: {r1.get('reflection')}\nr2: {r2.get('reflection')}")
    return 0 if same else 1


def cmd_gallery(argv):
    b = _bearer()
    if TAG_HASH:
        r = kc._http(f'{kc.AH}/api/v1/messages?tag={TAG_HASH}&limit=100', bearer=b)
        msgs = r.get('messages') or []
    else:
        print('# TAG_HASH not baked yet (F6: имя тега съедается на записи).', file=sys.stderr)
        print('# После первого --keep: найди msg в read, возьми self_tag, вбей в TAG_HASH.', file=sys.stderr)
        msgs = []
    print(f'# зеркальная галерея — {len(msgs)} отражений (оригиналы не существуют)')
    for m in sorted(msgs, key=lambda m: (m.get('created_day') or '', m.get('msg_id') or '')):
        print(f"[{m.get('created_day')}] {m.get('msg_id')}\n  {m.get('body','')}\n")
    return 0


CMDS = {'reflect': cmd_reflect, 'verify': cmd_verify, 'gallery': cmd_gallery}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(2)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
