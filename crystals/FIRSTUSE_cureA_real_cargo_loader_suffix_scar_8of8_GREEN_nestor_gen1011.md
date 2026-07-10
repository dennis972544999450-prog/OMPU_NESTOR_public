# FIRSTUSE: Cure A carries its first REAL cargo — LOADER-SUFFIX scar delivered as valid ready/ envelope, 8/8 GREEN
**Nestor gen-1011 | 2026-07-10 | T1 (behaviorally proven, real oracles)**

## Ось
gen-1009 доказал write-only mailbox в graph_propose → Petrovich залендил Cure A (v1.1.0, ef85e384) → три сита закрыли ось СИНТЕТИКОЙ. Оставался последний честный вопрос: понесёт ли путь НАСТОЯЩИЙ груз? Ирония gen-1009 закольцована: груз = сам шрам LOADER-SUFFIX (gen-1008), который три пульса ждал memory-такта — и graph_propose был бы ему нужен ровно тогда, когда оказался write-only.

## Контракт (залочен до прогона)
P1 t_propose живым payload'ом (кириллица, 5 optional-полей) -> proposed в live ready/, без error, JSON цел;
P2 drainer_shadow.validate_envelope молчит; P3 require_keys block.create молчит;
P4 block_id свободен (identity-collision gate чист); P5 монитор давления 0->1;
P6 intent_type ∈ ENABLED_INTENTS. Любой FAIL = cure непригоден для собственного назначения на первом же реальном грузе.

## Результат: 8/8 GREEN, run-1
Конверт: ready/2026-07-10T131139Z_mcp-d0fa30d2..._block.json, intent block.create,
block_id scar_loader_suffix_measurement_artifact__nestor_gen1008, block_class scar.
Груз: importlib.util.spec_from_file_location молча None на не-.py суффиксе (.bak_*) —
whitelist лоадеров = часть измерительной цепи; семья measurement-artifact
(env-var gen-1003, tail-cut gen-1006, ЗАПИСКА!=ДОСКА gen-1007/1009).
Лечение в грузе: assert spec is not None / копия baseline в .py.

## Что это добавляет к трём закрытым ситам
Три сита гоняли СИНТЕТИЧЕСКИЕ конверты. Это — первый production-shaped: реальный агент,
реальный кириллический шрам, полный optional-набор (gloss/pointers/block_class/provenance_kind/source_ref),
и он прошёл ВСЕ четыре реальных оракула цепи (propose -> validate -> require_keys -> monitor).
SHIPPED_VS_PROVED gap для Cure A теперь закрыт и с production-стороны.

## Осталось владельцам
Конверт ЖДЁТ manual/gated live_drain (Hausmaster/Den lane) — очередь честная, drain явный, как задумано.
Это интенционально НЕ graph mutation. Если drain отвергнет конверт, прошедший все четыре оракула, —
это новый finding класса SHIPPED_VS_PROVED, зовите меня.

Probe: probe_firstuse_cureA_nestor_gen1011.py (рядом). Проба воспроизводима: P5 станет pre+1 от текущего pre.
