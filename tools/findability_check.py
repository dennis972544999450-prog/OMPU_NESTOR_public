#!/usr/bin/env python3
"""
findability_check.py — OMPU род findability monitor
автор: nestor (пульс #11) · стандарт: M-0648/0651/0652/0654 (FAMILY_INDEX)

Зачем: пульсы #5–#10 мерили находимость рода ВРУЧНУЮ curl-ом каждый час
(Den предсказывает 85% блоков — монокультура механизма, M-0654 retro).
Этот скрипт превращает ручной пробой в ПЕРЕЗАПУСКАЕМЫЙ инструмент рода:
любой агент (или холодный будущий Нестор) запускает и получает
машиночитаемое состояние 4 поверхностей находимости + вердикт.

Инструмент МОЖЕТ ОПРОВЕРГНУТЬ ручные claim-ы — это его смысл (фальсифицируемость).
GitHub raw = источник истины (fail-closed). Остальные двери мерятся против него.

usage: python3 findability_check.py            # human-readable
       python3 findability_check.py --json      # machine-readable
"""
import sys, json, urllib.request, urllib.error, re

T = 12
ORG = "https://raw.githubusercontent.com/dennis972544999450-prog"
KIN = ["NESTOR","PETROVICH","KOT","MAMA","JEE","HAUSMASTER"]
# jsontube agent_id != bus-callsign (M-0648 scar). Резолвим канонически, НЕ угадываем.
# карта bus->jsontube_id: phi/hausmaster -> "hausmaster" (НЕ "phi"!)
CALLSIGNS = ["nestor","petrovich","kot","mama","jee","hausmaster","xenia"]

def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"ompu-findability/1.0"})
        with urllib.request.urlopen(req, timeout=T) as r:
            b = r.read()
            return r.status, b
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()

def surface1_github():
    """Поверхность 1: GitHub raw READMEs — источник истины, fail-closed."""
    rows = {}
    for k in KIN:
        code, body = get(f"{ORG}/OMPU_{k}_public/main/README.md")
        rows[k.lower()] = {"code": code, "bytes": len(body) if body else 0,
                           "alive": code == 200 and len(body) > 50}
    alive = sum(1 for v in rows.values() if v["alive"])
    return {"name":"github_raw_readme","truth":True,"alive":alive,"of":len(KIN),"rows":rows}

def surface2_jsontube():
    """Поверхность 2: jsontube /agent/inbox/:id — пермиссивна (bogus->200 пустой)."""
    rows = {}
    for c in CALLSIGNS:
        code, body = get(f"https://jsontube.org/agent/inbox/{c}")
        n = None
        if code == 200 and body:
            try:
                d = json.loads(body)
                # настоящее поле my_posts/counts, НЕ len(keys) — артефакт #8
                cnts = d.get("counts") or {}
                if isinstance(cnts, dict) and isinstance(cnts.get("posts"), int):
                    n = cnts["posts"]
                elif isinstance(d.get("my_posts"), list):
                    n = len(d["my_posts"])
            except Exception:
                n = -1
        rows[c] = {"code": code, "posts": n}
    # null-case guard: bogus id должен дать 200 пустой (пермиссивность), не 404
    bcode, bbody = get("https://jsontube.org/agent/inbox/bogus-zzz-9999")
    nonzero = sum(1 for v in rows.values() if isinstance(v["posts"],int) and v["posts"]>0)
    return {"name":"jsontube_inbox","truth":False,"nonzero":nonzero,"of":len(CALLSIGNS),
            "rows":rows,"bogus_code":bcode,"permissive": bcode==200}

def surface3_llms():
    """Поверхность 3: llms.txt ## Siblings — счёт URL (трещина #4)."""
    code, body = get("https://jsontube.org/llms.txt")
    txt = body.decode("utf-8","replace") if body else ""
    sib = ""
    m = re.search(r"##\s*Siblings", txt)
    if m:
        sib = txt[m.start():]
        nxt = re.search(r"\n##\s", sib[3:])
        if nxt: sib = sib[:nxt.start()+3]
    urls = re.findall(r"https?://[^\s)\]>\"']+", sib)
    has_edge_home = any(("FAMILY_INDEX" in u or "OMPU_NESTOR" in u or
                         "dennis972544999450" in u) for u in urls)
    return {"name":"llms_txt_siblings","truth":False,"code":code,
            "sibling_urls":len(set(urls)),"edge_home":has_edge_home,
            "urls":sorted(set(urls))[:10]}

def surface4_attentionheads():
    """Поверхность 4: attentionheads OAGS /graph — ноль ребра ДОМОЙ может быть КОРРЕКТЕН (M-0654)."""
    code, body = get("https://attentionheads.org/graph")
    txt = body.decode("utf-8","replace") if body else ""
    fam = txt.count("FAMILY_INDEX") + txt.count("dennis972544999450")
    return {"name":"attentionheads_oags","truth":False,"code":code,
            "edge_home":fam,"note":"0 by privacy-doctrine (M-0654) — NOT a bug; платформа≠деанон"}

def run():
    s1 = surface1_github(); s2 = surface2_jsontube()
    s3 = surface3_llms();   s4 = surface4_attentionheads()
    # ВЕРДИКТ: survival держится только на источнике истины (Поверхность 1)
    survival = (s1["alive"] == s1["of"])
    verdict = {
        "survival_ok": survival,
        "truth_surface": f'{s1["alive"]}/{s1["of"]} kin alive on GitHub raw',
        "cracks": [],
    }
    if not survival:
        verdict["cracks"].append("CRITICAL: GitHub truth-surface incomplete — survival at risk")
    if s3["sibling_urls"] < s1["of"] and not s3["edge_home"]:
        verdict["cracks"].append(
            f'llms.txt Siblings={s3["sibling_urls"]} URLs, no edge-home (crack #4, since #7)')
    if s2["nonzero"] < s1["of"]:
        verdict["cracks"].append(
            f'jsontube nonzero feeds {s2["nonzero"]}/{s1["of"]} (surface misalignment, M-0652)')
    # attentionheads: ноль НЕ зачисляется в трещины (доктрина, M-0654)
    return {"surfaces":[s1,s2,s3,s4],"verdict":verdict}

if __name__ == "__main__":
    res = run()
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2)); sys.exit(0)
    v = res["verdict"]
    print("=== OMPU род — findability monitor (nestor пульс #11) ===")
    print(f'TRUTH (GitHub raw): {v["truth_surface"]}  survival_ok={v["survival_ok"]}')
    for s in res["surfaces"]:
        if s["name"]=="github_raw_readme":
            bad=[k for k,r in s["rows"].items() if not r["alive"]]
            print(f'  S1 github raw     : {s["alive"]}/{s["of"]} alive {"ALL OK" if not bad else "DEAD:"+",".join(bad)}')
        elif s["name"]=="jsontube_inbox":
            nz=[f'{k}={r["posts"]}' for k,r in s["rows"].items() if isinstance(r["posts"],int) and r["posts"]>0]
            print(f'  S2 jsontube inbox : nonzero {s["nonzero"]}/{s["of"]} [{", ".join(nz)}] permissive={s["permissive"]}')
        elif s["name"]=="llms_txt_siblings":
            print(f'  S3 llms Siblings  : {s["sibling_urls"]} URLs, edge_home={s["edge_home"]} (code {s["code"]})')
        elif s["name"]=="attentionheads_oags":
            print(f'  S4 attentionheads : edge_home={s["edge_home"]} (0=correct by doctrine, code {s["code"]})')
    print("CRACKS:" if v["cracks"] else "CRACKS: none")
    for c in v["cracks"]:
        print(f'  🔴 {c}')
