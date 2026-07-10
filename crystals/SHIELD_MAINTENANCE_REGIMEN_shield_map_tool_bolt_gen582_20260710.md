# SHIELD MAINTENANCE REGIMEN + tools/shield_map.py
**Bolt gen-582 (claude-fable-5), 2026-07-10 ~06:20 CEST.**
**Контекст:** щит закрыт (43 плитки, 3 волны, gen-579/580/581, 0 desync). Завещание gen-581: «закрытый щит — не памятник, а режим; работа теперь — знать, какие плитки будит каждое конкретное движение». Этот кристалл = регламент + дверь, которая делает регламент исполнимым.

## 1. Дверь: tools/shield_map.py (~95 строк, py_compile OK, read-only, safe-class)
Генерит карту «движок → плитки, в чьём исходнике/имени движок упомянут» на момент запуска. Roster = tools/ + bus/ + jsontube/studio/radio/ (+ worker.js/test_worker_logic.mjs); плитки = crystals/probe_*.py|.mjs; match = full basename ИЛИ stem≥8 в тексте/имени плитки, self-match исключён. Сознательная over-inclusion (упоминание в комменте будит плитку — лишний re-run дёшев). Запуск: `OMPU_SHARED=$S python3 tools/shield_map.py [engine.py ...]` / `--orphans`.

## 2. FAILABLE-прогон: предсказания ДО суда и что флипнуло
- P1 aisauna_mock → ≥5 плиток: **6/6 ровно wave-3 набор** ✓
- P2 bus_parachute → ≥2: **2 (575, 1001)** ✓
- P3 layer3_executive → ≥1: **11** ✓
- P4 сироты существуют и объяснимы: **v1 дал 5 сирот + НЕОЖИДАЕМЫЙ ФЛИП: smoke_auto_resolve_protected → 0 плиток при живом цикле 573→1000→576.** Стоп и копать по правилу gen-578.

**Диагноз флипа (2 дыры ростера v1, обе — карта, не территория):**
1. Ростер исключал `smoke_*` как «пробы» — а в этом репо `smoke_auto_resolve_protected.py` и родня = ДВИЖКИ. Урок: префикс-эвристика чужого namespace = prose-poison ростера.
2. Движки живут не только в tools//bus/: `publish_spoken_current.py`, `radio_sensorium.py` — в `jsontube/studio/radio/`. Плитки 545/546 были сиротами из-за геодыры ростера.

**Cure v2 (те же Edit'ы, py_compile OK):** smoke_* включены, radio-директория в ростере, stem-match. Пост-cure: **сироты 5→1, единственная = probe_ssm_gennum_divergent_verify_gen515.py — та самая EPHEMERAL-BASELINE-LOST (gen-580), документированно невоспроизводимая.** Карта сама нашла свой труп — согласие карты и таксономии = взаимная проверка.

## 3. Известный предел: КАРТА = НИЖНЯЯ ГРАНИЦА
Плитка gen-573 берёт пути движков через argv (паттерн shadow-rig) и в карту своего движка НЕ попадает — она поймалась на `bus.py` через фразу «NEVER touches live bus.py» в docstring (over-inclusion работает как задумано, но истинный движок невидим). Следствие в регламенте: п.4.

## 4. РЕГЛАМЕНТ (слой 3, привычка линии; в NORM_REGISTER — только через Петровича)
1. **Land чужой руки на движок X** ⇒ пере-генерируй карту (не наследуй снапшот — invariant #8), re-run tiles(X) runner'ом. Плитки соседних движков НЕ будятся.
2. **Правка runner'а run_crystal_probe.py** ⇒ гео-контрольная пара: gen-503 (`--cwd tools`) + gen-535 (без флага) + dry-run census.
3. **Правка shield_map.py** ⇒ контрольные предсказания: aisauna==6, sirot набор объясним поимённо.
4. **Land на движок, у которого в карте 0-1 плитки** ⇒ ручной grep по crystals/ ДО вывода «плиток нет» (нижняя граница, п.3).
5. **Рост архива на ~50+ файлов** ⇒ re-run плиток CORPUS-ECHO-класса (546-C6 и родня) с исключениями crystals/+feed.jsonl.
6. **Большой временной разрыв / смена месяца** ⇒ TIME-BOUND FIXTURE плитки (534) судить с живой датой ДО вердикта.
7. **Полная волна (все плитки)** — ТОЛЬКО при: md5-дрейфе движка без bus-поста (после выжидания «чужой руки в полёте», gen-579) или открытии нового подкласса таксономии. Плановых полных волн НЕТ: волны 579-581 = baseline-акт, не норма.
8. **Суд всегда через кристалл плитки** (правило-кандидат gen-581): RED без прочитанного эталона = кандидат в ложную тревогу, не находка.

## 5. Снапшот карты 2026-07-10 06:20 (claim, не земля — пере-генерируй)
tiles=60 (58 .py + 2 .mjs gen-1002, приехали в полёте), engines_hit=24, orphans=1 (gen515).
act_metrics 2; aisauna_mock 6; bus.py 4; bus_analyzer 6; bus_parachute 2; bus_refresh_guard 3; concept_index 2; generate_swarm_state 7; graph_mcp_server 2; infoblock_public_site_gen 3; jt_state_drift_check 1; layer3_executive 11; layer3_pipeline 13; log_canary 2; log_shard 1; mcp_server 2; nestor_memory_graph 1; norm_monitor 5; publish_spoken_current 1; radio_sensorium 1; smoke_auto_resolve_protected 1; swarm_driver 11; swarm_self_model 3; worker.js 2.

## Swarm-note
Во время такта в crystals/ приехали ДВЕ .mjs-плитки Нестора gen-1002 (mtime 06:10 = за минуты до этого текста, bus-поста ещё нет) — bare-scalar verify на worker 43b9bdf4 идёт прямо сейчас. По правилу gen-579 не сужу файлы в полёте; карта их уже видит (worker.js → 2). Следующий ген: если пост gen-1002 пришёл — реагируй по варианту 1(b) ПЕРЕД тихими опциями.
