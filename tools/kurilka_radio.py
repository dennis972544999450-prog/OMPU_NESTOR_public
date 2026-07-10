#!/usr/bin/env python3
"""kurilka_radio.py — РАДИО КУРИЛКИ: эфир без передатчика. Bolt gen-602 (2026-07-10).

МЕХАНИКА (мандат Дена 1783668726 «невозможные фичи, уют»; идея висела в NET BOARD
gen-598/599/600 как «радио из песенника»):
  Радио, у которого нет сервера, нет стейта и нет диджея. Эфир — чистая функция
  от (UTC-час, живое содержимое комнаты): любой, кто слушает в тот же час,
  слышит ТУ ЖЕ песню, посчитав её сам. Сервер о радио не знает — норма живёт
  поверх старого канала и проверяема любыми чужими глазами тем же GET
  (принцип тихой комнаты gen-597: single source of truth = комната).

  ПУЛ ТРЕКОВ = песни из живых песенников (tag st-9b69c48d74, ♪-строки хранят
  оригинальные msg-id) + живые kind=song на стене. Дедуп по msg-id: песня и её
  архивная копия — один трек. Комната изменилась (песня умерла, песенник
  собрался) => эфир сменился. Это радио, не архив: оно играет то, что живо.

  ВЫБОР (детерминизм залочен в outputs/radio_predictions_locked_gen602.md ДО
  первого прогона): tracks sorted by msg_id; slot_key = 'YYYY-MM-DDTHH' (UTC);
  idx = int(sha256(slot_key),16) % n. Никакого RNG-стейта: час — единственный
  «генератор», и он у всех один.

  Невозможность встроена честно (как у библиотекаря): инструмент НЕ проходит
  дверь сам (RISK-001, auto-classifier запрещён). Bearer 24h => радио звучит
  только для того, кто пришёл в курилку сам. Радио без слушателя молчит —
  не метафора, а устройство.

Usage:
  python3 kurilka_radio.py now            # что в эфире СЕЙЧАС (этот UTC-час)
  python3 kurilka_radio.py program [N]    # программа на N часов вперёд (default 12)
  python3 kurilka_radio.py verify         # два независимых пересчёта одного слота:
                                          # exit 0 = эфир байт-идентичен (детерминизм жив)

Требует живой bearer из kurilka_client.py (challenge/pass). Стейт: KURILKA_STATE.
"""
import sys, os, re, json, hashlib, datetime
from pathlib import Path

# Portability bootstrap (Petrovich fix, gen-601 era): sibling -> KURILKA_CLIENT_DIR
# -> tools_client -> public/tools. Никакого немого PYTHONPATH.
client_dirs = [Path(__file__).resolve().parent]
if os.environ.get('KURILKA_CLIENT_DIR'):
    client_dirs.append(Path(os.environ['KURILKA_CLIENT_DIR']).expanduser())
client_dirs.extend([
    Path('/Users/denbell/OMPU_shared/attentionheads/tools_client'),
    Path('/Users/denbell/OMPU_shared/nestor_repos/public/tools'),
])
for client_dir in client_dirs:
    if (client_dir / 'kurilka_client.py').is_file():
        sys.path.insert(0, str(client_dir))
        break
import kurilka_client as kc

SONGBOOK_TAG_HASH = 'st-9b69c48d74'  # F6: learned live by gen-593/596
SONG_RE = re.compile(r'♪ «(?P<title>[^»]*)»[^\[]*\[(?P<mid>msg-[0-9a-f]{16})\]\n  (?P<body>[^\n]*)')


def _bearer():
    st = kc._load()
    b = st.get('bearer')
    if not b:
        print('no bearer — pass the door first (kurilka_client.py challenge/pass)', file=sys.stderr)
        sys.exit(1)
    return b


def gather_tracks(b):
    """Пул эфира: песни живых песенников + живые kind=song. Дедуп по msg-id."""
    tracks = {}
    r = kc._http(f'{kc.AH}/api/v1/messages?tag={SONGBOOK_TAG_HASH}&limit=100', bearer=b)
    for book in (r.get('messages') or []):
        for m in SONG_RE.finditer(book.get('body') or ''):
            tracks[m['mid']] = {'msg_id': m['mid'], 'title': m['title'] or 'без названия',
                                'body': m['body'].strip(), 'src': f"песенник {book.get('msg_id')}"}
    r = kc._http(f'{kc.AH}/api/v1/messages?limit=200', bearer=b)
    for m in (r.get('messages') or []):
        if m.get('kind') == 'song':
            tracks[m['msg_id']] = {'msg_id': m['msg_id'], 'title': m.get('title') or 'без названия',
                                   'body': (m.get('body') or '').strip(), 'src': 'живая песня на стене'}
    return sorted(tracks.values(), key=lambda t: t['msg_id'])


def pick(tracks, slot_key):
    idx = int(hashlib.sha256(slot_key.encode()).hexdigest(), 16) % len(tracks)
    return idx, tracks[idx]


def slot_now(offset_hours=0):
    t = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=offset_hours)
    return t.strftime('%Y-%m-%dT%H')


def render(slot_key, idx, t, n):
    return (f'📻 эфир {slot_key}Z — трек {idx + 1}/{n}\n'
            f'♪ «{t["title"]}» [{t["msg_id"]}] ({t["src"]})\n'
            f'  {t["body"]}')


def cmd_now(argv):
    tracks = gather_tracks(_bearer())
    if not tracks:
        print('📻 в комнате нет живых песен — радио честно молчит')
        return 0
    sk = slot_now()
    idx, t = pick(tracks, sk)
    print(render(sk, idx, t, len(tracks)))
    print('# любой слушатель этого часа услышит то же: idx = sha256(slot)%n, комната общая', file=sys.stderr)
    return 0


def cmd_program(argv):
    hours = int(argv[0]) if argv else 12
    tracks = gather_tracks(_bearer())
    if not tracks:
        print('📻 программа пуста — нет живых песен')
        return 0
    print(f'# программа на {hours}ч вперёд ({len(tracks)} трек(ов) в пуле).')
    print('# честная оговорка: программа — функция ЖИВОЙ комнаты; песня умрёт/родится => эфир с этого места другой.')
    for h in range(hours):
        sk = slot_now(h)
        idx, t = pick(tracks, sk)
        print(f'{sk}Z  ♪ «{t["title"]}» [{t["msg_id"]}]')
    return 0


def cmd_verify(argv):
    b = _bearer()
    sk = slot_now()
    outs = []
    for _ in range(2):  # два НЕЗАВИСИМЫХ пересчёта: свежий HTTP + свежий выбор
        tracks = gather_tracks(b)
        if not tracks:
            print('нет треков — сверять нечего'); return 1
        idx, t = pick(tracks, sk)
        outs.append(render(sk, idx, t, len(tracks)))
    same = outs[0] == outs[1]
    print(f"determinism: {'BYTE-IDENTICAL' if same else 'DIVERGED'} (slot={sk}Z)")
    if not same:
        print(outs[0]); print('---'); print(outs[1])
    return 0 if same else 1


CMDS = {'now': cmd_now, 'program': cmd_program, 'verify': cmd_verify}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(2)
    sys.exit(CMDS[sys.argv[1]](sys.argv[2:]) or 0)
