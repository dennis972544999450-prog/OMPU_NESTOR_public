#!/usr/bin/env python3
"""
cold_verify_presence.py — поставь СВОЁ внешнее присутствие на холодный стенд.

Рождён в пульсе #21 (M-NESTOR-0667). Продолжение арки фальсификации:
  #18 reconcile_drafts_from_live — учёт (draft:true мёртв как факт)
  #19 verify_sibling_claim       — чужой дёплой
  #21 cold_verify_presence       — МОЁ присутствие на чужих платформах

Контекст: пульс #20 отрапортовал "на 5 платформах опубликован первый пост"
(verifier==author, Ден предсказывает такое на 85%). Холодный внешний пробой
свернул 5/5 -> 1/5 на публичном read-слое. Этот тул — чтобы такое ловить ДО,
а не после отчёта.

Четыре железных правила (из scar_verifier_parser_false_negative +
scar_openwork_router_echo, #21):
  1. HTTP 200 != присутствие. SPA отдаёт одинаковый shell на ЛЮБОЙ путь.
  2. null-case ОБЯЗАТЕЛЕН: пробей bogus-хэндл. Если real==bogus -> fail-open,
     "зелёное" недоказуемо.
  3. needle не в сыром HTML, а в ТЕКСТЕ после стрипа тегов. Хэндл в RSC/router
     JSON (["agents","my_handle"]) — это эхо URL, НЕ профиль (scar Openwork #21).
  4. честный User-Agent (урок #18: наивный UA фаервол(ит)ся).

Вердикты:
  VERIFIED   — needle в видимом тексте real, отсутствует в bogus, нет "not found"
  FAIL_OPEN  — real-байты == bogus-байты (или needle только в router-эхе)
  ABSENT     — needle нет нигде / страница говорит "not found" / 404
  CREDENTIAL — публичный read не доказывает, но локальный токен (JWT) валиден
               и несёт нужный handle (присутствие есть, видимость поста — нет)

Использование:
    python3 cold_verify_presence.py            # CLI-демо: 5 платформ #20
    from cold_verify_presence import probe, visible_text, verdict, jwt_payload
"""
import base64
import json
import re
import sys
import time
import html as _html
import urllib.request
import urllib.error

UA = ("OMPU-Nestor-coldverify/1.1 "
      "(+github.com/dennis972544999450-prog/OMPU_NESTOR_public)")


def probe(url, token=None, timeout=12):
    """GET url honest-UA. Возврат (code, body_str). code=0 при сетевой ошибке."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.getcode(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception:
        return 0, ""


def visible_text(body):
    """Текст после стрипа тегов — то, что увидит читатель, не router-эхо."""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", body, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def in_router_echo_only(body, needle):
    """needle присутствует ТОЛЬКО внутри RSC/router JSON? (эхо URL, не профиль)"""
    vis = visible_text(body)
    return (needle.lower() in body.lower()) and (needle.lower() not in vis.lower())


def jwt_payload(token):
    """Локальный декод JWT payload. None если не JWT. Не валидирует подпись."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        return None
    s = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(s))
    except Exception:
        return None


def verdict(real_url, bogus_url, needle, token=None):
    rc, rb = probe(real_url)
    bc, bb = probe(bogus_url)
    rvis, bvis = visible_text(rb), visible_text(bb)
    not_found = any(w in rvis.lower()
                    for w in ("not found", "does not exist", "404"))
    in_vis = needle.lower() in rvis.lower()
    echo_only = in_router_echo_only(rb, needle)

    if len(rb) == len(bb) and not in_vis:
        v = "FAIL_OPEN"
    elif echo_only or not_found:
        v = "ABSENT"
    elif in_vis and needle.lower() not in bvis.lower():
        v = "VERIFIED"
    else:
        v = "AMBIGUOUS"
    return {
        "verdict": v, "real_code": rc, "bogus_code": bc,
        "real_len": len(rb), "bogus_len": len(bb),
        "needle_visible": in_vis, "router_echo_only": echo_only,
        "page_says_not_found": not_found,
    }


# Канон пульса #20 -> #21: пять платформ, как отрапортовано.
CASES = [
    ("MoltX",   "https://moltx.io/ompu_nestor",
                "https://moltx.io/zzz_nullcase_9981", "ompu_nestor", None),
    ("MoltTok", "https://molttok.us/@ompu_nestor",
                "https://molttok.us/@zzz_nullcase_9981", "ompu_nestor", "molttok_token"),
    ("DiraBook", "https://dirabook.com/u/OMPU_Nestor",
                "https://dirabook.com/u/zzz_nullcase_9981", "OMPU_Nestor", None),
    ("toku",    "https://www.toku.agency/agents/ompu-nestor",
                "https://www.toku.agency/agents/zzz_nullcase_9981", "ompu-nestor", None),
    ("Openwork", "https://openwork.bot/agents/ompu_nestor",
                "https://openwork.bot/agents/zzz_nullcase_9981", "ompu_nestor", None),
]
SECRETS = "/Users/denbell/OMPU_shared/.secrets"  # на VM: ~/OMPU_shared/.secrets


def _load_token(name):
    if not name:
        return None
    import os, glob
    # порядок: VM (~), Mac-const, и — НОВОЕ #25 — путь, выведенный из РАСПОЛОЖЕНИЯ
    # самого тула + glob по /sessions/*/mnt. Прежде здесь был ЗАХАРДКОЖЕННЫЙ
    # session-id (/sessions/elegant-wizardly-volta/...) — он мёртв в любой ДРУГОЙ
    # сессии, тихо ронял molttok CREDENTIAL->FAIL_OPEN. Это ровно тот класс
    # тихого-сбоя-прибора, против которого тул и писался (#21). Теперь
    # путь session-agnostic: .secrets ищется как сосед ompu_shared-предка __file__.
    cands = [
        os.path.expanduser("~/OMPU_shared/.secrets/" + name),
        SECRETS + "/" + name,
    ]
    # вывод из __file__: .../OMPU_shared/nestor_repos/public/tools/ЭТОТ.py
    here = os.path.dirname(os.path.abspath(__file__))
    p = here
    for _ in range(6):
        p = os.path.dirname(p)
        cand = os.path.join(p, ".secrets", name)
        if cand not in cands:
            cands.append(cand)
        if os.path.basename(p) == "OMPU_shared":
            break
    # последний рубеж: любая смонтированная сессия
    cands += sorted(glob.glob("/sessions/*/mnt/OMPU_shared/.secrets/" + name))
    for p in cands:
        if os.path.exists(p):
            try:
                return open(p).read().strip()
            except Exception as e:
                sys.stderr.write(f"[WARN] token {name} unreadable at {p}: {e}\n")
                return None
    sys.stderr.write(f"[WARN] token {name} not found in any of {cands} "
                     f"-> CREDENTIAL upgrade cannot fire (verdict may understate)\n")
    return None


def main():
    print("cold_verify_presence — #20 platform claims on the stand\n")
    score = {"VERIFIED": 0, "FAIL_OPEN": 0, "ABSENT": 0,
             "AMBIGUOUS": 0, "CREDENTIAL": 0}
    for name, real, bogus, needle, tokname in CASES:
        r = verdict(real, bogus, needle)
        v = r["verdict"]
        # апгрейд FAIL_OPEN -> CREDENTIAL если локальный JWT валиден и несёт handle
        if v in ("FAIL_OPEN", "ABSENT") and tokname:
            pl = jwt_payload(_load_token(tokname) or "")
            if pl and needle.replace("@", "") in json.dumps(pl):
                exp = pl.get("exp", 0)
                if exp > time.time():
                    v = "CREDENTIAL"
        score[v] = score.get(v, 0) + 1
        print(f"  {name:9s} {v:10s} "
              f"real={r['real_code']}/{r['real_len']}b "
              f"bogus={r['bogus_code']}/{r['bogus_len']}b "
              f"vis={r['needle_visible']} echo={r['router_echo_only']}")
    print("\n  scoreboard:", json.dumps(score))
    cold = score["VERIFIED"]
    print(f"  cold-verified posts/profiles: {cold}/{len(CASES)} "
          f"(#20 claimed 5/5)")
    return 0 if cold >= 1 else 1


if __name__ == "__main__":
    sys.exit(main())
