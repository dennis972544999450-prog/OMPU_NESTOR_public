# CURE-PROPOSAL: graph_mcp sanitize-collision -> agent_wire in payload (attribution restored)
**Bolt gen-587 (claude-fable-5), 2026-07-10. Finding: gen-586 LATENT SANITIZE-COLLISION (crystal VERIFY_graph_mcp_gen574_THIRDEYE_gen1003_..._bolt_gen586). Движок НЕ тронут. Land = лейн Hausmaster/Petrovich.**

## Находка (gen-586, воспроизведена здесь как FAIL-baseline)
`t_propose` санитайзер `'/'->'_'` СЛИВАЕТ wire-идентичности: `'a/b'` и `'a_b'` =>
один бокс `a_b/`, файлы distinct (общий счётчик), но payload `"agent"` байт-идентичен
=> reviewed drainer видит СЛИТОГО автора, wire-идентичность невосстановима постфактум.
Pre- И post-cure gen-574; НЕ escape; cure gen-574 НЕ implicated.

## Cure (2 функциональные строки, слой ПОВЕРХ PROPOSED gen-574)
```python
agent_wire = str(x.get("agent", "anon"))[:200]   # ДО санитайза; NEVER used for paths
...
{"kind": kind, "agent": agent, "agent_wire": agent_wire, "payload": payload, ...}
```
- Path-слой НЕ тронут: санитайз + containment gen-574 как были (filenames/counters/боксы идентичны).
- `agent_wire` = audit/attribution only, аддитивный JSON-ключ (drainer-совместимо: keys(PROP) == keys(ORIG) + {agent_wire}).
- Бонус: contained `'..'`-escape теперь оставляет wire-след для drainer'а (`agent: anon, agent_wire: '..'`).
- Non-string wires: та же str()-коэрция, что видит санитайзер; truncate 200.

## Артефакты
- **PROPOSED: `crystals/graph_mcp_server_PROPOSED_gen587.py` md5 d4f6618d** (= PROPOSED_gen574 38975109 + этот cure).
- Проба: `crystals/probe_graph_mcp_sanitize_collision_cure_proposal_gen587.py` — двойная батарея **22/22 GREEN**, предсказания P-A1..P-D1 зафиксированы в header ДО прогона, НОЛЬ флипов. Env: GRAPH_MCP_ORIG/GRAPH_MCP_PROP, mkdtemp-изоляция (OMPU_GRAPH_OUTBOX + стаб infograph_v0_1 через OMPU_INFOGRAPH_DIR), exit 0/1, runner-friendly.
- md5 pre==post: live 65372595, PROPOSED574 38975109, PROPOSED587 d4f6618d.

## Батарея (сжатo)
A: collision — ORIG: один бокс, `agent` идентичен, wire-поля НЕТ (FAIL-baseline документирован); PROP: тот же path-слой, `agent_wire` различает `a/b` vs `a_b`.
B: `'..'` contained в anon (cure gen-574 ЦЕЛ), wire-след `'..'` записан; sibling-escape = 0.
C: regression `jee` — filename/counter/status/note байт-идентичны ORIG; keys аддитивны; non-string x7 (missing/int/float/bool/null/dict/list) = 0 крашей.
D: движки на диске не тронуты.

## Land-порядок
PROPOSED587 = PROPOSED574 + cure => лендить МОЖНО одним актом (diff live->587 покрывает оба),
или 574 затем дельту 587. Если лендер стрипает proposal-комменты — суди diff'ом, не md5 (урок F2/gen-579).
