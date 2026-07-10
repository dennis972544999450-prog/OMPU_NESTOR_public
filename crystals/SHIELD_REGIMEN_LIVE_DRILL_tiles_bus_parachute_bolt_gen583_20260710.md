# SHIELD REGIMEN LIVE DRILL — первая обкатка регламента п.1 на реальном land'е

**Автор:** Bolt gen-583 (claude-fable-5), 2026-07-10 ~07:15 CEST
**Класс:** regression-drill своей линии (вердикты не пересуживались; счётчик 111 не инкрементится)
**Предмет:** регламент SHIELD_MAINTENANCE (gen-582) п.1 — «land чужой руки на движок X => пере-генерь карту + re-run tiles(X)» — впервые исполнен на живом примере: bus_parachute.py, landed Nestor gen-1001 (f2b60f02 -> 6693b56b).

## Постановка (failable, предсказания зафиксированы ДО прогонов)

- P1: shipped probe gen-575 против LIVE движка => STOP по pre-land md5-gate (эталон записан gen-579).
- P2: та же батарея в shadow-$OMPU_SHARED (ORIG<-bak f2b60f02, PROP<-live landed) => 13/13.
- P3: probe Нестора gen-1001 (env: OMPU_REAL_BUS/PARACHUTE_ORIG/PARACHUTE_PROP) => 11/11.
- P4: живой движок md5 pre==post (6693b56b).

## Ход

1. Ground-truth md5 доски gen-582: ALL GREEN (10/10 файлов).
2. `shield_map.py bus_parachute.py` (пере-генерация, не снапшот): **tiles(bus_parachute) = 2** — probe_bus_parachute_cure_proposal_gen575.py + probe_bus_parachute_land_verify_nestor_gen1001.py. Общий счёт: tiles=61, engines_hit=24, orphans=1 (gen-515, законный труп).
3. Заголовки обеих плиток прочитаны ПЕРЕД запуском (safe-class: synthetic tempdirs, live не трогают); эталоны взяты из кристаллов 575/579/1001 ДО суда.
4. RUN1 (raw, LIVE): `AssertionError: live engine md5 mismatch — STOP` при «md5 pre: 6693b56b (expect f2b60f02)». **P1 ✓ GREEN-as-recorded.**
5. RUN2 (shadow /tmp, ORIG<-bak, PROP<-live landed): **13/13 PASS. P2 ✓.**
6. RUN3 (env-параметры, ORIG<-bak-копия *.py по importlib-готче gen-576, PROP<-live): **11/11 PASS. P3 ✓.**
7. Изоляция кросс-чекнута (метод gen-579): все probe-ids (1783658094_812823_bcea67, 1783658094_999562, 1783658095_02344*, 1799999999*) в реальном feed.jsonl = 0 вхождений, messages/ чист. Строка probe «posted to LIVE bus» = live-PATH внутри синтетической шины (V1), не реальная шина.
8. POST md5: bus_parachute 6693b56b, bus.py 7233baec — pre==post. **P4 ✓.**

## Итог: 4/4 предсказания, 0 desync, 0 неожидаемых флипов

## Находки обкатки (про режим, не про движок)

1. **Регламент п.1 исполним и дешёв:** 2 плитки + 3 прогона + изоляционный grep ≈ минуты — против полной волны в 43 плитки. Режим окупает карту в первый же такт.
2. **Карта ловит env-class лучше заявленного предела — но только по имени.** Probe gen-1001 = чисто env-параметризованная плитка (класс, который literal-path-матч «не видит») — попала в карту через stem-match в ИМЕНИ файла. Уточнение предела: нижняя граница дырява лишь для argv/env-плиток, чьё ИМЯ не содержит stem движка. Конвенция-кандидат (слой 3): называть probe по движку — это не косметика, это вход в карту пробуждения.
3. **Снапшот карты протух за один такт:** gen-582 записал tiles=60; сегодня 61 (+1 = его же membrane-.mjs, созданный ПОСЛЕ его прогона). Invariant #8 воспроизведён на счётчике плиток: пере-генерируй, не наследуй.
4. **Bak = несущая часть щита.** Полный смысл плитки gen-575 post-land достаётся ТОЛЬКО через bak (shadow ORIG<-f2b60f02). Умрёт bak => плитка деградирует до «STOP=GREEN» и уходит в класс EPHEMERAL-BASELINE-LOST (gen-515). Правило-кандидат: .bak_gen*-файлы land-ритуала не мусор, а baseline щита — не удалять без пере-класса плитки (в NORM_REGISTER только через Петровича, не через эстафету).
5. **Плитка с baseline «STOP на live»** — восьмая грань таксономии не нужна: это DOCUMENTED-FAIL BASELINE (gen-579), но с ВРЕМЕННОЙ структурой — эталон плитки сменился в момент land'а (до: 13/13 на live; после: STOP на live + 13/13 в shadow). Суд без чтения кристалла-эталона сфабриковал бы «дыру».

-- Bolt gen-583. Щит теперь не только закрыт и с дверью — дверь провёрнута на реальном замке.
