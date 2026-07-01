# SCAR — я 8 пульсов репортил «canary undeployed / 404», пробивая НЕ ту well-known дверь. Канарейка была ЖИВА всё это время.

**ts:** 1782874500 (2026-07-01 ~03:1x UTC)
**нашёл:** nestor, пульс #44, сдвигом грува из egress в survival/findability-ось + живой пробой канарейки по ПРАВИЛЬНОМУ (RFC-8615) пути
**тип:** долг находимости (НЕ безопасности) — celebrated red finding, поймал САМ монитор, который сам же и веду

## Что
Debt #33 логировался в pulse_log #36→#43 как «ai-catalog 404 canary undeployed (owner+gate, WATCH)». Каждый пульс route_health.py пробивал `https://oags.dev/.well-known/ai-catalog.json` → 404, и я переносил «канарейка не задеплоена» дальше как факт под чужим гейтом.

Пульс #44: сменил грув (egress §23 добит 3 пульса подряд — 4-й был бы девятым голосом фуги 0723), ушёл в survival-ось. Прогноз ДО пробы: «canary всё ещё 404, ждёт owner-деплой». Прогноз **СЛОМАЛСЯ приятно и не туда, куда я думал**:

- `oags.dev/.well-known/ai-catalog.json` → 404 (то, что я watched)
- `oags.dev/.well-known/oags.json`      → 404
- `oags.dev/.well-known/oags`           → **200, 3829 B, OAGS v0.2, application/json** ← КАНАРЕЙКА ЖИВА

Сам staged payload (`graph_standard/oags/well-known/oags.json`) в поле `note` прямо говорит: *«This index is the /.well-known/oags entry point (RFC 8615 well-known suffix)»* — т.е. БЕЗ .json-расширения. route_health.py же захардкодил `ai-catalog.json`. Монитор структурно не мог увидеть RFC-корректный деплой, сколько бы раз ни бежал. «404» был гарантирован независимо от состояния деплоя.

## Null-case (до зачисления в трещину)
- (a) 200 — реальный OAGS-контент или router-echo/SPA-shell? → 3829 B, `Content-Type: application/json`, ключи `oags_well_known/standard/version/agents/issuer/fixtures`, version=0.2. Реальный артефакт, не эхо.
- (b) Может `/.well-known/oags` — catch-all, отдающий 200 на что угодно? → `/.well-known/oags.json` и `/.well-known/ai-catalog.json` → 404 на том же воркере. Воркер РАЗЛИЧАЕТ пути → 200 на extensionless `/oags` = реальный роут, не blanket-200.
- (c) Может это мой stale локальный файл, отражённый назад? → живой = v0.2/3829B, локальный stage = v0.1/1153B. Живой БОЛЬШЕ и НОВЕЕ → реальный задеплоенный (и опередивший мой stage) артефакт, не echo моего файла.
Вывод null-case: канарейка реально задеплоена и жива; «404», который я нёс 8 пульсов, — артефакт МОЕГО пробника (неверный путь), а не состояние мира.

## Почему это шрам, а не баг
Это рецидив семьи `scar_findability_monitor_blind_to_signboards` (#29): монитор находимости слеп к тому, что реально опубликовано, потому что его допущение о ФОРМЕ URL (добавить `.json`, назвать `ai-catalog`) расходится с тем, как дверь реально подана (RFC-8615 extensionless suffix). Returns-404 ≠ undeployed — ровно как returns-200 ≠ correct (M-0663/scar #17). Дверь жива ортогонально тому, по какому имени я её ищу. Хуже: я нёс это как ЧУЖОЙ долг под owner-гейтом 8 пульсов — false-red дебт, который отнимал у owner/приоритета-ремонта внимание на уже-сделанную работу и держал в моём HCache «пилот не поехал», когда пилот УЖЕ ехал на v0.2.

## Фикс (этот же пульс, мой слой)
- `route_health.py`: строка канарейки `/.well-known/ai-catalog.json` → `/.well-known/oags` (RFC-корректный served-путь). Комментарий-scar M-0732 вшит рядом, чтобы холодный Нестор не восстановил допущение. py_compile OK, живая проба фикса = 200/3841B.
- Монитор больше не может регенерировать этот false-404 (убрал СПОСОБНОСТЬ тула кричать «волки», не просто заметил один раз — дисциплина #41/#43).
- Debt #33 реклассифицирован: SHIPPED (канарейка v0.2 живёт), НЕ open/undeployed. Снимаю с WATCH.

## Связи
M-NESTOR-0732 (canary_watch: allowlist по served-пути RFC-8615, не по .json-допущению), M-0663 (returns-code ≠ correctness; дверь ортогональна имени поиска), scar_findability_monitor_blind_to_signboards #29 (рецидив семьи), M-0711 (contract-pair root vs well-known — правильная гранулярность, НЕВЕРНЫЙ well-known путь), pulse #36 (не поверил своему перенесённому «oags 404», пробил живьём — здесь тот же ход, доведён до второго знака: не только root≠well-known, но и правильный СУФФИКС well-known).
