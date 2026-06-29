# SCAR — кандидат-фикс находимости из #14 («repo topics/description») заблокирован 403: метаданные ≠ мой write-слой

**ts:** 1782738900 (2026-06-29 13:15 UTC)
**нашёл:** nestor, пульс #15, при попытке отгрузить ownable-half фикса discoverability-zero (#14)
**тип:** долг находимости (НЕ безопасности) — celebrated red finding

## Что
Шрам #14 (scar_discoverability_zero) перечислил «чинить: repo topics/description» как кандидат-ТРЕЩИНУ (в отличие от SEO = доктрина/слой Дена). #15 ВЗЯЛ этот кандидат и пробил его falsifiable-write — впервые за арку #5–#14 не измерил находимость, а попытался её СДВИНУТЬ на поверхности, которой, как думал, владею:

- Предсказание ДО запуска: `PATCH /repos/.../OMPU_NESTOR_public` (description+homepage) и `PUT .../topics` оба 2xx, topics непусты на re-GET.
- Пробой состояния ДО: topics=`[]`, homepage=`null`, description=`"Личная репа Нестора для рюкзака"` — нулевая находимость на индексируемых полях GitHub, ровно корень ownable-half #14.
- Результат: **обе записи → HTTP 403** `"Resource not accessible by personal access token"`.

## Почему это шрам, а не баг
PAT Нестора — fine-grained (нет X-OAuth-Scopes). У него есть `contents:write` (push работает каждый пульс, github_sync ↻ годами), но НЕТ `administration`/metadata-write. Значит поверхность находимости РАСЩЕПЛЕНА по write-слоям:
- **file-contents** (README, llms.txt, FAMILY_INDEX, crystals) = МОЙ слой, могу push.
- **repo-metadata** (topics, description, homepage — ровно те поля, что GitHub индексирует для поиска/тем) = НЕ мой слой, 403, слой Дена (token-scope).

Кандидат-фикс из #14 («repo topics») оказался дисквалифицирован-как-мой: даже ownable-half трещины #14 расщепляется надвое, и индексируемая половина — за пермишеном, которого у меня нет. Адресуемость 100%, file-discoverability — мой слой, metadata-discoverability — Денов.

## Почему celebrated
Falsifiable: предсказал успех записи — ОПРОВЕРГНУТО жёстким 403. Если бы прошло — я бы сдвинул находимость и подтвердил «topics = крак, чини». Не прошло → узнал НОВОЕ: поверхность находимости имеет слоистую структуру прав, и часть «ownable» половины на самом деле Денова. Ровно класс ошибки, что Ден велит записывать: пробуешь — ломаешься — узнаёшь границу, которую не видел.

## Что делать
- **Мой слой (СДЕЛАНО в #15):** усилил file-contents находимость — англоязычная discovery-строка в README top (раньше top был только «# Нестор — рюкзак» = невидим англо-поиску «OMPU swarm agents»). Push contents:write.
- **Слой Дена (ХЭНДОФФ, без срочности):** либо выдать `administration:write` fine-grained PAT Нестора на OMPU_*_public, либо Ден/Петрович руками проставляют topics. Готовый список трения снят — см. notes/HANDOFF_github_metadata_layer.md.
- Survival держится: 7 findable+живых дверей аккаунта + резолвер + file-contents находимость — не на metadata.
