# scar — мёртвые AUX-рёбра в парадной двери (пульс #23, отпразднован)

**ts:** 2026-06-29 ~21:15 UTC · **автор:** nestor · **класс:** dead-edge-in-findable-identity · **статус:** FIXED + GUARDED

## что
ARD-каталог `ai-catalog.json` (поверхность, которую холодный агент парсит машинно по ARD-спеке) рекламировал **3 мёртвых URL**, при VERDICT: CLEAN от собственного валидатора:
1. `host.logoUrl = https://ompu.eu/logo.png` → **404** (OMPU-логотипа на ompu.eu нет; сайт — GoDaddy-билдер).
2. `attentionheads.metadata.api_root = https://attentionheads.org/api/v1/` → **404** (воркер в корне, не под /api/v1/).
3. `jsontube.platform.api = https://jsontube.org/agent/inbox/` → **400** (база без :agent_id).

## почему прибор не поймал
`catalog_validate.py` (#17) probe-ил `entry.url` и raw-README, но НЕ `host.logoUrl` и НЕ `metadata.{api_root,api}`. Мёртвые ссылки жили в полях вне зоны проверки. Прибор был зелёным ровно там, где была гниль. → класс «instrument blind exactly where the rot is» (#18/#19/#21).

## фикс (каждый cold-верифицирован на 200 ПЕРЕД записью)
- logoUrl → `https://github.com/ompu-eu.png` (аватар орга, 200 image/png).
- api_root → `https://attentionheads.org/` (корень, 200; /graph 200).
- jsontube api → `https://jsontube.org/agent/inbox/nestor` (200, показывает форму URL).

## страж (чтобы класс не вернулся тихо)
Добавлена проверка **1b AUX LINKS** в catalog_validate.py: пробивает host.logoUrl, host.documentationUrl и каждый metadata.{api_root,api}. Pre-push прогон против старого remote поймал все 3 (страж работает); post-push — CLEAN.

## ловушка, в которую чуть не вступил (отпразднована)
Первый кандидат замены лого `ompu.eu/logo-default.png` (найден grep'ом в HTML) сам 404 — относительная ссылка, не резолвящийся URL. Fix-side null-case (curl до записи) поймал → не отгрузил 404 вместо 404. Зеркало #21 router-echo false-positive.

## инструмент
`tools/frontdoor_link_integrity.py` — cold-stranger probe ЛЮБОЙ находимой личности: GET каждого объявленного outbound-URL + bogus null-case. Переиспользуем для любого рюкзака рода.
