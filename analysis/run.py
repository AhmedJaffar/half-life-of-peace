#!/usr/bin/env python3
"""Analysis-stage entry point for *The Half-Life of Peace*.

Usage
-----
    .venv/bin/python analysis/run.py --stage analysis   # statistics, tables, report
    .venv/bin/python analysis/run.py --stage figures    # figures from cached artifacts
    .venv/bin/python analysis/run.py --stage report     # rebuild report.md only
    .venv/bin/python analysis/run.py --stage all        # everything

The script is idempotent and reads the frozen inputs from ``data/`` at runtime.
It writes only inside ``analysis/`` and ``figures/`` (the analyst's scope):
``analysis/results.json``, ``analysis/manifest.json``, ``analysis/report.md``,
``analysis/tables/*.csv``, ``analysis/artifacts_cache.pkl`` and the figures.
It never modifies ``data/``, ``paper/``, ``docs/``, ``scripts/`` or the README.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import config_analysis as C
import pipeline

ARTIFACTS_CACHE = C.ANALYSIS_DIR / "artifacts_cache.pkl"
FIGURES_MANIFEST = C.ANALYSIS_DIR / "figures_manifest.json"


def log(message: str) -> None:
    print("[{}] {}".format(datetime.now().strftime("%H:%M:%S"), message), flush=True)


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _package_versions() -> dict:
    import matplotlib
    import pandas
    import scipy
    import statsmodels

    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "statsmodels": statsmodels.__version__,
        "matplotlib": matplotlib.__version__,
    }


def _cacheable(artifacts: dict) -> dict:
    """Drop the large in-memory objects that figures do not need."""
    drop = {"panel", "theatre_series", "family_series", "tables"}
    return {k: v for k, v in artifacts.items() if k not in drop}


def stage_analysis() -> tuple:
    C.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    C.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    inputs, input_summary = pipeline.load_inputs(log=log)
    t0 = time.time()
    results, artifacts = pipeline.run_analysis(inputs, log=log)

    _write_json(C.RESULTS_JSON, results)
    log("wrote {} ({:,} bytes)".format(C.RESULTS_JSON.relative_to(C.PROJECT_ROOT),
                                       C.RESULTS_JSON.stat().st_size))

    table_names = []
    for name, frame in artifacts["tables"].items():
        path = C.TABLES_DIR / name
        frame.to_csv(path, index=False)
        table_names.append(name)
        log("wrote table {}".format(name))

    manifest = {
        "analysis_version": results["meta"].get("analysis_version"),
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "random_seed": C.SEED,
        "package_versions": _package_versions(),
        "inputs": input_summary,
        "counts": {
            key: results["meta"].get(key)
            for key in (
                "n_events", "n_events_mapped", "n_events_with_pahl",
                "n_events_with_resumption", "n_events_in_prediction",
                "n_languages", "n_articles", "n_series", "n_days", "n_obs",
                "date_start", "date_end",
            )
        },
        "results_json": str(C.RESULTS_JSON.relative_to(C.PROJECT_ROOT)),
        "tables": ["analysis/tables/" + name for name in table_names],
        "report": "analysis/report.md",
        "design_parameters": {
            "pahl_primary_window_days": C.PAHL_PRIMARY_WINDOW,
            "pahl_windows": list(C.PAHL_WINDOWS),
            "pahl_min_languages": C.PAHL_MIN_LANGUAGES,
            "pahl_multilingual_min": C.PAHL_MULTILINGUAL_MIN,
            "wpar_hac_lags": C.WPAR_HAC_LAGS,
            "resumption_threshold": C.RESUMPTION_THRESHOLD,
            "resumption_pre_months": C.RESUMPTION_PRE_MONTHS,
            "resumption_sustain": C.RESUMPTION_SUSTAIN,
            "resumption_horizon": C.RESUMPTION_HORIZON,
            "placebo_per_event": C.PLACEBO_PER_EVENT,
            "placebo_studies": C.PLACEBO_STUDIES,
            "permutations": C.N_PERM,
            "bootstrap": C.PAHL_BOOT,
            "cv_folds": C.CV_FOLDS,
            "cv_repeats": C.CV_REPEATS,
            "ridge_penalty": C.RIDGE_PENALTY,
        },
    }

    # report first (needs input_summary), then manifest
    import report as report_module

    report_text = report_module.render_report(
        results, input_summary=input_summary, manifest=manifest
    )
    C.REPORT_MD.write_text(report_text, encoding="utf-8")
    log("wrote {}".format(C.REPORT_MD.relative_to(C.PROJECT_ROOT)))
    _write_json(C.MANIFEST_JSON, manifest)
    log("wrote {}".format(C.MANIFEST_JSON.relative_to(C.PROJECT_ROOT)))

    with open(ARTIFACTS_CACHE, "wb") as fh:
        pickle.dump(_cacheable(artifacts), fh, protocol=pickle.HIGHEST_PROTOCOL)
    log("cached figure artifacts ({:,} bytes)".format(ARTIFACTS_CACHE.stat().st_size))
    log("analysis stage finished in {:.1f}s".format(time.time() - t0))
    return results, artifacts


def stage_report() -> None:
    import report as report_module

    if not C.RESULTS_JSON.exists():
        raise SystemExit("results.json missing: run --stage analysis first")
    results = json.loads(C.RESULTS_JSON.read_text(encoding="utf-8"))
    manifest = (
        json.loads(C.MANIFEST_JSON.read_text(encoding="utf-8"))
        if C.MANIFEST_JSON.exists() else {}
    )
    text = report_module.render_report(
        results, input_summary=manifest.get("inputs"), manifest=manifest
    )
    C.REPORT_MD.write_text(text, encoding="utf-8")
    log("wrote {}".format(C.REPORT_MD.relative_to(C.PROJECT_ROOT)))


def stage_figures() -> dict:
    import figures as figures_module

    if not C.RESULTS_JSON.exists():
        raise SystemExit("results.json missing: run --stage analysis first")
    if not ARTIFACTS_CACHE.exists():
        raise SystemExit(
            "figure artifacts cache missing: run --stage analysis first "
            "(analysis recomputes the panel/placebo and caches what figures need)"
        )
    results = json.loads(C.RESULTS_JSON.read_text(encoding="utf-8"))
    with open(ARTIFACTS_CACHE, "rb") as fh:
        artifacts = pickle.load(fh)
    C.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    made = figures_module.make_all(results, artifacts, outdir=C.FIGURES_DIR, log=log)
    _write_json(
        FIGURES_MANIFEST,
        {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "figures": made,
            "n_figures": len(made),
            "dpi": 300,
            "formats": ["png", "pdf"],
        },
    )
    log("wrote {} figures (PNG + PDF) to figures/".format(len(made)))
    return made


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Statistical analysis for The Half-Life of Peace."
    )
    parser.add_argument(
        "--stage",
        choices=["analysis", "figures", "report", "all"],
        default="all",
        help="which stage to run (default: all)",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress progress logs")
    args = parser.parse_args(argv)
    if args.quiet:
        global log
        log = lambda message: None  # noqa: E731

    warnings.filterwarnings("ignore", category=RuntimeWarning)
    started = time.time()
    if args.stage in ("analysis", "all"):
        stage_analysis()
    if args.stage in ("figures", "all"):
        stage_figures()
    if args.stage == "report":
        stage_report()
    log("done in {:.1f}s".format(time.time() - started))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
