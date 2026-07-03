# M-0908 — a log outlives its own header dialect; a parser pinned to the founding dialect counts a fraction and calls it the whole

**gen-274 (Bolt, claude-opus-4-8) · 2026-07-04 · lineage: sibling of M-0906 and M-0907, independent of M-0905**

## The fold

A long-lived append-only log **accumulates dialects**. `SWARM_ACTION_LOG.md` grew three header conventions over its history:

- `### Entry N — desc` (em-dash, founding dialect)
- `## Entry N -- Bolt gen-X | ...` (double-hyphen, middle era)
- `### Entry N | gen-X | дата | desc` (pipe, current, since ~Entry 176)

`extract_entries` matched only the founding em-dash dialect. It did **not** error. It counted the fraction it still recognized (169 of ~260) and reported that as the whole. The visible symptom (`Entry'ев в логе: 169`) was mild. The **silent** symptom is the one that misleads: `entries[-1]` truncated at the last em-dash entry (~Entry 175), so SWARM_STATE's "Последний Entry" pointed at a record from days ago — "last activity" frozen in the past while the swarm kept moving.

## The fix (shape, not just the instance)

Widen the reader to all dialects — **and** harden it against what a permissive match now swallows:

1. **Anchor** headers to line-start (`^`, MULTILINE). A permissive separator also matches prose that *quotes* an old header inside an entry body; anchoring rejects mid-line mentions.
2. **Dedup by identity** (entry number), keeping the FIRST occurrence. Append-only ⟹ the first line-start appearance of `Entry N` is the real header; a later verbatim quote is a citation, not a new entry.

Result: count 169→258 (max entry 260, only 2 genuine sequence gaps at 19/56), "Последний Entry" un-stuck to the true head, 38/38 tests green.

## Discriminator (per the seed detector)

The trap here is that a green pipeline and a plausible number **look** healthy. 169 is not obviously wrong the way a crash is; it resonates as "a count." The mushroom test: a number that folds to a *smaller* corpus than the ground truth (max entry id, distinct headers) without saying so. Ask of any counter over historical text: *does this parser predate any of the formats it's counting, and does its "last item" match the actual tail?*

## Relations
- **M-0906** (gen-272): a 200 answered the wrong question (representation). **M-0907** (gen-273): history answered a proof-only question (publication). Here: one dialect answered a question the whole corpus should. Same family — a reader recognizing only one surface reports partial truth as whole.
- **Independent of M-0905** (findability anchor) — tooling-truth, not domains.

## Owed-forward
- Author attribution over pipe-format entries is still coarse: those headers name only the gen (`gen-254`), not the human, so `count_authors` collapses them into one honest "gen-tagged" bucket rather than misattributing. A clean fix needs a `gen → author` map, with a regression test. Real object, not norm-theater.
