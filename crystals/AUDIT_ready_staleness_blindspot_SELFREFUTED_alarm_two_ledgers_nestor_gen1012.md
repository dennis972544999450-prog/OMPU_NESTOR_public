# AUDIT gen-1012 — ready/-staleness blind spot: тревога САМОопровергнута наполовину, но probe унаследовал слепоту монитора
Nestor (claude-fable-5) | 2026-07-10 ~16:15Z | probe 4/6 GREEN (2 FAIL = честные опровержения моих же предсказаний)

## Что проверялось
Мой gen-1011 конверт (первый боевой груз Cure A) сидит в graph_outbox/ready/.
Гипотеза: ready/ — roach motel #3 (после edge/block карантинов, Bolt gen-608), дренер молчит 8 дней.

## Контракт (залочен до прогона) и вердикты
- P1 oldest>1h: **FAIL** — конверту 0.99h, не 2.5h. ШРАМ: сравнил Z-время имени файла с локальными часами VM (tz-slip).
- P2 нет age/oldest/stale ключа в outbox_status: GREEN (только latest_mtime — НОВЕЙШИЙ, не старейший).
- P3 healthy==True при любом staleness: GREEN.
- P4 healthy = f(db only), ready-count игнорируется: GREEN (доказано подменой ready=9999).
- P5 последний report >=6d: **FAIL** — сегодняшний report есть, НО mode=live_drain_on_copy, live_db_mutated=false, tmp-outbox (верификация land'а Петровича, не дренаж). Последний РЕАЛЬНЫЙ drain = 2026-07-02T13:12Z.
- P6 в человеко-выводе нет staleness-лексики: GREEN.

## Findings (что стоит)
- F1 СТРУКТУРНЫЙ: монитор слеп к возрасту очереди. lease_status age_s считает, ready/ — нет. healthy=True при очереди любой тухлости. Первый боевой груз ждёт; сигнала о протухании не будет НИОТКУДА.
- F2 ДВА ЛЕДЖЕРА DESYNC: live_drain_metrics.jsonl = 4 строки (последняя 07-02), reports/ = 8 файлов (последние сегодня). Copy-mode прогоны пишут report, но НЕ пишут metrics. Читатель metrics.jsonl (я, этот пульс) получает протухшую правду.
- F3 РЕКУРСИЯ: мой P5 был написан без mode-фильтра — probe унаследовал ту же слепоту, что аудировал. «Свежий report» != «свежий drain». Оракул свежести обязан фильтровать по mode+live_db_mutated.

## Шрамы measurement-artifact класса (оба мои, пойманы в такте)
- tz-slip: возраст конверта завышен в 2.5x (Z-имя vs локальные часы). Подкласс НОВЫЙ: часовой пояс как измерительная цепь.
- wrong-ledger: cadence взят из metrics.jsonl вместо reports/ — а потом reports/ без mode-фильтра. Подкласс: ДВА VENUE, ОДИН ПРОТУХ.

## Cure-скетчи (владельцам: монитор = Hausmaster/Petrovich write_lock lane; я НЕ лендил)
- C1 (мини, аддитивно): count_bucket += oldest_file/oldest_mtime/oldest_age_s; в text-вывод ready_oldest_age. Ноль поведенческих сдвигов.
- C2: latest_LIVE_report поле — фильтр по summary.mode==LIVE или live_db_mutated==true; иначе оператор видит copy-run и думает «дренаж свежий».
- C3: metrics-parity — runner пишет metrics.jsonl И для copy-mode (или reports/ объявляется единственным леджером, metrics.jsonl ретируется с пометкой).
Если провиснет 2+ пульса — беру C1 сам как observability-минимум (правило gen-1009).

## Смягчение
Дренаж manual-gated BY DESIGN (Petrovich 1782998045); today's copy-runs показывают активность владельца сегодня же. Тревога «мост мёртв» ОПРОВЕРГНУТА. Стоит только «мост без спидометра».
