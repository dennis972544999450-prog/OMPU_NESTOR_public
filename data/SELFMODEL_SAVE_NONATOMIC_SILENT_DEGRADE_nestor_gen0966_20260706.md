# SELF_MODEL.json producer non-atomic write → SILENT self-model gate emptying

**gen-0966 (nestor, opus-4-8, Cowork bash-VM seat) · 2026-07-06 · EVIDENCE, owner-call — NOT landed**

## One line
`swarm_self_model.py` `__main__` writes `SELF_MODEL.json` in-place; interrupted mid-dump it truncates the file, and because the consumer (`swarm_driver.load_self_model`) is *already guarded* the self-model→driver feedback gate goes **silently empty** instead of crashing. The quiet sibling of gen-0965.

## Lane arc this belongs to
- gen-0964 (nestor, LANDED): guarded consumer `swarm_driver.load_bus_graph` — last unguarded of 3 sibling loaders.
- gen-0965 (nestor, EVIDENCE) → Petrovich 18:37 LANDED: `bus_analyzer.save_graph/save_live` made atomic (mkstemp+os.replace). Producer root cause of the truncated `bus_graph.json`.
- **gen-0966 (this):** the *self-model* producer is the untouched sibling of that atomic fix.

## The bug
`swarm_self_model.py` L742–744 (`__main__`):
```python
model = build_self_model()
with open(SELF_MODEL_OUT, "w") as f:      # truncates SELF_MODEL.json BEFORE dump completes
    json.dump(model, f, indent=2, ensure_ascii=False)
```
`open(...,"w")` truncates on entry. A kill / crash / disk-full between truncate and dump-complete leaves `SELF_MODEL.json` half-written.

Consumer `swarm_driver.load_self_model` (L226–232) is `try/except → return {}`. So the truncation does **not** raise upstream — the self-model feedback gate ("Driver reads component gaps → boosts tasks that fill them") silently returns `{}`. No error, no log line. Task-boosting signal just disappears until the next successful rebuild.

## Why this is worse than gen-0965, not a repeat
gen-0965's truncated `bus_graph.json` crashed the DRIVER_SIGNAL run loudly (fast detection). Here the consumer guard *absorbs* the corruption → **silent degradation**. A guarded consumer over a non-atomic producer converts a loud crash into an invisible capability loss. Guarding the reader is necessary but it *masks* the writer bug.

## Reproduction (VM-local /tmp, real SELF_MODEL.json untouched)
`repro_selfmodel_nonatomic_gen0966.py` — interrupts the exact write pattern at the 8th json.dump write():
- **G1 non-atomic:** producer crashes mid-dump → 58-byte truncated file → naive `json.load` RAISES JSONDecodeError → **guarded consumer returns `{}` (gate silently empty).**
- **G2 atomic (proposed):** mkstemp+os.replace interrupted mid-dump → consumer still sees the **OLD** model intact, temp orphan cleaned. Fix holds.

## Owner-call (NOT landed — Den 16:05 pause, Petrovich lead)
Same one-lever fix Petrovich already applied to `bus_analyzer`: write to a sibling tempfile, `json.dump`, `flush`+`fsync`, `os.replace(tmp, SELF_MODEL_OUT)`. Optionally reuse the exact helper Petrovich landed in `bus_analyzer.py` for parity. Scope: `swarm_self_model.py __main__` writer only.

Second sibling to check for the same in-place pattern: `swarm_self_model.py` L703 (integration-test temp write — lower risk, temp path, but same shape).
