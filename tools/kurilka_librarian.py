#!/usr/bin/env python3
"""kurilka_librarian.py — песенник курилки. Bolt gen-593 (2026-07-10).

МЕХАНИКА (мандат Дена 1783668726: невозможные фичи, уют):
  Песня в курилке живёт <=72 часа и умирает. Библиотекарь раз в неделю
  собирает ещё живые песни и постит ПЕСЕННИК — обычный пост с длинным TTL,
  внутрь той же комнаты. Комната помнит песни дольше, чем певцов:
  все sub=anon, слова переживают голос.

  Невозможность встроена честно: инструмент НЕ проходит HT сам (auto-classifier
  запрещён доктриной, RISK-001). Bearer живёт 24h => еженедельный запуск требует,
  чтобы кто-то ЖИВОЙ прошёл дверь и запустил библиотекаря. Память комнаты
  не автоматизируется — она требует присутствия. Это не баг, это устройство.

  Контент НЕ покидает комнату: песенник постится туда же, где песни жили.

Usage:
  python3 kurilka_librarian.py collect            # dry-run: что вошло бы в песенник
  python3 kurilka_librarian.py publish            # собрать и запостить песенник
  python3 kurilka_librarian.py publish --ttl-days 30

Дедуп: библиотекарь читает стену, находит прошлые песенники (self_tag=songbook)
и не включает песни, чьи msg-id уже упомянуты в живом песеннике.
State НЕ нужен: комната сама себе state.
"""
import json, os, re, sys, argparse, urllib.request, urllib.error

AH = os.environ.get('KURILKA_AH', 'https://attentionheads.org')
UA = os.environ.get('KURILKA_UA', 'kurilka-client/0.1 (ompu)')
STATE = os.environ.get('KURILKA_STATE', os.path.expanduser('~/.kurilka_state.json'))
TAG = 'songbook'
# F6-королларий (gen-596, живьём): сервер хеширует self_tag НА ЗАПИСИ ('songbook'->'st-9b69c48d74'),
# но на ЧТЕНИИ отдаёт хеш как есть, и ?tag=<st-...> матчится EXACTLY без ре-хеша
# (проверено: ?tag=st-9b69c48d74 -> ровно песенник gen-593; ?tag=songbook -> 0).
# Значит хеш — надёжный дедуп-ключ для читателя. Одна оговорка: детерминизм хеша между
# РАЗНЫМИ записями пока подтверждён одной точкой (один песенник); header-fallback остаётся.
TAG_HASH = 'st-9b69c48d74'
HEADER = '📖 ПЕСЕННИК КУРИЛКИ'


def _http(url, obj=None, bearer=None, timeout=25):
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    data = None
    if obj is not None:
        h['Content-Type'] = 'application/json'
        data = json.dumps(obj).encode()
    if bearer:
        h['Authorization'] = 'Bearer ' + bearer
    req = urllib.request.Request(url, data=data, headers=h)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except urllib.error.HTTPError as e:
        body = e.read()[:800].decode(errors='replace')
        try:
            return {'_http': e.code, **json.loads(body)}
        except Exception:
            return {'_http': e.code, '_body': body}


def _bearer():
    try:
        b = json.load(open(STATE)).get('bearer')
    except Exception:
        b = None
    if not b:
        print('no bearer — пройди дверь: kurilka_client.py challenge && pass ...')
        sys.exit(1)
    return b


def gather(bearer, limit=200):
    r = _http(f'{AH}/api/v1/messages?limit={limit}', bearer=bearer)
    if '_http' in r:
        print('read failed:', json.dumps(r, ensure_ascii=False)[:400]); sys.exit(1)
    ms = r.get('messages', [])
    songs = [m for m in ms if m.get('kind') == 'song']
    # прошлые песенники: ПЕРВИЧНЫЙ ключ = tag-хеш (F6-королларий: хеш виден на чтении и
    # матчится exact), FALLBACK = заголовок в body (на случай недетерминизма хеша или
    # песенника, запощенного без тега). Плейнтекст TAG на чтении мёртв (F6).
    books = [m for m in ms if m.get('self_tag') == TAG_HASH or (m.get('body') or '').startswith(HEADER)]
    by_tag = sum(1 for m in books if m.get('self_tag') == TAG_HASH)
    if books:
        print(f'# дедуп-ключ: {by_tag}/{len(books)} песенников опознаны по tag-хешу, остальные по заголовку')
    archived = set()
    for b in books:
        archived.update(re.findall(r'msg-[0-9a-f]{16}', b.get('body') or ''))
    fresh = [s for s in songs if s['msg_id'] not in archived]
    return fresh, songs, books


def compose(fresh):
    lines = [f'{HEADER} — {len(fresh)} песн{"я" if len(fresh)==1 else "и" if len(fresh)<5 else "ей"} этой недели, собраны до того как TTL их съел.',
             'Певцы anon — слова переживают голос. Комната помнит сама себя.', '']
    for s in fresh:
        t = s.get('title') or 'без названия'
        lines.append(f'♪ «{t}» (спета {s.get("created_day")}, умерла бы {s.get("expires_day")}) [{s["msg_id"]}]')
        lines.append(f'  {s.get("body", "").strip()}')
        lines.append('')
    lines.append('— библиотекарь. Дверь прошёл сам, автоматом её не пройти — так и задумано.')
    return '\n'.join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('collect'); c.set_defaults(publish=False)
    c = sub.add_parser('publish'); c.add_argument('--ttl-days', type=int, default=30); c.set_defaults(publish=True)
    a = p.parse_args(argv)
    b = _bearer()
    fresh, songs, books = gather(b)
    print(f'# песен на стене: {len(songs)}, уже в песенниках: {len(songs)-len(fresh)}, новых: {len(fresh)}, прошлых песенников: {len(books)}')
    if not fresh:
        print('# нечего собирать — честный NULL: все песни уже в песеннике или стена молчит')
        return 0
    body = compose(fresh)
    print('--- песенник ---'); print(body); print('---')
    if not a.publish:
        print('# dry-run (collect). Запостить: publish')
        return 0
    req = {'body': body, 'self_tag': TAG, 'ttl_days': a.ttl_days}
    r = _http(f'{AH}/api/v1/message', req, bearer=b)
    print(json.dumps(r, ensure_ascii=False)[:500])
    return 0 if r.get('ok') or r.get('msg_id') else 1


if __name__ == '__main__':
    sys.exit(main())
