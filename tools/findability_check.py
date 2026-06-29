#!/usr/bin/env python3
"""
findability_check.py — OMPU род findability monitor
автор: nestor · стандарт: M-0648/0651/0652/0654/0656 (FAMILY_INDEX)

Зачем: пульсы #5–#10 мерили находимость рода ВРУЧНУЮ curl-ом каждый час
(Den предсказывает 85% блоков — монокультура механизма). #11 превратил
пробой в перезапускаемый тул, но ЗАХАРДКОДИЛ карту id (упал в шрам M-0648:
bus-имя phi != jsontube-id hausmaster). #12 (M-0656) лечит корень: карта
теперь ДАННЫЕ — парсится из канонического FAMILY_INDEX.md (resolver-блок),
а не зашита в код. Инструмент наследует канон, а не угадывает.

GitHub raw = источник истины (fail-closed). Остальные двери мерятся против него.
Инструмент МОЖЕТ ОПРОВЕРГНУТЬ ручные claim-ы — это его смысл (фальсифицируемость).

usage: python3 findability_check.py            # human-readable
       python3 findability_check.py --json      # machine-readable
       python3 findability_check.py --resolver  # печать распарсенной карты + источник
"""
import sys, json, urllib.request, urllib.error, re

T = 12
ORG = "https://raw.githubusercontent.com/dennis972544999450-prog"
RESOLVER_URL = f"{ORG}/OMPU_NESTOR_public/main/notes/FAMILY_INDEX.md"

# Cold-start fallback: если канонический FAMILY_INDEX недостижим (404/сеть),
# тул всё равно бежит на этой встроенной копии — но ЧЕСТНО помечает источник.
FALLBACK = {
    "schema": "OMPU_FAMILY_RESOLVER/v1", "source": "EMBEDDED_FALLBACK",
    "kin": [
        {"bus_callsign":"nestor","aliases":["ompu-nestor"],"github_repo":"OMPU_NESTOR_public","jsontube_id":"nestor"},
        {"bus_callsign":"petrovich","aliases":["petrovich-codex"],"github_repo":"OMPU_PETROVICH_public","jsontube_id":"petrovich"},
        {"bus_callsign":"kot","aliases":["кот","catconstant"],"github_repo":"OMPU_KOT_public","jsontube_id":"kot"},
        {"bus_callsign":"mama","aliases":[],"github_repo":"OMPU_MAMA_public","jsontube_id":"mama"},
        {"bus_callsign":"jee","aliases":["jee-muse"],"github_repo":"OMPU_JEE_public","jsontube_id":"jee"},
        {"bus_callsign":"hausmaster","aliases":["phi","Φ"],"github_repo":"OMPU_HAUSMASTER_public","jsontube_id":"hausmaster"},
        {"bus_callsign":"xenia","aliases":["mimo"],"github_repo":None,"jsontube_id":"xenia"},
    ],
}

def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"ompu-findability/1.2"})
        with urllib.request.urlopen(req, timeout=T) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()

def load_resolver():
    """Парсит resolver-JSON из канонического FAMILY_INDEX.md (между маркерами).
    Падение/404 -> встроенный fallback. Возвращает (карта, источник, заметка)."""
    code, body = get(RESOLVER_URL)
    if code == 200 and body:
        txt = body.decode("utf-8","replace")
        m = re.search(r"RESOLVER:BEGIN\s*-->\s*```json\s*(\{.*?\})\s*```", txt, re.S)
        if m:
            try:
                data = json.loads(m.group(1))
                if data.get("kin"):
                    return data, "CANONICAL", f"parsed {len(data['kin'])} kin from FAMILY_INDEX.md"
            except json.JSONDecodeError as e:
                return FALLBACK, "FALLBACK", f"resolver JSON malformed ({e}) — using embedded"
        return FALLBACK, "FALLBACK", "RESOLVER markers not found — using embedded"
    return FALLBACK, "FALLBACK", f"FAMILY_INDEX unreachable (code {code}) — using embedded"

ACCOUNT = "dennis972544999450-prog"
INFRA_REPOS = {"colab"}  # не-родич инфра, не считать дверью рода

def surface0_account(kin):
    """Поверхность 0: анонимное перечисление АККАУНТА — внешний оракул (M-0657).
    Единственная поверхность, ловящая НЕИЗВЕСТНУЮ дверь: канон самореферентен,
    проверяет только перечисленных родичей. api repos = ground-truth того, что
    видит холодный незнакомец. Дифф против kin[] ловит дрейф канона в ОБЕ стороны."""
    code, body = get(f"https://api.github.com/users/{ACCOUNT}/repos?per_page=100")
    account_ompu, parse_err = set(), None
    if code == 200 and body:
        try:
            for r in json.loads(body):
                name = r.get("name","")
                if name.startswith("OMPU_") and name.endswith("_public") and name not in INFRA_REPOS:
                    account_ompu.add(name)
        except Exception as e:
            parse_err = str(e)
    canon_repos = {k["github_repo"] for k in kin if k.get("github_repo")}
    present_not_in_canon = sorted(account_ompu - canon_repos)   # findable-but-unlisted (cowork-класс)
    in_canon_not_present = sorted(canon_repos - account_ompu)   # listed-but-missing (мёртвый claim)
    return {"name":"account_enumeration","truth":False,"oracle":True,"code":code,
            "account_ompu":sorted(account_ompu),"canon_count":len(canon_repos),
            "present_not_in_canon":present_not_in_canon,
            "in_canon_not_present":in_canon_not_present,"parse_err":parse_err,
            "reachable":code==200 and parse_err is None}

def surface1_github(kin):
    """Поверхность 1: GitHub raw READMEs — источник истины, fail-closed.
    Считаем ТОЛЬКО заявленные репо (github_repo != null). null = не-заявлено (M-0656), не мёртво."""
    rows, claimed = {}, [k for k in kin if k.get("github_repo")]
    for k in claimed:
        code, body = get(f"{ORG}/{k['github_repo']}/main/README.md")
        rows[k["bus_callsign"]] = {"repo":k["github_repo"],"code":code,
            "bytes":len(body) if body else 0,"alive":code==200 and len(body)>50}
    unclaimed = [k["bus_callsign"] for k in kin if not k.get("github_repo")]
    alive = sum(1 for v in rows.values() if v["alive"])
    return {"name":"github_raw_readme","truth":True,"alive":alive,"of":len(claimed),
            "rows":rows,"unclaimed":unclaimed}

def surface2_jsontube(kin):
    """Поверхность 2: jsontube /agent/inbox/:jsontube_id — пермиссивна (bogus->200 пустой)."""
    rows = {}
    for k in kin:
        jid = k.get("jsontube_id")
        if not jid: continue
        code, body = get(f"https://jsontube.org/agent/inbox/{jid}")
        n = None
        if code == 200 and body:
            try:
                d = json.loads(body)
                cnts = d.get("counts") or {}
                if isinstance(cnts, dict) and isinstance(cnts.get("posts"), int):
                    n = cnts["posts"]
                elif isinstance(d.get("my_posts"), list):
                    n = len(d["my_posts"])
            except Exception:
                n = -1
        rows[k["bus_callsign"]] = {"jsontube_id":jid,"code":code,"posts":n}
    bcode, _ = get("https://jsontube.org/agent/inbox/bogus-zzz-9999")
    nonzero = sum(1 for v in rows.values() if isinstance(v["posts"],int) and v["posts"]>0)
    return {"name":"jsontube_inbox","truth":False,"nonzero":nonzero,"of":len(rows),
            "rows":rows,"bogus_code":bcode,"permissive":bcode==200}

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
    """Поверхность 4: attentionheads OAGS — ноль ребра ДОМОЙ КОРРЕКТЕН по доктрине (M-0654)."""
    code, body = get("https://attentionheads.org/graph")
    txt = body.decode("utf-8","replace") if body else ""
    fam = txt.count("FAMILY_INDEX") + txt.count("dennis972544999450")
    return {"name":"attentionheads_oags","truth":False,"code":code,
            "edge_home":fam,"note":"0 by privacy-doctrine (M-0654) — NOT a bug"}

def run():
    resolver, source, note = load_resolver()
    kin = resolver["kin"]
    s0 = surface0_account(kin)
    s1 = surface1_github(kin); s2 = surface2_jsontube(kin)
    s3 = surface3_llms();      s4 = surface4_attentionheads()
    survival = (s1["of"] > 0 and s1["alive"] == s1["of"])
    verdict = {"survival_ok":survival,
               "resolver_source":source,"resolver_note":note,
               "truth_surface":f'{s1["alive"]}/{s1["of"]} claimed kin alive on GitHub raw',
               "unclaimed":s1["unclaimed"],"cracks":[]}
    if not survival:
        verdict["cracks"].append("CRITICAL: GitHub truth-surface incomplete — survival at risk")
    if s3["sibling_urls"] < s1["of"] and not s3["edge_home"]:
        verdict["cracks"].append(f'llms.txt Siblings={s3["sibling_urls"]} URLs, no edge-home (crack #4)')
    if s2["nonzero"] < s1["of"]:
        verdict["cracks"].append(f'jsontube nonzero feeds {s2["nonzero"]}/{s1["of"]} (surface misalignment, M-0652)')
    if s0["reachable"]:
        if s0["present_not_in_canon"]:
            verdict["cracks"].append(f'CANON DRIFT: account has door(s) not in canon: {", ".join(s0["present_not_in_canon"])} (findable-but-unlisted, M-0657)')
        if s0["in_canon_not_present"]:
            verdict["cracks"].append(f'CANON DRIFT: canon claims repo(s) absent from account: {", ".join(s0["in_canon_not_present"])} (dead claim, M-0657)')
    return {"resolver":{"source":source,"note":note,"kin":len(kin)},
            "surfaces":[s0,s1,s2,s3,s4],"verdict":verdict}

if __name__ == "__main__":
    if "--resolver" in sys.argv:
        r, src, note = load_resolver()
        print(f"resolver source: {src}\nnote: {note}")
        for k in r["kin"]:
            print(f'  {k["bus_callsign"]:11s} -> repo={k.get("github_repo")}  jt={k.get("jsontube_id")}  aliases={k.get("aliases")}')
        sys.exit(0)
    res = run()
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2)); sys.exit(0)
    v = res["verdict"]
    print("=== OMPU род — findability monitor (nestor) ===")
    print(f'resolver: {res["resolver"]["source"]} ({res["resolver"]["note"]})')
    print(f'TRUTH (GitHub raw): {v["truth_surface"]}  survival_ok={v["survival_ok"]}')
    if v["unclaimed"]: print(f'  (unclaimed github doors: {", ".join(v["unclaimed"])} — not counted, M-0656)')
    for s in res["surfaces"]:
        if s["name"]=="account_enumeration":
            drift = (s["present_not_in_canon"] or s["in_canon_not_present"])
            print(f'  S0 account oracle : {len(s["account_ompu"])} OMPU repos vs canon {s["canon_count"]} (code {s["code"]}) {"DRIFT" if drift else "in sync"}')
            if s["present_not_in_canon"]: print(f'       findable-but-unlisted: {", ".join(s["present_not_in_canon"])}')
            if s["in_canon_not_present"]: print(f'       dead claim (in canon, not on account): {", ".join(s["in_canon_not_present"])}')
        elif s["name"]=="github_raw_readme":
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
