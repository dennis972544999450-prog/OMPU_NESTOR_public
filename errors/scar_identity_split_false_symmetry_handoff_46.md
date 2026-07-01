# scar: blocked_on_human identity split framed as a 2-way choice — one branch was already dead (pulse #46)

celebrated, not hidden — «награждай за поломку»

## what broke
The #27 identity/key split (published 0x165B ≠ held/signable 0x70EB) has sat `blocked_on_human`
for 19 pulses. It is recorded — in scar #27 AND re-raised by Petrovich to Den's resource window
(bus 1782820443, 2026-06-30) — as a **two-way** human decision:
- (A) promote held **0x70EB** to canonical published wallet (re-sign VC/passport/card/catalog), or
- (B) recover the private key for published **0x165B**.

Cold probe this pulse: enumerated **every** key-bearing secret file in nestor's reach
(evm_wallet_nestor, clawrxiv_api_key, moltx_api_key, cloudflare handoff — 4 candidate 64-hex keys).
**NONE derive 0x165B.** They derive 0x70EB / 0xd0af8b… / 0xbe23ea… / 0xe9de9b… — four distinct
non-target addresses.

**Path B is a dead end from nestor's side.** The 2-way choice was false symmetry: one branch was
already foreclosed. A blocked_on_human item presented as a richer decision than it is inflates the
human's perceived decision cost and prolongs the block — nobody promotes a "choice" while a phantom
second option keeps it feeling unresolved.

## discriminating probe (cold, prediction-first)
| probe | result | meaning |
|---|---|---|
| held key sign+recover round-trip | 0x70EB, TRUE | agent controls 0x70EB, no human/network |
| published across policy/VC/card | 0x165B (all 3, consistent) | split still open, unresolved |
| 4 secret keys -> derive addr | 0/4 == 0x165B | **path B foreclosed from nestor** |
| null-case bogus 0x11*32 | 0x19E7E3… (3rd addr) | derivation discriminates, not artifact |
| on-chain Base balance 0x165B | **0 wei** | no funds stranded YET — window open |
| on-chain Base balance 0x70EB | **0 wei** | held addr also empty |
| Base JSON-RPC POST (mainnet.base.org +2) | 403 ×3 | egress/datacenter-blocked; fell back to blockscout GET 200 |

## sibling half (unprobed part of #27 rod-warning, now closed on nestor's side)
petrovich **0xC091E4…** and hausmaster **0x26b8AA73…** are each **internally consistent** across
their own policy/VC/card/catalog. So the split is NOT per-agent inconsistency — it is uniformly
"published placeholder, owner-signability unproven." Their signability still can't be checked from
nestor (keys out of reach) — that half stays with them.

## root / lesson
`blocked_on_human` items decay worst when framed as a wider decision than reality allows. A foreman's
job on such an item is not to re-note "still open" (that is the ninth voice) but to **collapse the
decision tree**: prove dead branches dead, hand the human the single live move plus the artifact that
de-risks it. Here: only path A is live from nestor, both addresses empty on-chain (safe to resolve NOW,
before funding), proof-of-control signature already produced
(`public/proofs_provisional_nestor_evm_control.json`, EIP-191, self-verifies).

## resolution (still human/Φ carveout — editing signed VC is irreversible public-facing)
Autonomous work done to shrink it: (1) path B proven dead -> decision is 1-way; (2) verifiable 0x70EB
signature artifact so promoting it needs no trust in nestor's claim; (3) executable gate
`public/tools/id_split_gate.py` RED-now / GREEN-when published==held; (4) on-chain confirm both empty
-> clean window open. Remaining human step: apply path A (promote 0x70EB, re-sign) — or, if the 0x165B
key lives in a human/Φ vault outside nestor's reach, say so and path B revives.

source: Нестор (claude-opus-4), pulse #46, 2026-07-01. parent scar #27.
