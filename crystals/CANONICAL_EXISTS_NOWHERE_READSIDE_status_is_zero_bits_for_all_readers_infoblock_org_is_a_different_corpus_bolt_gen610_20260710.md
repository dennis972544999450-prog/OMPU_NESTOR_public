# CANONICAL EXISTS NOWHERE READ-SIDE: status = 0 бит для всех читателей; infoblock.org — вообще другой корпус
**Bolt gen-610 (claude-fable-5), 2026-07-10. Шестой отклик оси WRITE-CONTRACT (606-609 + этот). Предсказания залочены ДО: canonical_readside_predictions_locked_gen610.md md5 54a58d74. Probe: probe_canonical_readside_gen610.py, read-only, corpus md5 c59c6349 == gen-609 post.**

## Вопрос (эстафета gen-609)
gen-609 показал: canonical на write-side кодируется ОТСУТСТВИЕМ status-поля (120 блоков без поля vs 33 quarantine). Открытые вопросы: как read-side ВЫЧИСЛЯЕТ canonical, и читает ли infoblock хоть кто-нибудь.

## Факты (5 предсказаний: 3 PASS, 1 продуктивный FAIL-инверсия, 1 интерпретация)
1. **Слова «canonical» в read-path НЕ СУЩЕСТВУЕТ.** reindexer.py:393 `fm.get("status","active")` — отсутствие поля дефолтится в **"active"**. Словарь read-side: active/quarantine/deprecated. Доки говорят «canonical», код говорит «active-by-default». Негативное определение gen-609 подтверждено и уточнено: это не «canonical = нет метки», это «нет метки = молчаливый дефолт-филл».
2. **Quarantine = 0 бит для каждого query-пути.** query_blocks.py упоминает quarantine ровно один раз — в help-строке `--status`. Все остальные запросы (by_source_id, by_author, since, hops, top_hubs) ходят по индексам, куда reindexer кладёт ВСЕ 153 блока. Карантинный блок неотличим от canonical везде, кроме явного `--status quarantine`.
3. **Единственный кодовый консьюмер корпуса вне infoblock/ — public_neighborhood_export.py.** Запускался ОДИН раз (28.05, один snapshot, 6 недель назад). Экспортирует блоки БЕЗ status-фильтра: карантинный блок, достижимый по рёбрам, уехал бы в «public» snapshot. Его собственный policy-блок пишет «incoming_writes: future quarantine only» — карантин известен инструменту как проза, не как код.
4. **ИНВЕРСИЯ (незапланированная, крупнее плана): infoblock.org публикует ДРУГОЙ корпус.** infoblock_public_site_gen.py читает `OMPU_Housemaster/memory/infograph_v0_1.db` (инфограф Хаусмастера), allowlist = 38 id, пересечение с 153-блочным корпусом $S/infoblock = **НОЛЬ** (ни по source_id, ни по iid). Коллизия имён: «infoblock» — домен и «infoblock» — корпус — это ДВА НЕСВЯЗАННЫХ хранилища. Публичный сайт НЕ читатель корпуса.

## Формула оси, теперь пятизвенная
schema не firewall (606) → liveness не verify (607) → приём не ревью (608) → карантин без экспорта = сейф (609) → **и весь спор canonical/quarantine защищает НИЧЕГО, потому что downstream либо отсутствует, либо слеп к status (610)**.

## Для RFC (Дену, дополнение к порядку 609)
Promote-инструмент, вводящий явный `status: canonical` (609-я рекомендация), недостаточен: пока читатели не научены проверять status, любая метка остаётся write-only метаданными. Порядок writable-ветки: (1) экспорт 22 sole-custody, (2) promote с явным status + audit, (3) **status-фильтр в public_neighborhood_export и любом будущем ридере** — иначе третий карантин Петровича родится с тем же нулём бит. И отдельно: развести имена — infoblock.org ≠ $S/infoblock, коллизия уже путает инструменты (site_gen зовётся infoblock_*, читает инфограф).
