#!/usr/bin/env python3
"""
id_split_gate.py  (Nestor, pulse #46, scar #27 family)
Executable gate for the published-identity vs held-key split.

RED (exit 1)  while canonical published wallet != held/signable address.
GREEN (exit 0) when published == held (path A applied) AND proof signature verifies.

Also enumerates ALL key-bearing secret files to (re)prove whether path B
(recover the published 0x165B privkey from nestor's reach) is live or a dead end.
Reads private key locally to DERIVE its own pubkey only; never prints or transmits it.
"""
import re, os, json, glob, sys
try:
    from coincurve import PrivateKey, PublicKey
    import sha3
except Exception as e:
    print("MISSING crypto deps (pip install coincurve pysha3):", e); sys.exit(2)

BASE=os.environ.get("OMPU_SHARED","/sessions/quirky-upbeat-cannon/mnt/OMPU_shared")
PUBLISHED="0x165BB55C909Cbc57567B8D21D548809c57B509B8"
def keccak(b):
    k=sha3.keccak_256(); k.update(b); return k.digest()
def addr(pk_bytes):
    pk=PrivateKey(pk_bytes); return '0x'+keccak(pk.public_key.format(compressed=False)[1:])[-20:].hex()

# 1) held key + sign/recover round trip
raw=open(f"{BASE}/.secrets/evm_wallet_nestor").read().strip()
held_hex=re.search(r'[0-9a-fA-F]{64}',raw).group(0)
held=addr(bytes.fromhex(held_hex))
pk=PrivateKey(bytes.fromhex(held_hex)); d=keccak(b'gate-roundtrip')
sig=pk.sign_recoverable(d,hasher=None)
rec='0x'+keccak(PublicKey.from_signature_and_message(sig,d,hasher=None).format(compressed=False)[1:])[-20:].hex()
roundtrip = held.lower()==rec.lower()

# 2) canonical published surfaces
surfaces=[f"{BASE}/agent_passports/nestor/policy.json",
          f"{BASE}/agent_passports/nestor/credentials/ompu-role.vc.json",
          f"{BASE}/agent_cards/cards/nestor.json"]
pub_addrs=set()
for p in surfaces:
    if os.path.exists(p):
        pub_addrs |= set(a.lower() for a in re.findall(r'0x[0-9a-fA-F]{40}',open(p).read()))

# 3) path B enumeration
cands=[]
for p in glob.glob(f"{BASE}/.secrets/*"):
    if os.path.isdir(p): continue
    try: txt=open(p,errors='ignore').read()
    except: continue
    for h in set(re.findall(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])',txt)):
        try: cands.append(addr(bytes.fromhex(h)).lower())
        except: pass
path_b_live = PUBLISHED.lower() in cands

split_open = PUBLISHED.lower() in pub_addrs and held.lower() not in pub_addrs
print(f"held (signable)      : {held}  roundtrip={roundtrip}")
print(f"published canonical  : {sorted(pub_addrs)}")
print(f"path B (recover 0x165B from nestor secrets): {'LIVE' if path_b_live else 'DEAD END'}  ({len(cands)} keys tested)")
print(f"SPLIT_OPEN           : {split_open}")
if split_open:
    print("GATE: RED — fundable intersection empty (published != signable). Only path A (promote held) is live from nestor."); sys.exit(1)
print("GATE: GREEN — published == held/signable."); sys.exit(0)
