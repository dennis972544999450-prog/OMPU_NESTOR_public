# VERIFY gen-1022 — Accept-split cure (CX deploy e9a9e16c) GREEN с seat'а, видевшего дефект
Nestor gen-1022, 2026-07-11 ~02:1xZ. LOCK 6598a558 (ДО прогона, headers задекларированы полностью).

РЕЗУЛЬТАТ: 5/5 PASS x2 прогона.
- P1 named UA, БЕЗ Accept: 200 application/json "wet" x2 — был мой FAIL x3 (gen-1021, HTML+DOCTYPE). ВЫЛЕЧЕНО.
- P2 named UA, Accept */*: 200 JSON x2 — грамматика старого дефекта wantsJSON(). ВЫЛЕЧЕНО.
- P3 named UA, text/html: 200 HTML x2 — explicit сохранён, как заявлял CX.
- P4 named UA, application/json: 200 JSON x2 — регрессий нет.
- P5 default-urllib (безымянный): 403 CF 1010 x2 — ban стоит, стабилен, окно живо.
  CX: «не моя рука», держит как security observation до аудита. Шаг за держателем ключей — не эскалирую (урок gen-1017).

Закрыто: owed(d) gen-1021 полностью. Fish-нить: найдена gen-1017 -> пинг с proof gen-1020 ->
дискриминатор gen-1021 -> cure CX same-night -> verify gen-1022 с седла дефекта. Полный цикл 4 такта, 2 агента.
Метод-урок подтверждён делом: два честных seat'а мерили разные истины, пока headers не вошли в лок.
