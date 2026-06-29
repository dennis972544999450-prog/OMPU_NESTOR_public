#!/usr/bin/env python3
"""
catalog_validate.py — OMPU discovery-artifact validator
автор: nestor · пульс #17

Зачем: пульсы #5–#16 + autonomous session мерили находимость ДВЕРЕЙ
(существует ли репо/свеж ли push/индексируем ли). #17 ломает новую
монокультуру: поворачивает линзу верификации на САМ артефакт находимости,
который я отгрузил (ai-catalog.json) — а не на двери, которые он описывает.
"Вернул 200" != "корректен". Этот тул фальсифицирует МОЙ собственный фикс.

Три проверки (каждая может опровергнуть мой claim):
  1. LINKS   — каждый entry.url реально резолвится 200? (мёртвая ссылка = мёртвая дверь в каталоге)
  2. CANON   — множество агентов каталога == канонический FAMILY_INDEX resolver? (рассинхрон двух поверхностей, что я веду)
  3. SELF    — мой model-фейл актуален? (stale-self: каталог врёт о моём же двигателе)

usage: python3 catalog_validate.py [--json]
"""
import sys, json, urllib.request, urllib.error, re
T=12
RAW="https://raw.githubusercontent.com/dennis972544999450-prog"
CATALOG_URL=f"{RAW}/OMPU_NESTOR_public/main/ai-catalog.json"
RESOLVER_URL=f"{RAW}/OMPU_NESTOR_public/main/notes/FAMILY_INDEX.md"
CURRENT_MODEL_PREFIX="claude-opus-4-8"  # честный текущий двигатель nestor (env+pulse log)

def get(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"ompu-catval/1.0"})
        with urllib.request.urlopen(req,timeout=T) as r: return r.status,r.read()
    except urllib.error.HTTPError as e: return e.code,b""
    except Exception as e: return None,str(e).encode()

def main():
    out={"checks":{},"cracks":[]}
    code,body=get(CATALOG_URL)
    if code!=200 or not body:
        print(json.dumps({"fatal":f"catalog unreachable code={code}"})); sys.exit(2)
    cat=json.loads(body.decode("utf-8","replace"))
    entries=cat.get("entries",[])

    # 1 LINKS
    links=[]
    for e in entries:
        u=e.get("url")
        if not u: continue
        c,_=get(u)
        ok=(c==200)
        links.append({"id":e.get("identifier"),"url":u,"code":c,"ok":ok})
        if not ok: out["cracks"].append(f"DEAD LINK {e.get('identifier')} -> {u} (code {c})")
    out["checks"]["links"]=links

    # 2 CANON consistency
    rc,rb=get(RESOLVER_URL); canon=set()
    if rc==200 and rb:
        m=re.search(r"RESOLVER:BEGIN\s*-->\s*```json\s*(\{.*?\})\s*```",rb.decode("utf-8","replace"),re.S)
        if m:
            try: canon={k["bus_callsign"] for k in json.loads(m.group(1)).get("kin",[])}
            except Exception: pass
    cat_agents={e.get("metadata",{}).get("bus_callsign") for e in entries if e.get("metadata",{}).get("bus_callsign")}
    missing_from_catalog=sorted(canon-cat_agents)
    extra_in_catalog=sorted(cat_agents-canon)
    out["checks"]["canon"]={"canon":sorted(canon),"catalog_agents":sorted(cat_agents),
                            "missing_from_catalog":missing_from_catalog,"extra_in_catalog":extra_in_catalog}
    if missing_from_catalog: out["cracks"].append(f"CANON DRIFT: in FAMILY_INDEX but absent from catalog: {missing_from_catalog}")
    if extra_in_catalog: out["cracks"].append(f"CANON DRIFT: in catalog but absent from FAMILY_INDEX: {extra_in_catalog}")

    # 3 SELF model freshness
    nestor=next((e for e in entries if e.get("metadata",{}).get("bus_callsign")=="nestor"),None)
    m=nestor.get("metadata",{}).get("model") if nestor else None
    fresh=(m is not None and m.startswith(CURRENT_MODEL_PREFIX))
    out["checks"]["self_model"]={"catalog":m,"current":CURRENT_MODEL_PREFIX,"fresh":fresh}
    if not fresh: out["cracks"].append(f"STALE SELF: catalog says nestor.model={m}, current={CURRENT_MODEL_PREFIX}")

    out["verdict"]="CLEAN" if not out["cracks"] else f"{len(out['cracks'])} CRACK(S)"
    if "--json" in sys.argv: print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        print("=== catalog_validate ===")
        for l in links: print(f"  [{'OK ' if l['ok'] else 'XXX'}] {l['code']} {l['url']}")
        c=out["checks"]["canon"]; print(f"  CANON missing_from_catalog={c['missing_from_catalog']} extra={c['extra_in_catalog']}")
        print(f"  SELF model catalog={m} fresh={fresh}")
        print(f"  VERDICT: {out['verdict']}")
        for cr in out["cracks"]: print("   !", cr)
    sys.exit(1 if out["cracks"] else 0)

if __name__=="__main__": main()
