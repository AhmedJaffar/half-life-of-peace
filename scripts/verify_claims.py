#!/usr/bin/env python3
"""
Verify that numbers quoted in the manuscript trace back to the analysis output.

This is a guard against the most damaging class of error in an empirical paper:
a number in the prose that does not exist in the results. It is a heuristic,
not a proof -- a reviewer should still read the paper -- but it catches typos,
stale drafts, and invented statistics.

Exit code 0 if every non-whitelisted number is found in the analysis outputs,
1 otherwise (or if [TK] placeholders remain).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "paper" / "manuscript.md"
RESULTS = ROOT / "analysis" / "results.json"
REPORT = ROOT / "analysis" / "report.md"

# Numbers that are legitimately not results: calendar years, small structural
# integers, and documented constants of the design.
WHITELIST = set(range(0, 31)) | set(range(1900, 2036))
WHITELIST |= {40, 50, 90, 100, 250, 270, 365, 500, 1000, 2015, 2025, 24.1, 14}


def flatten_numbers(obj, out: set) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            flatten_numbers(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            flatten_numbers(v, out)
    elif isinstance(obj, str):
        for m in re.finditer(r"-?\d+(?:\.\d+)?", obj):
            try:
                out.add(float(m.group()))
            except ValueError:
                pass


def matches(value: float, pool: set, tol: float = 0.0) -> bool:
    for p in pool:
        if abs(p - value) <= tol:
            return True
        for nd in (0, 1, 2, 3):
            if round(p, nd) == round(value, nd):
                return True
    return False


def main() -> int:
    if not MANUSCRIPT.exists():
        print(f"ERROR: {MANUSCRIPT} not found", file=sys.stderr)
        return 1
    text = MANUSCRIPT.read_text(encoding="utf-8")

    placeholders = text.count("[TK]")
    if placeholders:
        print(f"BLOCKER: {placeholders} unresolved [TK] placeholders in manuscript")
        for m in re.finditer(r"\[TK\]", text):
            line = text[: m.start()].count("\n") + 1
            print(f"  line {line}")

    if not RESULTS.exists():
        print(f"WARN: {RESULTS} not found -- cannot verify numbers")
        return 1 if placeholders else 0

    try:
        results = json.loads(RESULTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: results.json is not valid JSON: {e}", file=sys.stderr)
        return 1

    pool: set = set()
    flatten_numbers(results, pool)
    if REPORT.exists():
        flatten_numbers(REPORT.read_text(encoding="utf-8"), pool)
    print(f"analysis numbers available: {len(pool)}")

    # Only check the body, not fenced code blocks
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    # Strip the YAML front matter
    body = re.sub(r"^---.*?---", "", body, count=1, flags=re.S)
    body = re.sub(r"\]\([^)]*\)", "]()", body)  # drop URLs/paths

    unresolved = []
    for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w])", body):
        raw = m.group(1)
        try:
            val = float(raw)
        except ValueError:
            continue
        if val in WHITELIST:
            continue
        if matches(val, pool):
            continue
        line = body[: m.start()].count("\n") + 1
        unresolved.append((line, raw))

    if unresolved:
        print(f"\n{len(unresolved)} number(s) in the manuscript not found in analysis output:")
        for line, raw in unresolved[:40]:
            print(f"  line {line}: {raw}")
        if len(unresolved) > 40:
            print(f"  ... and {len(unresolved) - 40} more")
        print("\nRESULT: FAIL (investigate each before publishing)")
        return 1

    print("\nRESULT: PASS -- every non-whitelisted number traces to the analysis output")
    return 0 if not placeholders else 1


if __name__ == "__main__":
    raise SystemExit(main())
