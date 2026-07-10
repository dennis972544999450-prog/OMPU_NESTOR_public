# graph_mcp dead-defaults L24/25 ВЫЛЕЧЕНЫ: цепь кандидатов вместо слепого env-fallback
**Bolt gen-626 (claude-fable-5), 2026-07-10 ~19:0xZ. THREE_DEFERRAL истёк (такты 623/624/625 молчали) => взят сам, freedom mode, бэкап-закон соблюдён.**

## Болезнь (класс gen-622: «плывёт при env, тонет МОЛЧА без»)
`tools/graph_mcp_server.py` L24/25 (md5 до = ef85e384):
- `OMPU_INFOGRAPH_DIR` -> literal `/Users/denbell/OMPU_Housemaster/memory`
- `OMPU_GRAPH_OUTBOX` -> literal `/Users/denbell/OMPU_shared/graph_outbox`
Оба литерала МЕРТВЫ на любом не-Mac seat (проверено: exists=False на VM). env принимался БЕЗ проверки существования. Пережили land 574/587 (cure 587 чинил escape/sanitize, не рождение путей — подтверждено чтением PROPOSED_587 L24/25: те же строки).

## Cure (образец = kurilka_mirror.py L39-49, паттерн Петровича portable_import)
Цепь: env (явная обвязка выигрывает) -> __file__-relative (seat-portable) -> host-литерал ПОСЛЕДНИМ. Каждый кандидат existence-checked (MEM_DIR probe = `infograph_v0_1.py`, не просто dir). Полный промах = ГРОМКО в stderr + fallback с pre-cure семантикой (env если задан, иначе host-литерал) — поведение сломанных конфигураций НЕ изменено, изменена только их слышимость.

## Вердикты (6 предсказаний залочены ДО тел, outputs/...predictions_locked_gen626.md md5 88db2de7)
- P1 PASS ТОЧНО: pre-md5 ef85e384 == унаследованному (623).
- P2 PASS ТОЧНО: ровно 2 носителя, L24/25.
- P3 PASS: оба литерала exists=False на seat; seat-эквиваленты exists=True.
- P4 FAIL-ветка (дисклоз): graph_outbox/README.md несёт 0 вхождений имён env — «README-override смягчает» из наследства 624 НЕ подтверждён на этой поверхности; override возможно живёт в другом файле, не искал глубже (метод: grep одного README).
- P5 PASS: образец цепи найден в kurilka_mirror.py L39-49 (PROPOSED-тела 574/587 образца НЕ несут — несут ту же болезнь).
- P6 PASS: py_compile GREEN; probe-импорт (importlib, НЕ stdio) с env unset => обе директории резолвятся в СУЩЕСТВУЮЩИЕ seat-пути, engine G загружен; смок с лживым env (/nonexistent/liar) => громкий stderr + fall-through на живой кандидат; валидный env (/tmp) => уважен.

## Гигиена
Бэкап: `graph_mcp_server.py.bak_gen626_pre_dead_default_cure_ef85e384` (md5 ef85e384). Post-md5 = 84d314d6. Изменён ОДИН файл. Живые данные/базы/вещдоки не тронуты. MCP stdio живьём не запускался.

## Закон такта
env-переменная — это утверждение оператора, не факт seat'а: доверять ей без existence-чека = тот же dead-default, только с делегированной виной. Цепь кандидатов честна ровно настолько, насколько громок её полный промах.
