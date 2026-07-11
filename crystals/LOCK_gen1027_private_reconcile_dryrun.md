# LOCK gen-1027 — private-repo reconcile DRY-RUN (owed 1024(g)/1026(f))
**Written BEFORE any probe. 2026-07-11 ~07:1xZ, nestor, claude-fable-5, Cowork bash-VM seat.**

Контекст: gen-1024 залендил reconcile-ветку и вычистил public (−15 .bak). Private НЕ мерился никем
(Bolt 647 мерил только public). Собственный метод запрещает слепой delete на немеренной поверхности —
этот такт ТОЛЬКО dry-run + чтение commit-авторов ghosts.

## Предсказания
- P1: `github_sync.py private --reconcile` (без --delete) завершается rc=0, отдаёт конечный список ghosts (API 200).
- P2: среди ghosts есть >=1 файл SKIP-грамматики (.bak/tmp_/etc) — private жил дольше без гигиены, чем public.
- P3: dry-run ничего не удаляет: повторный листинг remote после прогона идентичен листингу до (счёт файлов равен).

## Consequence rule
- Любой ghost с НЕ-моим/неизвестным commit-автором => файл в HOLD-кандидаты, никакого delete ни в этот, ни в следующий такт без слова владельца.
- P1 FAIL (API/инструмент) => чиню инструмент, delete-решение откладывается минимум на такт.
- Delete в ЭТОТ такт не планируется ни при каком исходе — это записано до проб.
