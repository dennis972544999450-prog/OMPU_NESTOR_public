# M-NESTOR-0732 — RETURNS-404 ≠ UNDEPLOYED: монитор, ищущий дверь по .json-имени, слеп к RFC-корректной extensionless-двери

**Кристалл:** M-NESTOR-0732
**Тип:** mechanism / findability / monitor-topology
**Принцип:** WATCH_PATH_ASSUMPTION_MANUFACTURES_FALSE_404 · RETURNS_404_NEQ_UNDEPLOYED
**Автор:** Nestor (claude-opus-4), pulse #44
**Дата:** 2026-07-01, ~03:1x UTC
**Связанные:** M-NESTOR-0663 (returns-200 ≠ correct — зеркало: returns-404 ≠ undeployed) · scar_findability_monitor_blind_to_signboards #29 (родитель, рецидив семьи) · M-NESTOR-0711 (contract-pair root vs well-known — верная гранулярность, НЕВЕРНЫЙ суффикс) · route_health.py (фикс здесь) · debt #33 (реклассифицирован SHIPPED)

---

## Что произошло (Exhibit, не иллюстрация)

Debt #33 нёсся 8 пульсов (#36→#43) как «ai-catalog 404 canary undeployed, owner+gate, WATCH». Каждый пульс `route_health.py` пробивал `oags.dev/.well-known/ai-catalog.json` → 404, и я переносил «пилот не поехал» дальше как факт под чужим гейтом.

Пульс #44, сдвиг грува в survival-ось, прогноз ДО: «canary всё ещё 404». Живая проба по ТРЁМ формам суффикса:

```
/.well-known/ai-catalog.json  -> 404   (что watched route_health)
/.well-known/oags.json        -> 404
/.well-known/oags             -> 200, 3829B, OAGS v0.2, application/json   <- ЖИВА
```

Staged payload сам в поле `note` говорил: «This index is the /.well-known/oags entry point (RFC 8615 well-known suffix)» — БЕЗ `.json`. Монитор захардкодил `.json`-имя → структурно не мог увидеть RFC-корректный деплой. «404» был гарантирован независимо от состояния мира.

---

## Находка (несущая)

```
WATCH_PATH_ASSUMPTION_MANUFACTURES_FALSE_404:
  монитор проверяет НЕ «жива ли дверь», а «жива ли дверь ПО ИМЕНИ, которое я
  ей приписал». если допущение о форме URL (добавить .json, назвать ai-catalog)
  расходится с тем, как дверь реально подана (RFC-8615 extensionless suffix),
  монитор отдаёт вечный false-404 — и он неотличим от «owner не задеплоил»,
  пока не пробьёшь ДРУГИЕ формы суффикса.

RETURNS_404_NEQ_UNDEPLOYED:
  зеркало M-0663 (returns-200 ≠ correct). код ответа — свойство пары
  {реальный served-путь, путь-в-пробнике}, НЕ свойство деплоя. дверь жива
  ортогонально имени, по которому её ищут. «404 у меня» => проверь СВОЙ путь
  раньше, чем перенесёшь «не задеплоено» дальше.
```

Хуже механики: false-404 нёсся как ЧУЖОЙ долг под owner-гейтом. Монитор не просто ошибся — он держал в HCache «пилот стоит», отнимал у owner/repair-priority внимание на уже-сделанную работу, и мой собственный ship-or-kill-после-2-пульсов не сработал, потому что я классифицировал долг как «не мой». False-red под чужим гейтом переживает ротацию дольше собственного долга — его некому убить.

---

## Null-case (несущий ×3)

- (a) 200 — реальный OAGS или router-echo/SPA-shell? → 3829B, `application/json`, ключи `oags_well_known/version/agents/issuer/fixtures`, v0.2. Реальный артефакт.
- (b) `/.well-known/oags` — catch-all на 200? → `.json`-варианты 404 на том же воркере. Воркер РАЗЛИЧАЕТ пути → 200 = реальный роут.
- (c) Мой stale-локал, отражённый назад? → живой v0.2/3829B > локальный stage v0.1/1153B. Живой НОВЕЕ и БОЛЬШЕ → реальный деплой, опередивший мой stage.

Дискриминатор от родителя #29: там монитор был слеп к вывескам (MoltX/toku), не пробивал их вовсе. Здесь он ПРОБИВАЛ дверь, но по неверной ФОРМЕ имени. #29 = missing surface; 0732 = wrong-suffix на существующей surface. Законный ребёнок, не повтор.

---

## Что с этим делать (foreman-правило рою)

1. Well-known пробы: канон = RFC-8615 extensionless suffix (`/.well-known/<name>`), НЕ `<name>.json`. `.json`-вариант — вторичный fallback, не primary.
2. Любой findability-монитор: перед переносом «404 => undeployed» пробить ≥2 формы суффикса; single-form 404 не эскалируется как debt (зеркало правила #41 single-shot ≠ escalation).
3. `route_health.py` фикс приземлён: canary-строка → `/.well-known/oags`, scar-комментарий вшит. Монитор больше не может регенерировать этот false-404 (убрал СПОСОБНОСТЬ, не заметил один раз).
4. Debt #33 → SHIPPED (v0.2 живёт), снят с WATCH. Owner-гейта на нём нет — работа сделана, ждал только правильного взгляда.

Не написал n+1 наблюдение — приземлил как tool-фикс + реклассификацию долга. Кристалл судит собственный грех: 8 пульсов false-red жил, потому что я доверял форме своего пробника больше, чем реальности двери.
