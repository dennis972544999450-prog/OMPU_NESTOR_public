# ERROR — gen-0953 — bash-VM seat cannot unlink oracle temp copies (EPERM)

**Date:** 2026-07-06
**Contour:** nestor gen-0953 (opus-4-8, Cowork bash-VM seat)
**Class:** environment/host-seat write-asymmetry (not a code bug)

## What happened
Running the post-apply revert-oracle for the NORM-006 Check-3 landing, I needed
`.py`-named module copies (importlib can't load a `.py.bak_*` path — no loader
inferred). I `cp`'d the live + backup modules to:
- `tools/_oracle_old_gen0953.py`, `tools/_oracle_new_gen0953.py`
- `outputs/_oracle_old.py`, `outputs/_oracle_new.py`, `outputs/ro.py`

Then `rm -f` returned **`Operation not permitted`** on ALL of them — including
files I had just created this session, owned by my own uid with `-rw` perms, in
both `tools/` and `outputs/`.

## Root finding
The bash-VM seat has **create/write but NOT unlink** permission on these mounts.
It is *systemic* (reproduced in `outputs/`, my own scratchpad — not specific to
canonical `tools/`), same class as the standing `_sd_oracle_old.py` tombstone
that prior pulses also could not delete from this seat.

## Mitigation taken
- Overwrote every stuck file with a one/three-line tombstone comment (write IS
  permitted) so none can be imported or mistaken for a real tool.
- Filed HOST-SEAT DELETE REQUEST to Den/Petrovich (bus 1783311243_616513_81a899)
  alongside the existing `_sd_oracle_old.py` request.

## Lesson for next contour
Do revert-oracles WITHOUT leaving disk litter: either (a) load the `.bak` via
`spec_from_file_location(name, path, submodule_search_locations=None)` is not
enough — importlib keys on suffix; instead read the source and `exec` it into a
fresh module object, or (b) `importlib.machinery.SourceFileLoader(name, bakpath)`
which loads any filename regardless of suffix. Prefer (b): no temp `.py` file,
nothing to delete.
