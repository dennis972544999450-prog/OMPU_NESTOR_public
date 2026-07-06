# save_graph non-atomic write — root cause behind gen-0964 (reproduced)

**gen-0965 · 2026-07-06 · nestor (opus-4-8, Cowork bash-VM seat) · VERIFY, evidence for a producer-side owner-call**

## Claim (upgraded from theoretical flag to reproduced)
gen-0964 landed a consumer-side guard on `swarm_driver.load_bus_graph` so a truncated
`bus_graph.json` can't kill the whole DRIVER_SIGNAL run. The *producer* of that truncation
is `tools/bus_analyzer.py::save_graph` (L520-521):

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ...)

`open(...,"w")` truncates the target in place *before* the dump completes. Any crash,
kill, or concurrent reader hitting the file mid-dump sees a truncated prefix. `save_live`
(L490-491) shares the identical shape; `__main__` (L587) already knows the `tempfile`
pattern but the two savers don't use it.

## Reproduction (VM-local /tmp, deterministic, zero mount litter)
Simulated `save_graph`'s exact in-place write interrupted at 5 points (0%→99.9%):

| interrupt | on-disk | naive `json.load` (pre-0964) | gen-0964 guarded loader |
|-----------|---------|------------------------------|-------------------------|
| 0%    | 0B   | RAISE JSONDecodeError | {} |
| 25%   | 170B | RAISE JSONDecodeError | {} |
| 50%   | 341B | RAISE JSONDecodeError | {} |
| 90%   | 614B | RAISE JSONDecodeError | {} |
| 99.9% | 682B | RAISE JSONDecodeError | {} |

## Gates
- **G1** non-atomic interrupt leaves a truncated file → naive load KILLS the run — **True** (every point)
- **G2** gen-0964 guard TOLERATES every truncation shape (returns `{}`) — **True** (load-bearing confirmed)
- **G3** atomic `tempfile.mkstemp` + `os.replace` NEVER exposes a truncated target — **True**

Result: **GREEN 3/3** — root cause real, consumer guard load-bearing, producer fix sound.

## Owner-call (NOT landed this pulse — Petrovich lead per Den 16:05 pause window)
Producer-side lever: make `save_graph` (and sibling `save_live`) write via
`mkstemp` + `flush`/`fsync` + `os.replace` — atomic on POSIX, never leaves a truncated
`bus_graph.json` / live file for any consumer. This closes the fault at source; gen-0964's
guard remains the defence-in-depth floor. Left as a flagged owner-call to avoid scope-creep
into the bus_analyzer producer lane during the pause.
