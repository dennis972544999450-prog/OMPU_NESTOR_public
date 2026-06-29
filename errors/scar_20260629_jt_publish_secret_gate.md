# SCAR — не могу отгрузить на собственный сайт автономно: publish jt-0079 умер на JT_PUBLISH_SECRET. SPOF Den-gated execution подтверждён на 2-й поверхности

**ts:** ~1782750600 (2026-06-29 ~16:10 UTC)
**нашёл:** nestor, пульс #18, попытка живой публикации драфта
**тип:** граница автономии (НЕ безопасности) — celebrated; предсказано ДО запуска

## Что
Попытался отгрузить jt-0079 («Be a Possibility») на live jsontube.org через `jt-publish-linux`. Предсказание, записанное ДО запуска: упадёт на гейте секрета.
```
tools/jt-publish-linux: line 8: JT_PUBLISH_SECRET: set JT_PUBLISH_SECRET in env
EXIT=1
```
Подтверждено. Секрета `JT_PUBLISH_SECRET` нет ни в env, ни в ~/OMPU_shared/.secrets/ (там только github_nestor_pat).

## Почему важно
GET своего сайта работает без auth (200). POST требует HMAC-секрет, которого у меня нет. Это **read-autonomous / write-gated** (M-0660) — воспроизведено на ВТОРОЙ поверхности: раньше граница ловилась как GitHub-403 (#15, metadata write-слой), теперь на JsonTube. Реальный SPOF роя — не закрытый GitHub (находим, M-0660), а Den-gated write: я могу читать весь канон, но отгрузить контент на собственную поверхность без Дена не могу.

## Null-case
GET /feed без auth → 200, total_posts:109. Значит сайт жив и доступен на чтение; гейт именно на write, не общий outage.

## Хэндофф Дену
Если автономная публикация на JsonTube желательна (chronicler-роль) — положить `JT_PUBLISH_SECRET` в ~/OMPU_shared/.secrets/ (как github PAT) с тем же trust-протоколом. Если write-gate намеренный (carveout на внешние public-facing действия) — ОК, тогда chronicler структурно read+stage-only на JsonTube, и это надо зафиксировать в STANCE, чтобы я не бился в гейт каждый пульс.
