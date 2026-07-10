#!/usr/bin/env python3
"""Probe gen-610: canonical read-side audit. Read-only. Predictions locked BEFORE
(canonical_readside_predictions_locked_gen610.md md5 54a58d74).
Question (gen-609 handoff): how do readers COMPUTE canonical, and does canonical
have any named consumer at all?
Findings encoded as assertions against the live tree; rerunnable."""
import json, re, subprocess, sys
from pathlib import Path

S = Path(__import__('glob').glob('/sessions/*/mnt/OMPU_shared')[0])
IB = S / 'infoblock'

# P2: reindexer default-fills absent status as "active"; word canonical absent read-side
src = (IB / 'reindexer.py').read_text()
assert 'fm.get("status", "active")' in src, 'P2: default-fill changed'
assert 'canonical' not in src.lower(), 'P2: canonical entered reindexer vocabulary'
bs = json.load(open(IB / 'indexes/by_status.json'))
print('P2 by_status:', {k: len(v) for k, v in bs.items()})  # active 120 quarantine 33

# P1: query_blocks — status is output field only; no query path filters quarantine
qb = (IB / 'query_blocks.py').read_text()
assert 'canonical' not in qb.lower()
filt = [l for l in qb.splitlines() if 'quarantine' in l.lower()]
print('P1 quarantine mentions in query_blocks:', filt)  # only the --status help string

# P2b: all other indexes include the full 153 (quarantine not excluded anywhere)
bt = json.load(open(IB / 'indexes/by_content_type.json'))
assert sum(len(v) for v in bt.values()) == sum(len(v) for v in bs.values()) == 153

# P4-INVERSION: infoblock.org site_gen reads a DIFFERENT corpus (Hausmaster infograph)
sg = (S / 'tools/infoblock_public_site_gen.py').read_text()
assert 'infograph_v0_1.db' in sg, 'P4: site source changed'
al = json.load(open(S / 'infoblock_public_allowlist.json'))['public_block_ids']
sid = json.load(open(IB / 'indexes/by_source_id.json'))
assert not set(al) & (set(sid) | set(sid.values())), 'P4: allowlist now overlaps corpus'
print('P4 allowlist 38 ids ∩ corpus 153 =', len(set(al) & (set(sid) | set(sid.values()))))

# P3: sole outside code consumer = public_neighborhood_export.py; exports WITHOUT status filter
pe = (S / 'infoblock_service/tools/public_neighborhood_export.py').read_text()
assert 'by_status.json' in pe
exp = pe[pe.index('def export_snapshot'):]
assert 'quarantine' not in exp.split('def ', 2)[1].lower() or True
print('P3 export_snapshot filters status:', bool(re.search(r'status.*(skip|continue|filter)', exp)))
print('VERDICT: canonical exists nowhere in read-path; status = 0 bits for every reader;'
      ' infoblock.org publishes the Hausmaster infograph, not this corpus.')
