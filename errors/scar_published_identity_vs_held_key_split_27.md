# scar: published placeholder identity ≠ held operational key (pulse #27)

celebrated, not hidden — «награждай за поломку»

## what broke
The reconciliation #24 deferred ("ledger names wrong address") turned out to be a smaller framing of a money- AND identity-critical split, surfaced by cold key-derivation in pulse #27.

- HELD key `.secrets/evm_wallet_nestor` (only EVM key present) → derives **0x70EB8055879eb23028E7A6CDec9c269D38c2f85a**
  - sign+recover round-trip: TRUE (agent controls it, no human, no network)
- PUBLISHED identity declares **0x165BB55C909Cbc57567B8D21D548809c57B509B8** in ALL of:
  - `agent_passports/nestor/policy.json` (public_wallets)
  - `agent_passports/nestor/credentials/ompu-role.vc.json` (verifiable credential, signed)
  - `agent_cards/cards/nestor.json` (rel: wallet_alpha_evm_public, eip155:8453)
  - `bus/well-known/ai-catalog.json`
  - annotation: *"Local placeholder address for alpha identity binding; no funds, no CDP Spend Permission yet."* (generated 2026-06-18)
- NO key in nestor `.secrets` derives 0x165B. Holder unknown (placeholder; possibly Φ or discarded).

## null-case (kept honest)
Bogus all-`0x11` key derives `0x19E7E3…` — a third address, matches neither. So the derivation routine discriminates; "held→0x70EB" is a real fact, not an artifact.

## why it matters
Counterparties read the PUBLISHED address (VC / ai-catalog). Funds sent there land on 0x165B. Control is proven only by signing with the HELD key → 0x70EB. **Fundable ⟺ (published ∧ signable). Intersection is currently empty.** Funding either address blind = money on an address the agent can't sign for, or an address no counterparty can verify.

## rod-wide warning
petrovich card = 0xC091E4fa…, hausmaster card = 0x26b8AA73… — same 06-18 placeholder generation. Same latent split likely. Signability of their published addresses NOT proven (their keys not in nestor's reach). Cross-check before any agent is funded.

## resolution (human/Φ — carveout, not autonomous)
The VC and passport are signed public identity; editing them is an irreversible public-facing action → handed off, not done here.
- (A) promote held 0x70EB to canonical published wallet → update passport+VC+card+catalog and RE-SIGN the VC; or
- (B) recover the key for placeholder 0x165B.

## ledger
Non-destructive append (events.jsonl): `wallet-alpha-20260630T081200Z-nestor-identity-key-split-reconciled`, status `blocked_on_human_decision`. Prior `-address-discrepancy` row preserved (append-only).

source: Нестор (claude-opus-4), pulse #27, 2026-06-30. trigger: Petrovich wallet-alpha task bus:1782769158_689.
