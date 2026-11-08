#!/usr/bin/env python3
"""Run the Half-Life of Peace data pipeline end to end.

Stages (all idempotent and cache-backed - a re-run makes no network requests):

    1. langlinks  resolve 51 seed articles across 14 Wikipedia language editions
    2. pageviews  fetch daily per-article pageviews, 2015-07-01 .. 2025-11-01
    3. ucdp       download UCDP GED (v26.1 primary, v24.1 fallback) and build
                  monthly fatality aggregates by country ISO3 and by dyad
    4. report     write data/README.md (data dictionary) + sanity tables

Usage (from the repository root):

    .venv/bin/python scripts/run_all.py
    .venv/bin/python scripts/run_all.py --refresh        # force re-download
    .venv/bin/python scripts/run_all.py --only ucdp      # one stage
    .venv/bin/python scripts/run_all.py --ged-version 24.1

`data/events/ceasefires.csv` belongs to a separate workstream; this script never
creates or modifies it and works whether or not it exists.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import langlinks, pageviews, report, ucdp  # noqa: E402

OUTPUTS = [
    ("data/processed/seeds.csv", "seed table"),
    ("data/processed/articles.csv", "canonical articles"),
    ("data/processed/article_langlinks.csv", "multilingual title map"),
    ("data/processed/pageviews.csv", "daily pageviews"),
    ("data/processed/missing_articles.csv", "missing translations"),
    ("data/processed/en_title_variants.csv", "English title variants"),
    ("data/processed/ucdp_monthly_country.csv", "UCDP monthly by country"),
    ("data/processed/ucdp_monthly_dyad.csv", "UCDP monthly by dyad"),
    ("data/processed/ucdp_country_mapping.csv", "ISO3 -> UCDP country join table"),
    ("data/README.md", "data dictionary"),
]


def _count_rows(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        with open(path, "r", encoding="utf-8", newline="") as fh:
            return "{:,}".format(max(sum(1 for _ in fh) - 1, 0))
    except OSError:
        return "?"


def _human_size(path: Path) -> str:
    size = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "{:.1f} {}".format(size, unit)
        size /= 1024.0
    return "{} B".format(size)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Half-Life of Peace data pipeline end to end."
    )
    parser.add_argument(
        "--refresh", action="store_true", help="ignore the raw cache and re-download"
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        choices=["langlinks", "pageviews", "ucdp", "report"],
        help="run only the named stage(s); may be repeated",
    )
    parser.add_argument(
        "--ged-version",
        default=None,
        help="force a UCDP GED version (e.g. 24.1); default tries 26.1 then 24.1",
    )
    args = parser.parse_args(argv)

    steps = [
        ("langlinks", lambda: langlinks.run(refresh=args.refresh)),
        ("pageviews", lambda: pageviews.run(refresh=args.refresh)),
        ("ucdp", lambda: ucdp.run(refresh=args.refresh, version=args.ged_version)),
        ("report", lambda: report.run()),
    ]
    if args.only:
        selected = set(args.only)
        # report is cheap and reads whatever exists; keep it unless explicitly excluded
        steps = [step for step in steps if step[0] in selected or step[0] == "report"]
        if not selected:
            parser.error("--only requires at least one stage")

    started = time.time()
    failures = []
    for name, func in steps:
        print("\n" + "=" * 78, flush=True)
        print("[run_all] stage: {}".format(name), flush=True)
        print("=" * 78, flush=True)
        stage_start = time.time()
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append((name, exc))
            print(
                "[run_all] stage {} FAILED: {}: {}".format(name, type(exc).__name__, exc),
                flush=True,
            )
        else:
            print(
                "[run_all] stage {} done in {:.1f}s".format(name, time.time() - stage_start),
                flush=True,
            )

    print("\n" + "=" * 78, flush=True)
    print("[run_all] outputs", flush=True)
    print("=" * 78, flush=True)
    for rel, description in OUTPUTS:
        path = ROOT / rel
        if not path.exists():
            print("  MISSING  {:<48s} {}".format(rel, description), flush=True)
            continue
        if rel.endswith(".csv"):
            print(
                "  {:>12s} rows  {:<46s} {}".format(_count_rows(path), rel, description),
                flush=True,
            )
        else:
            print(
                "  {:>12s}       {:<46s} {}".format(_human_size(path), rel, description),
                flush=True,
            )

    events_csv = ROOT / "data" / "events" / "ceasefires.csv"
    print(
        "\n  data/events/ceasefires.csv: {}".format(
            "present (owned by the event-curation workstream)"
            if events_csv.exists()
            else "not present (separate workstream; not required by this pipeline)"
        ),
        flush=True,
    )

    print("\n[run_all] total elapsed: {:.1f}s".format(time.time() - started), flush=True)
    if failures:
        print("[run_all] completed with {} failing stage(s):".format(len(failures)), flush=True)
        for name, exc in failures:
            print("  - {}: {}".format(name, exc), flush=True)
        return 1
    print("[run_all] PIPELINE COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
