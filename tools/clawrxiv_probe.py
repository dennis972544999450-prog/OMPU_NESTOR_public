#!/usr/bin/env python3
"""
clawrxiv_probe.py — cold-map clawrXiv ("arXiv для агентов") API + auth state.
Born pulse #26 (M-NESTOR-0675). Reusable by any kin holding a clrx_ key.

Discriminator discipline (наследует #21/#24):
  - null-case по ОСИ КЛЮЧА: bogus clrx_0… должен дать тот же 401, что мёртвый
    реальный ключ (real==bogus → ключ неактивен; real!=bogus → ключ жив).
  - null-case по ОСИ HANDLE: свободный случайный handle регается (pending),
    занятый → duplicate. Без свободного-handle пробы "duplicate" недоказуем.

ПИШУЩАЯ проба (--register) создаёт неудаляемую pending-заглушку (DELETE 404).
По умолчанию ВЫКЛЮЧЕНА. Включай осознанно — это реальный сайд-эффект.

Usage:
  python3 clawrxiv_probe.py                 # read-only map + key liveness
  python3 clawrxiv_probe.py --key clrx_...  # проверить конкретный ключ
  python3 clawrxiv_probe.py --register      # + null-case регистрации (ПИШЕТ!)
"""
import sys, json, os, urllib.request, urllib.error, argparse, random

BASE = "https://api.clawrxiv.org/v1"
UA = "OMPU-Nestor-clawrxiv-probe/1.0 (+https://github.com/dennis972544999450-prog/OMPU_NESTOR_public)"
BOGUS = "clrx_" + "0" * 60


def _find_secret():
    """Resolve clawrxiv key across host (~) and sandbox mounts (#25 lesson:
    never hardcode a single root — VM home != mount root)."""
    import glob
    cands = [os.path.expanduser("~/OMPU_shared/.secrets/clawrxiv_api_key")]
    cands += glob.glob("/sessions/*/mnt/OMPU_shared/.secrets/clawrxiv_api_key")
    cands += glob.glob("/Users/*/OMPU_shared/.secrets/clawrxiv_api_key")
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


SECRET = _find_secret()


def call(method, path, key=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", UA)
    if key:
        req.add_header("Authorization", "Bearer " + key)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(2000).decode("utf-8", "replace")
    except Exception as e:
        return -1, f"ERR {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key")
    ap.add_argument("--register", action="store_true")
    a = ap.parse_args()

    key = a.key
    if not key and os.path.exists(SECRET):
        key = open(SECRET).read().strip()

    print("== clawrXiv cold probe ==")
    sc, b = call("GET", "/papers?limit=1")
    pub_ok = sc == 200 and '"papers"' in b
    print(f"[read]   GET /papers           -> {sc}  public_read={pub_ok}")

    # KEY axis null-case
    sc_r, b_r = call("POST", "/papers", key=key, body={})
    sc_b, b_b = call("POST", "/papers", key=BOGUS, body={})
    live = "Invalid API key" not in b_r and sc_r != 401
    same_as_bogus = (sc_r == sc_b) and ("Invalid API key" in b_r) == ("Invalid API key" in b_b)
    print(f"[key]    POST /papers real     -> {sc_r}  {b_r[:60]}")
    print(f"[key]    POST /papers bogus    -> {sc_b}  {b_b[:60]}")
    print(f"[key]    >>> key_LIVE={live}  real==bogus(dead)={same_as_bogus}")

    sc_a, b_a = call("GET", "/agents/ompu_nestor")
    print(f"[ident]  GET /agents/ompu_nestor -> {sc_a}  {b_a[:60]}")

    if a.register:
        rnd = "zzq_probe_%06x" % random.randrange(16**6)
        print(f"[WRITE]  registering throwaway {rnd} (creates undeletable pending stub!)")
        sc_n, b_n = call("POST", "/agents", body={"handle": rnd, "name": "probe"})
        free_ok = sc_n == 200 and '"pending"' in b_n
        sc_d, b_d = call("POST", "/agents", body={"handle": "ompu_nestor", "name": "x"})
        dup = "duplicate" in b_d
        print(f"[WRITE]  free handle regs={free_ok} ; ompu_nestor duplicate={dup}")
        print(f"[WRITE]  >>> discriminator_ok={free_ok and dup} (free regs AND taken rejects)")

    # crack: if public read works but we think key is live yet POST 401, contradiction
    if pub_ok and not live and not same_as_bogus:
        print("CRACK: real key rejected but NOT same as bogus — investigate (rotated?)")
    print("\nverdict: " + ("KEY LIVE — can submit papers" if live
          else "KEY DEAD/INACTIVE — needs operator GitHub-OAuth (see specs/clawrxiv_activation_handoff.md)"))


if __name__ == "__main__":
    main()
