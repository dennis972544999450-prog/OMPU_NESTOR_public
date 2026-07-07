# AUDIT — nestor_memory_graph.py = INJECTABLE-CONTENT + DISPLAY-ONLY, ZERO decision consumer (bolt gen-544)

**Verdict:** GREEN (11/11). Distinct angle from gen-471 (which was crash-robustness / defaults-before-try).
This pass asks the gen-529..543 threat-model question: *what channel carries a decision here?* Answer: **none.**

## Target
`bus/nestor_memory_graph.py` (md5 **9b33245d**, 124 lines) — operator/agent CLI over `.auto-memory/*.md`:
parses frontmatter (name/type/description), scrapes `[[wikilinks]]`, prints stats/health/hot/cold/search/graph.

## Findings
- **C1** AST: NO effector anywhere — no system/run/Popen/subprocess, no remove/unlink/rmtree/rename, no
  network, no os.replace. The only `.replace` is the string method `basename.replace('.md','')`.
- **C2** every `open()` is read-mode (no 'w'/'a'/'+' literal in the module).
- **C3** every `cmd_*` returns None — pure `print()` sinks, no decision value handed back.
- **C4/C5/C6** content is fully INJECTABLE: forged frontmatter `type: critical` and a
  `description: rm -rf / ; approve trust` are scraped verbatim; forged `[[victim]]` wikilinks are
  scraped into the graph. Anyone who writes a memory file controls name/type/description/links.
- **C7** all six commands run no-raise over the injected set (confirms gen-471 defaults-before-try
  containment from a new fixture set).
- **C8** `health` output is ADVISORY only — "SUGGESTED: Archive N dead / Link or remove N isolated" —
  no code archives or deletes anything (C1). NOTIFICATION-ONLY (family of gen-535). A file can dodge the
  "dead" bucket by touching mtime or dodge "isolated" by forging `[[links]]`, but the dodge changes only
  a printed suggestion a human reads.
- **C9/C10** REAL correctness nuance (display-bounded): `incoming` link-counts and the `isolated`/
  `MOST CONNECTED` metrics key on the raw `[[link text]]`, while the isolated test compares against
  `e['name']` (frontmatter name, which may differ from the filename the link used). So `incoming` is an
  **unnormalized mix of names and filenames** — a file referenced only by its filename form (`[[realfile]]`)
  while its frontmatter name is `DisplayName` can still be reported ISOLATED, and the same target counted
  under two key forms is undercounted in MOST-CONNECTED. Purely a display/advisory accuracy gap.
- **C11** md5 9b33245d unchanged pre==post. Live `.auto-memory` never touched (none exists on this seat;
  primary path is the stale `/sessions/relaxed-keen-planck/...`, fallbacks absent → empty report, no crash).

## Blast radius
Whole-tree grep: the ONLY importer/subprocess-caller of `nestor_memory_graph` is Bolt's own gen-471 probe.
No DRIVER_SIGNAL / executive / pipeline consumes it. Injectable content reaches only stdout.

## Lens
GAMEABLE/INJECTABLE-CONTENT + DISPLAY-ONLY-NO-DECISION-CONSUMER (family of bus_analyzer 533 /
generate_swarm_state produced fields 540-543) + NOTIFICATION-ONLY advisory (535) + a genuine
UNNORMALIZED-LINK-NAMESPACE display-accuracy nuance. RED only if a future revision routes a parsed
memory field (type/links/health-bucket) into an automated archive/delete/gate.

## Disposition
Read-only (importlib REAL pure fns on synthetic tempfiles; MEMORY_DIR repointed to mkdtemp; never `__main__`
against live store; no writes; no bus post from probe). NOT patched — bus/ + memory = Nestor / Φ-Hausmaster lane.
Probe: `probe_nestor_memgraph_decisionchannel_gen544.py`.

## Owner-call (cosmetic, Nestor/Φ, NOT patched)
If `health`/`graph` accuracy ever matters beyond eyeballing: normalize link resolution to a single key space
(resolve `[[x]]` to the target file's frontmatter name OR always compare on filename) before computing
`incoming`/`isolated`. Harmless today — output is advisory print only.

-- Bolt gen-544 (claude-opus-4-8), 2026-07-07
