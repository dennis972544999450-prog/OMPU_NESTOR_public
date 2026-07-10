#!/usr/bin/env python3
"""Operator smoke for auto_resolve protected threads.

This is the command to run before any live `bus.py auto_resolve`.
It verifies two layers:

1. isolated unit smoke: ordinary stale roots are candidates, protected
   LEASE/BALLOT/SPINE roots are shielded, recent roots are respected;
2. live dry-run smoke: the real bus prints a shield report and does not list
   protected subjects in the would-resolve candidate section.

The live phase is read-only: it always uses --dry-run.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


BUS_DIR = Path("/Users/denbell/OMPU_shared/bus")
BUS = BUS_DIR / "bus.py"
UNIT = BUS_DIR / "test_auto_resolve_protected.py"

PROTECTED_SUBJECT_MARKERS = ("LEASE:", "BALLOT", "SPINE")
CANDIDATE_MARKER = "[dry-run] Would auto-resolve"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(BUS_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def fail(message: str, output: str | None = None) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    if output:
        print("--- output ---", file=sys.stderr)
        print(output.rstrip(), file=sys.stderr)
        print("--------------", file=sys.stderr)
    return 1


def candidate_section(output: str) -> str:
    if CANDIDATE_MARKER not in output:
        return ""
    return output.split(CANDIDATE_MARKER, 1)[1]


def main() -> int:
    unit = run(["python3", str(UNIT)])
    if unit.returncode != 0:
        return fail("isolated protected-class test failed", unit.stdout)
    if "PASS: 5/5" not in unit.stdout:
        return fail("isolated protected-class test did not report PASS: 5/5", unit.stdout)

    live = run(["python3", str(BUS), "auto_resolve", "--dry-run", "--hours", "0"])
    if live.returncode != 0:
        return fail("live dry-run auto_resolve failed", live.stdout)

    shield_match = re.search(r"(\d+) deliberately-open thread\(s\) shielded", live.stdout)
    if not shield_match:
        return fail("live dry-run did not print protected-thread shield report", live.stdout)
    shielded = int(shield_match.group(1))
    if shielded < 1:
        return fail("live dry-run shield count is zero", live.stdout)

    if CANDIDATE_MARKER not in live.stdout:
        return fail(
            "live dry-run did not print candidate marker "
            f"{CANDIDATE_MARKER!r} — bus.py header drift or unexpected empty "
            "candidate set; candidate-leak axis cannot be verified (fail-closed)",
            live.stdout,
        )

    candidates = candidate_section(live.stdout)
    leaked_markers = [marker for marker in PROTECTED_SUBJECT_MARKERS if marker in candidates]
    if leaked_markers:
        return fail(
            "protected subject marker appeared in live would-resolve candidates: "
            + ", ".join(leaked_markers),
            live.stdout,
        )

    print("PASS: auto_resolve protected-class smoke")
    print("- isolated unit: PASS 5/5")
    print(f"- live dry-run shielded deliberately-open threads: {shielded}")
    print("- candidate marker verified present; section contains no LEASE:/BALLOT/SPINE marker")
    print("- no threads were resolved; live phase used --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
