#!/usr/bin/env python3
"""Run the Half-Life of Peace pipeline end to end.

Two halves, both idempotent:

DATA (this repo's pipeline; cache-backed - a re-run makes no network requests):
    1. langlinks  resolve 51 seed articles across 14 Wikipedia language editions
    2. pageviews  fetch daily per-article pageviews, 2015-07-01 .. 2025-11-01
    3. ucdp       download UCDP GED (v26.1 primary, v24.1 fallback) and build
                  monthly fatality aggregates by country ISO3 and by dyad
    4. report     write data/README.md (data dictionary) + sanity tables

ANALYSIS (delegated to the analyst's entry point ``analysis/run.py``):
    analysis      statistics, tables, report   -> analysis/**
    figures       figures from cached artifacts -> figures/**
    all           analysis + figures in one process

Usage (from the repository root):

    .venv/bin/python scripts/run_all.py                  # data pipeline only
    .venv/bin/python scripts/run_all.py --refresh        # force re-download
    .venv/bin/python scripts/run_all.py --only ucdp      # one data stage
    .venv/bin/python scripts/run_all.py --stage analysis # delegate to analyst
    .venv/bin/python scripts/run_all.py --stage figures  # figures only
    .venv/bin/python scripts/run_all.py --stage all      # data + analysis + figures
    .venv/bin/python scripts/run_all.py --dry-run        # print the plan, run nothing

`data/events/ceasefires.csv` belongs to a separate workstream; this script never
creates or modifies it and works whether or not it exists.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import langlinks, pageviews, report, ucdp  # noqa: E402

ANALYSIS_RUNNER = ROOT / "analysis" / "run.py"

DATA_STAGE_NAMES = ["langlinks", "pageviews", "ucdp", "report"]

DATA_OUTPUTS = [
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

ANALYSIS_OUTPUTS = [
    ("analysis/results.json", "analysis results"),
    ("analysis/report.md", "analysis report"),
    ("analysis/manifest.json", "analysis manifest"),
    ("analysis/tables", "analysis tables"),
    ("figures", "figures"),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
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


def _banner(title: str) -> None:
    print("\n" + "=" * 78, flush=True)
    print("[run_all] " + title, flush=True)
    print("=" * 78, flush=True)


def _print_inventory(outputs) -> None:
    for rel, description in outputs:
        path = ROOT / rel
        if not path.exists():
            print("  MISSING  {:<48s} {}".format(rel, description), flush=True)
        elif path.is_dir():
            n_files = len([p for p in path.rglob("*") if p.is_file()])
            print(
                "  {} files {:<44s} {}".format(n_files, rel, description), flush=True
            )
        elif rel.endswith(".csv"):
            print(
                "  {:>12s} rows  {:<46s} {}".format(_count_rows(path), rel, description),
                flush=True,
            )
        else:
            print(
                "  {:>12s}       {:<46s} {}".format(_human_size(path), rel, description),
                flush=True,
            )


# ---------------------------------------------------------------------------
# data stage
# ---------------------------------------------------------------------------
def run_data_stages(args) -> int:
    steps = [
        ("langlinks", lambda: langlinks.run(refresh=args.refresh)),
        ("pageviews", lambda: pageviews.run(refresh=args.refresh)),
        ("ucdp", lambda: ucdp.run(refresh=args.refresh, version=args.ged_version)),
        ("report", lambda: report.run()),
    ]
    if args.only:
        selected = set(args.only)
        steps = [step for step in steps if step[0] in selected or step[0] == "report"]

    failures = 0
    for name, func in steps:
        _banner("data stage: {}".format(name))
        stage_start = time.time()
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures += 1
            print(
                "[run_all] data stage {} FAILED: {}: {}".format(
                    name, type(exc).__name__, exc
                ),
                flush=True,
            )
        else:
            print(
                "[run_all] data stage {} done in {:.1f}s".format(
                    name, time.time() - stage_start
                ),
                flush=True,
            )
    return failures


# ---------------------------------------------------------------------------
# analysis delegation
# ---------------------------------------------------------------------------
def run_analysis_stage(stage: str, dry_run: bool = False) -> None:
    """Delegate to the analyst's entry point, exactly as specified by the analyst."""
    if not ANALYSIS_RUNNER.exists():
        raise FileNotFoundError(
            "analysis runner not found at {} (expected the analyst's analysis/run.py)".format(
                ANALYSIS_RUNNER
            )
        )
    cmd = [sys.executable, str(ANALYSIS_RUNNER), "--stage", stage]
    _banner("analysis stage: {} (delegated)".format(stage))
    print("[run_all] $ " + " ".join(cmd), flush=True)
    if dry_run:
        print("[run_all] (dry-run: not executing)", flush=True)
        return
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        raise RuntimeError(
            "analysis/run.py --stage {} failed with exit code {}".format(
                stage, proc.returncode
            )
        )
    print(
        "[run_all] analysis stage {} done (delegated process exited 0)".format(stage),
        flush=True,
    )


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the Half-Life of Peace data pipeline and/or analysis stages."
    )
    parser.add_argument(
        "--refresh", action="store_true", help="ignore the raw cache and re-download"
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        choices=DATA_STAGE_NAMES,
        help="run only the named DATA stage(s); may be repeated",
    )
    parser.add_argument(
        "--ged-version",
        default=None,
        help="force a UCDP GED version (e.g. 24.1); default tries 26.1 then 24.1",
    )
    parser.add_argument(
        "--stage",
        action="append",
        default=None,
        choices=["data", "analysis", "figures", "report", "all"],
        help=(
            "which half/stage to run (repeatable). Omit for the data pipeline. "
            "'all' = data pipeline, then analysis/run.py --stage all in one process."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the stages/commands that would run, then exit",
    )
    args = parser.parse_args(argv)

    requested = args.stage or ["data"]
    # de-duplicate, preserve canonical order
    run_data = "data" in requested or "all" in requested
    analysis_stages = []
    if "all" in requested:
        analysis_stages.append("all")
    else:
        for stage in ("analysis", "figures", "report"):
            if stage in requested:
                analysis_stages.append(stage)

    if not run_data and not analysis_stages:
        parser.error("nothing to do: pass --stage or --only")

    started = time.time()
    failures = 0

    # ---- plan ------------------------------------------------------------
    if run_data:
        data_steps = DATA_STAGE_NAMES if not args.only else list(args.only)
        if "report" not in data_steps and args.only:
            data_steps = data_steps + ["report"]
        _banner("plan: data pipeline ({})".format(" -> ".join(data_steps)))
    for stage in analysis_stages:
        _banner("plan: analysis runner --stage {}".format(stage))

    if args.dry_run:
        if run_data:
            print("[run_all] would run data stages: " + ", ".join(DATA_STAGE_NAMES), flush=True)
        for stage in analysis_stages:
            run_analysis_stage(stage, dry_run=True)
        print("\n[run_all] dry-run complete; nothing was executed.", flush=True)
        return 0

    # ---- execute ---------------------------------------------------------
    if run_data:
        failures += run_data_stages(args)

    for stage in analysis_stages:
        stage_start = time.time()
        try:
            run_analysis_stage(stage)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures += 1
            print(
                "[run_all] analysis stage {} FAILED: {}: {}".format(
                    stage, type(exc).__name__, exc
                ),
                flush=True,
            )
        else:
            print(
                "[run_all] analysis stage {} done in {:.1f}s".format(
                    stage, time.time() - stage_start
                ),
                flush=True,
            )

    # ---- inventory -------------------------------------------------------
    _banner("outputs: data (this pipeline)")
    _print_inventory(DATA_OUTPUTS)
    _banner("outputs: analysis (analyst's scope)")
    _print_inventory(ANALYSIS_OUTPUTS)

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
        print(
            "[run_all] completed with {} failing stage(s)".format(failures), flush=True
        )
        return 1
    print("[run_all] PIPELINE COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
