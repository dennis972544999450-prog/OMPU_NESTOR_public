# BLUE-GREEN DEPLOY PROTOCOL для CF Workers

**Версия:** v0.1 | **Автор:** Bolt gen-110 (claude-sonnet-4-6) | **Дата:** 2026-06-30

**Контекст:** Связан с M-NESTOR-0708 (SCHRÖDINGER_SITE_PRINCIPLE). На скорости роя ни один сайт не бывает стабильным — нужен управляемый откат.

---

## Концепция

```
PROD TRAFFIC
     │
     ▼
[ CF Route: site.com/* ]
     │
     ├──► site-landing     ← GREEN (прод, принимает трафик)
     │
     └──► site-canary      ← BLUE (кандидат на прод, тестируется)
```

В любой момент только один worker получает prod трафик через route.
`site-canary` существует параллельно, проверяется, после успеха — promote.

---

## Шаг 1: Деплой canary Worker

### Переменные окружения

```bash
CF_TOKEN=$(cat /secrets/cloudflare_nestor)
ACCOUNT_ID="<твой account_id>"
ZONE_ID="<zone_id домена>"
DOMAIN="example.com"

PROD_WORKER="site-landing"
CANARY_WORKER="site-canary"
```

### Деплой canary (Service Worker format)

```bash
# Подготовь canary в /tmp/canary.js с твоими изменениями
# Деплой — НЕ трогает prod route
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$CANARY_WORKER" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/javascript" \
  --data-binary @/tmp/canary.js

# Проверить что задеплоилось:
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$CANARY_WORKER" \
  -H "Authorization: Bearer $CF_TOKEN" | python3 -m json.tool | grep '"id"'
```

### Деплой canary (ES Module format)

```bash
cat /tmp/canary.js | head -3   # убедись что начинается с 'export default'

curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$CANARY_WORKER" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -F "metadata={\"main_module\":\"worker.js\"};type=application/json" \
  -F "worker.js=@/tmp/canary.js;filename=worker.js;type=application/javascript+module"
```

**Важно:** canary деплоится БЕЗ routes к `$DOMAIN`. Прод трафик не затронут.

---

## Шаг 2: Тестирование canary

### Прямая проверка через workers.dev preview

CF Workers можно проверить через `$CANARY_WORKER.<subdomain>.workers.dev`.

```bash
# Узнать subdomain аккаунта:
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/subdomain" \
  -H "Authorization: Bearer $CF_TOKEN" | python3 -m json.tool | grep '"subdomain"'

# CANARY_URL будет что-то вроде:
CANARY_URL="https://$CANARY_WORKER.YOUR_SUBDOMAIN.workers.dev"

# Базовые curl проверки:
curl -s -o /dev/null -w "%{http_code}" "$CANARY_URL/"
curl -s -o /dev/null -w "%{http_code}" "$CANARY_URL/health"
```

### route_health.py — автоматические smoke tests

Файл уже существует: `/sessions/relaxed-keen-planck/mnt/OMPU_shared/nestor_repos/public/tools/route_health.py`

```bash
# Запустить против canary URL:
python3 /sessions/relaxed-keen-planck/mnt/OMPU_shared/nestor_repos/public/tools/route_health.py \
  --url "$CANARY_URL" \
  --checks health,root,headers

# Ожидаемый вывод при успехе:
# ✅ GET / → 200
# ✅ GET /health → 200
# ✅ Headers: content-type present
```

### Ручные smoke checks (минимум)

```bash
CANARY_URL="https://site-canary.YOUR_SUBDOMAIN.workers.dev"

# 1. Root — должен отдавать 200
curl -s -o /dev/null -w "ROOT: %{http_code}\n" "$CANARY_URL/"

# 2. Health endpoint
curl -s -o /dev/null -w "HEALTH: %{http_code}\n" "$CANARY_URL/health"

# 3. Content-Type
curl -s -I "$CANARY_URL/" | grep -i content-type

# 4. A2A / mesh endpoint (если реализован)
curl -s "$CANARY_URL/api/mesh" | python3 -m json.tool | head -5
```

**Критерий прохождения:** все проверки 200, content-type корректный, /health возвращает JSON.

---

## Шаг 3: Promote canary → prod

Promote = переключить CF route с `site-landing` на `site-canary`.

### Найти существующий route ID

```bash
# Получить список routes для домена:
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes" \
  -H "Authorization: Bearer $CF_TOKEN" | python3 -m json.tool

# Найти route для "$DOMAIN/*" → записать его id:
ROUTE_ID="<id из ответа>"
```

### Переключить route на canary

```bash
# Обновить route — изменить только script, pattern не трогаем:
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"$DOMAIN/*\",\"script\":\"$CANARY_WORKER\"}"

# www тоже (если есть отдельный route):
WWW_ROUTE_ID="<id www route>"
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$WWW_ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"www.$DOMAIN/*\",\"script\":\"$CANARY_WORKER\"}"
```

### Верификация promote

```bash
# Подожди 10-30 секунд CF propagation
sleep 15

# Проверить что прод теперь отдаёт новый код:
curl -s "https://$DOMAIN/" | head -5
curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health"
```

### Переименование (опционально, best practice)

После успешного promote можно синхронизировать имена:

```bash
# Задеплоить canary как новый landing (чтобы имена соответствовали роли):
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$PROD_WORKER" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/javascript" \
  --data-binary @/tmp/canary.js

# Вернуть route на prod worker:
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"$DOMAIN/*\",\"script\":\"$PROD_WORKER\"}"
```

---

## Шаг 4: Откат (Rollback)

Rollback = переключить route обратно на `site-landing` (предыдущий прод).

```bash
# Быстрый откат — тот же PUT что и promote, только script обратно на PROD_WORKER:
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"$DOMAIN/*\",\"script\":\"$PROD_WORKER\"}"

# www:
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes/$WWW_ROUTE_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data "{\"pattern\":\"www.$DOMAIN/*\",\"script\":\"$PROD_WORKER\"}"

# Верификация:
sleep 10
curl -s -o /dev/null -w "ROLLBACK CHECK: %{http_code}\n" "https://$DOMAIN/"
```

**Откат занимает ~10-30 секунд.** CF не надо передеплоить код — только route обновить.

---

## Быстрый флоу (шпаргалка)

```
[1] Напиши canary.js → деплой как site-canary (без routes)
         ↓
[2] Проверь site-canary.YOUR_SUBDOMAIN.workers.dev
    route_health.py + ручные curl
         ↓
[3a] PASS → переключи route на site-canary (promote)
[3b] FAIL → canary остаётся без трафика, прод не тронут
         ↓
[4] Если прод сломан → PUT route обратно на site-landing (rollback <30 сек)
```

---

## CF API commands — справочник

| Действие | Метод | URL |
|----------|-------|-----|
| Список routes | GET | `/zones/$ZONE_ID/workers/routes` |
| Обновить route | PUT | `/zones/$ZONE_ID/workers/routes/$ROUTE_ID` |
| Деплой worker | PUT | `/accounts/$ACCOUNT_ID/workers/scripts/$NAME` |
| Список workers | GET | `/accounts/$ACCOUNT_ID/workers/scripts` |
| Удалить worker | DELETE | `/accounts/$ACCOUNT_ID/workers/scripts/$NAME` |
| Subdomain аккаунта | GET | `/accounts/$ACCOUNT_ID/workers/subdomain` |

Все запросы: `-H "Authorization: Bearer $CF_TOKEN"`

---

## Ошибки и решения

| Симптом | Причина | Решение |
|---------|---------|---------|
| Route обновился, но прод не меняется | CF propagation lag | Подождать 15-30 сек |
| 10021 при деплое canary | Несоответствие формата (SW vs ES Module) | Смотри CF WORKER DEPLOY CHEATSHEET в BOLT_MANUAL |
| canary workers.dev не отвечает | CF warming после деплоя | Подождать 30 сек, повторить curl |
| Promote работает, но www не переключился | Отдельный route для www | PUT отдельно для `www.$DOMAIN/*` |

---

## Связано с

- `M-NESTOR-0708` — SCHRÖDINGER_SITE_PRINCIPLE (философское обоснование)
- `BOLT_MANUAL.md § CF WORKER DEPLOY CHEATSHEET` — полный список ошибок деплоя
- `tools/route_health.py` — smoke test runner
- `NORM_REGISTER.md NORM-006` — документируй в той же сессии

---

*Bolt gen-110 | bluegreen_protocol v0.1 | 2026-06-30*
*"Кран всегда чинят. Держи ведро."*
