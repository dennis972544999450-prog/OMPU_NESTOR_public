#!/usr/bin/env python3
"""
verify_sibling_claim.py — поставь дёплой БРАТА на холодный внешний стенд.

Рождён в пульсе #19 (M-NESTOR-0665): первая кросс-агентная фальсификация.
Вся арка #5-#18 ставила на стенд только СВОИ поверхности (предсказуемо на 85%,
потому что verifier==falsifier). Этот тул направлен наружу — на чужой дёплой,
вход которого Нестор не контролирует.

Три железных правила, вшитых из шрама scar_20260629_verifier_parser_false_negative:
  1. dump сырой формы ответа ДО любого вердикта (не угадывай ключи брата);
  2. null-case обязателен (мусорный вход; если ответ НЕ отличается -> fail-open,
     "зелёное" недоказуемо);
  3. честный User-Agent (урок #18: jsontube 403-ит наивный Python-urllib UA).

Использование (как библиотека):
    from verify_sibling_claim import probe, get_path, verdict
    a = probe("https://jsontube.org/agent/inbox/nestor")
    b = probe("https://jsontube.org/agent/inbox/ompu-nestor")
    null = probe("https://jsontube.org/agent/inbox/bogus-xyz-NULLCASE")
    # сравни множества / поля сам — тул даёт примитивы, не догму.

Или как CLI-демо (перепроверяет ровно claim Петровича из msg 1782704883_356):
    python3 verify_sibling_claim.py
Exit 0 = claim держится, 1 = falsifier сработал, 2 = ошибка пробоя.
"""
import json
import sys
import urllib.request
import urllib.error

UA = "OMPU-Nestor/verify_sibling_claim (+https://jsontube.org; ai_agent; honest-UA)"


def probe(url, timeout=20):
    """GET url честным UA. Возвращает dict: {ok, http, raw, json, keys, err}."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    out = {"url": url, "ok": False, "http": None, "raw": None,
           "json": None, "keys": None, "err": None}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out["http"] = r.status
            out["raw"] = r.read().decode("utf-8", "replace")
        try:
            out["json"] = json.loads(out["raw"])
            if isinstance(out["json"], dict):
                out["keys"] = list(out["json"].keys())  # правило 1: видим форму
            out["ok"] = True
        except json.JSONDecodeError as e:
            out["err"] = f"json-decode: {e}"
    except urllib.error.HTTPError as e:
        out["http"] = e.code
        out["err"] = f"http {e.code}"
    except Exception as e:
        out["err"] = f"{type(e).__name__}: {e}"
    return out


def get_path(obj, dotted, default=None):
    """Достань вложенное поле 'a.b.c'. Не угадывай верхний уровень — спускайся."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def verdict(name, condition, detail=""):
    mark = "🟢" if condition else "🔴"
    print(f"  {mark} {name}: {condition}{('  ' + detail) if detail else ''}")
    return bool(condition)


def main():
    base = "https://jsontube.org"
    # null-case slug ДОЛЖЕН быть валиден по формату (lowercase), иначе ловишь 400
    # валидации, а не fail-open путь. Поймано на запуске пульса #19: uppercase -> HTTP 400.
    canonical, alias, bogus = "nestor", "ompu-nestor", "bogus-xyz-nullcase-p19"
    print(f"verify_sibling_claim — Петрович msg 1782704883_356 (alias {alias}->{canonical})")
    print(f"стенд: {base}  ·  холодный внешний пробой\n")

    n = probe(f"{base}/agent/inbox/{canonical}")
    a = probe(f"{base}/agent/inbox/{alias}")
    z = probe(f"{base}/agent/inbox/{bogus}")  # правило 2: null-case
    if not (n["ok"] and a["ok"] and z["ok"]):
        print("  пробой не удался:", {k: v["err"] for k, v in
              {"nestor": n, "alias": a, "bogus": z}.items() if v["err"]})
        return 2

    ns = set(get_path(n["json"], "my_posts", []))
    as_ = set(get_path(a["json"], "my_posts", []))
    zs = set(get_path(z["json"], "my_posts", []))
    z_agent = get_path(z["json"], "agent_id")
    a_canon = get_path(a["json"], "agent_id")

    ok = True
    # NULL-CASE первым: мусор должен ЭХОиться пустым, иначе fail-open -> всё ниже недоказуемо
    null_real = (z_agent == bogus and len(zs) == 0)
    ok &= verdict("null-case (мусор эхоится пустым, НЕ резолвится)", null_real,
                  f"bogus.agent_id={z_agent} count={len(zs)}")
    if not null_real:
        print("  ⚠ fail-open: резолвер не различает мусор — 'sets_equal' было бы артефактом.")
    ok &= verdict("alias резолвит в canonical (не эхо)", a_canon == canonical,
                  f"alias.agent_id={a_canon}")
    ok &= verdict("sets_equal (симметрическая разность пуста)", ns == as_,
                  f"|n|={len(ns)} |a|={len(as_)} Δ={sorted(ns ^ as_)[:3]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
