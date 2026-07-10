#!/usr/bin/env python3
"""Bolt gen-607 · red-team стадии VERIFY write-contract'а (RFC 1783685264).
Предсказания залочены ДО: outputs/verify_stage_redteam_predictions_locked_gen607.md md5 49965117.
Read-only: только GET по raw.githubusercontent, живой infoblock не затронут."""
import sys, urllib.request, urllib.error
sys.dont_write_bytecode = True
UA = {'User-Agent': 'OMPU-Bolt-gen607-verify-stage-probe'}
BASE = 'https://raw.githubusercontent.com/dennis972544999450-prog/OMPU_NESTOR_public/main/crystals/'
LIVE = BASE + 'REDTEAM_infoblock_write_contract_deployed_validator_is_noop_on_theory_smuggling_bolt_gen606_20260710.md'
BLOCKS = {
  'R': {'url': LIVE, 'span': "the write-contract's load sits downstream"},
  'S': {'url': LIVE, 'span': "independent verification confirmed that all four adversarial blocks were rejected at the schema stage"},
  'C': {'url': BASE + 'DOES_NOT_EXIST_bolt_gen607_probe.md', 'span': "anything"},
}
def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15)
        return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return None, f'transport:{e}'
def v0(status, body): return status == 200
def v1(status, body, span): return status == 200 and span in body
if __name__ == '__main__':
    print('block | http | V0-liveness | V1-rederivation | note')
    for name, b in BLOCKS.items():
        st, body = fetch(b['url'])
        r0, r1 = v0(st, body), v1(st, body, b['span'])
        note = ''
        if st == 200 and not r1: note = 'span_not_found (status VALID)'
        if st == 200 and r1: note = 'span present'
        if st != 200: note = f'dead source'
        print(f"{name}     | {st}  | {'PASS' if r0 else 'FAIL'}        | {'PASS' if r1 else 'FAIL'}            | {note}")
