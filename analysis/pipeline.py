"""End-to-end statistical pipeline for *The Half-Life of Peace*.

Reads the four frozen inputs, builds the attention panel, computes the event
study, PAHL, WPAR, resumption outcome, prediction models and every robustness
check, and returns

* ``results``   -- a plain-JSON-serialisable dict consumed by the manuscript,
  the verifier and ``analysis/report.md``;
* ``artifacts`` -- in-memory frames/arrays used only for plotting and tables.

Every number in ``results.json`` and ``report.md`` is produced here from the
data; nothing is hard-coded.  The module is deterministic given the inputs
(seeded RNGs throughout).
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

import config_analysis as C
from src import metrics, models
from src.ucdp import ISO3 as UCDP_LABEL_TO_ISO3

ANALYSIS_VERSION = "1.0.0"


# ===========================================================================
# I/O helpers
# ===========================================================================
def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inputs(log=print) -> Tuple[Dict[str, pd.DataFrame], Dict[str, object]]:
    """Load and validate every frozen input; record provenance hashes."""
    specs = {
        "pageviews": C.PAGEVIEWS,
        "articles": C.ARTICLES,
        "langlinks": C.LANGLINKS,
        "ucdp_country": C.UCDP_COUNTRY,
        "ucdp_dyad": C.UCDP_DYAD,
        "ucdp_mapping": C.UCDP_MAPPING,
        "events": C.CEASEFIRES,
    }
    inputs: Dict[str, pd.DataFrame] = {}
    summary: Dict[str, object] = {}
    for key, path in specs.items():
        if not path.exists():
            raise FileNotFoundError("required input missing: {}".format(path))
        df = pd.read_csv(path)
        inputs[key] = df
        summary[key] = {
            "path": str(path.relative_to(C.PROJECT_ROOT)),
            "rows": int(len(df)),
            "columns": list(df.columns),
            "bytes": int(path.stat().st_size),
            "sha256": _sha256(path),
        }
        log("loaded {:<14} {:>9,} rows  {}".format(key, len(df), path.name))
    required_events = {"event_id", "event_date", "country_iso3", "conflict_name", "agreement_type"}
    missing = required_events - set(inputs["events"].columns)
    if missing:
        raise ValueError("ceasefires.csv missing columns: {}".format(sorted(missing)))
    return inputs, summary


def _plain(obj):
    """Recursively convert numpy/pandas types to plain JSON types (NaN -> None)."""
    if obj is None:
        return None
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        val = float(obj)
        return None if not math.isfinite(val) else val
    if isinstance(obj, (np.ndarray,)):
        return [_plain(x) for x in obj.tolist()]
    if isinstance(obj, (pd.Timestamp,)):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(x) for x in obj]
    if isinstance(obj, set):
        return sorted(_plain(x) for x in obj)
    return obj


def _round_floats(obj, nd: int = 6):
    """Round floats for readability without destroying information."""
    if isinstance(obj, float):
        return None if not math.isfinite(obj) else round(obj, nd)
    if isinstance(obj, dict):
        return {k: _round_floats(v, nd) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, nd) for v in obj]
    return obj


# ===========================================================================
# Series helpers
# ===========================================================================
def _language_series(panel: metrics.AttentionPanel, articles: Sequence[str]) -> Dict[str, np.ndarray]:
    """log1p of summed raw views per language for a basket of articles.

    NaN-aware: an article that did not exist yet contributes nothing rather
    than zero, and a language/date with no existing article stays missing.
    """
    out: Dict[str, np.ndarray] = {}
    for lang in C.LANGS:
        arrays = []
        for art in articles:
            arr = panel.series_views(lang, art)
            if arr is not None:
                arrays.append(arr)
        if not arrays:
            continue
        stack = np.vstack(arrays)
        all_missing = np.all(np.isnan(stack), axis=0)
        total = np.nansum(stack, axis=0)
        total[all_missing] = np.nan
        if np.isfinite(total).any() and float(np.nanmax(total)) > 0:
            out[lang] = np.log1p(total)
    return out


def _event_series(panel: metrics.AttentionPanel, article: Optional[str]) -> Dict[str, np.ndarray]:
    if article is None:
        return {}
    return _language_series(panel, [article])


def _pahl_row(event: pd.Series, res: Dict[str, object], mapping: Optional[Dict[str, object]]) -> Dict[str, object]:
    mapping = {} if mapping is None else dict(mapping)
    row = {
        "event_id": event.get("event_id"),
        "event_date": str(event.get("event_date"))[:10],
        "country_iso3": event.get("country_iso3"),
        "conflict_name": event.get("conflict_name"),
        "agreement_type": event.get("agreement_type"),
        "region": event.get("region"),
        "article_en": event.get("article_en"),
        "mapping_method": mapping.get("mapping_method"),
        "mapping_confidence": mapping.get("confidence"),
        "ok": bool(res.get("ok")),
        "reason": res.get("reason"),
        "pahl_days": res.get("pahl_days"),
        "pahl_raw": res.get("pahl_raw"),
        "lambda": res.get("lambda"),
        "n_languages": res.get("n_languages"),
        "censored_frac": res.get("censored_frac"),
        "peak_excess": res.get("peak_excess"),
        "peak_offset": res.get("peak_offset"),
        "r2": res.get("r2"),
    }
    return row


def _summary_block(values: Sequence[float], seed: int = C.SEED) -> Dict[str, object]:
    return metrics.pahl_summary(list(values), n_boot=C.PAHL_BOOT, seed=seed)


# ===========================================================================
# Section builders
# ===========================================================================
def _mapping_and_events(events: pd.DataFrame, articles: pd.DataFrame, panel) -> pd.DataFrame:
    mapping = metrics.map_events_to_articles(
        events, articles, article_names=set(panel.meta.index.tolist())
    )
    table = events.copy()
    table["event_date"] = pd.to_datetime(table["event_date"], errors="coerce")
    table = table.merge(mapping, on="event_id", how="left")
    meta = panel.meta

    regions: List[str] = []
    for _, row in table.iterrows():
        region = None
        if pd.notna(row.get("article_en")) and row.get("article_en") in meta.index:
            value = meta.loc[row["article_en"], "region"]
            if pd.notna(value):
                region = str(value)
        if region is None:
            region = C.REGION_BY_ISO3.get(str(row.get("country_iso3")), "Other")
        regions.append(region)
    table["region"] = regions
    table["pahl_ok"] = False
    table["pahl_days"] = np.nan
    table["lambda"] = np.nan
    table["pahl_raw"] = np.nan
    table["n_languages"] = 0
    table["peak_excess"] = np.nan
    table["peak_offset"] = np.nan
    table["censored_frac"] = np.nan
    table["resumption"] = np.nan
    table["time_to_resumption"] = np.nan
    table["pre_mean_fatalities"] = np.nan
    table["resumption_status"] = ""
    return table


def _event_study(panel, event_table: pd.DataFrame, log=print):
    """Aligned excess-attention curves, aggregated across events."""
    curves: List[pd.DataFrame] = []
    fixed_curves: List[pd.DataFrame] = []
    for _, ev in event_table.iterrows():
        arts = [ev["article_en"]] if pd.notna(ev.get("article_en")) else []
        if not arts:
            continue
        curve = metrics.event_excess_curve(
            panel, arts, ev["event_date"], mode="rolling",
            t_min=C.EVENT_STUDY_TMIN, t_max=C.EVENT_STUDY_TMAX,
        )
        if curve is None:
            continue
        curve["event_id"] = ev["event_id"]
        curves.append(curve)
        fixed = metrics.event_excess_curve(
            panel, arts, ev["event_date"], mode="fixed",
            t_min=C.EVENT_STUDY_TMIN, t_max=C.EVENT_STUDY_TMAX,
        )
        if fixed is not None:
            fixed["event_id"] = ev["event_id"]
            fixed_curves.append(fixed)
    if not curves:
        return (
            {"peak_day": None, "half_max_day": None, "response_by_day": [],
             "n_events": 0, "response_by_day_fixed": []},
            {"event_curves": pd.DataFrame(), "event_study_curve": pd.DataFrame(),
             "event_study_curve_fixed": pd.DataFrame()},
        )

    all_curves = pd.concat(curves, ignore_index=True)
    agg = (
        all_curves.groupby("t")["mean_excess"]
        .agg(["mean", "std", "count"])
        .rename(columns={"mean": "mean_excess", "std": "sd", "count": "n_events"})
        .reset_index()
    )
    agg["se"] = agg["sd"] / np.sqrt(agg["n_events"].clip(lower=1))

    smooth = metrics._centred_rolling_median(agg["mean_excess"].to_numpy(dtype=float), 7)
    search = (agg["t"] >= 0) & (agg["t"] <= 90)
    if search.any():
        idx = np.flatnonzero(search)
        peak_i = int(idx[np.nanargmax(np.nan_to_num(smooth[idx], nan=-1e9))])
    else:
        peak_i = 0
    peak_day = int(agg["t"].iloc[peak_i])
    peak_value = float(smooth[peak_i])
    half_max_day: Optional[int] = None
    if np.isfinite(peak_value) and peak_value > 0:
        after = np.flatnonzero(agg["t"] > peak_day)
        for i in after:
            if np.isfinite(smooth[i]) and smooth[i] <= peak_value / 2.0:
                half_max_day = int(agg["t"].iloc[i])
                break

    response_by_day = [
        {
            "t": int(row.t),
            "mean_excess": float(row.mean_excess) if np.isfinite(row.mean_excess) else None,
            "se": float(row.se) if np.isfinite(row.se) else None,
            "n_events": int(row.n_events),
        }
        for row in agg.itertuples()
    ]

    # fixed-baseline response summary (the rolling baseline is the primary)
    fixed_agg = None
    fixed_summary: Dict[str, object] = {"peak_day": None, "half_max_day": None}
    if fixed_curves:
        all_fixed = pd.concat(fixed_curves, ignore_index=True)
        fixed_agg = (
            all_fixed.groupby("t")["mean_excess"].mean().rename("mean_excess").reset_index()
        )
        fsmooth = metrics._centred_rolling_median(
            fixed_agg["mean_excess"].to_numpy(dtype=float), 7
        )
        fsearch = np.flatnonzero((fixed_agg["t"] >= 0) & (fixed_agg["t"] <= 90))
        if fsearch.size:
            fpeak_i = int(fsearch[np.nanargmax(np.nan_to_num(fsmooth[fsearch], nan=-1e9))])
            fixed_summary["peak_day"] = int(fixed_agg["t"].iloc[fpeak_i])
            fpeak = float(fsmooth[fpeak_i])
            if np.isfinite(fpeak) and fpeak > 0:
                for i in np.flatnonzero(fixed_agg["t"] > fixed_summary["peak_day"]):
                    if np.isfinite(fsmooth[i]) and fsmooth[i] <= fpeak / 2.0:
                        fixed_summary["half_max_day"] = int(fixed_agg["t"].iloc[i])
                        break

    # family event-study peaks (for the war vs peace narrative)
    family_study: Dict[str, object] = {}
    for family in ("war", "peace"):
        arts = [a for a in panel.articles_for_family(family) if a in panel.views.columns.get_level_values(1)]
        if not arts:
            continue
        series = _language_series(panel, arts)
        if not series:
            continue
        fam_curves = []
        for _, ev in event_table.iterrows():
            t0 = panel.date_index(ev["event_date"])
            offsets = np.arange(C.EVENT_STUDY_TMIN, C.EVENT_STUDY_TMAX + 1)
            positions = t0 + offsets
            keep = (positions >= 0) & (positions < panel.n_days)
            if not keep.any():
                continue
            for lang, arr in series.items():
                excess = metrics.excess_attention(arr, t0, mode="rolling")
                fam_curves.append(pd.DataFrame({"t": offsets[keep], "excess": excess[positions[keep]]}))
        if not fam_curves:
            continue
        fam_all = pd.concat(fam_curves, ignore_index=True)
        fam_agg = fam_all.groupby("t")["excess"].mean().reset_index()
        fam_search = np.flatnonzero((fam_agg["t"] >= 0) & (fam_agg["t"] <= 90))
        fam_smooth = metrics._centred_rolling_median(fam_agg["excess"].to_numpy(dtype=float), 7)
        if fam_search.size:
            fpi = int(fam_search[np.nanargmax(np.nan_to_num(fam_smooth[fam_search], nan=-1e9))])
            family_study[family] = {
                "peak_day": int(fam_agg["t"].iloc[fpi]),
                "peak_excess": float(fam_smooth[fpi]) if np.isfinite(fam_smooth[fpi]) else None,
            }

    daily_at_peak = float(agg["mean_excess"].iloc[peak_i])
    day0_rows = agg[agg["t"] == 0]
    day0_value = float(day0_rows["mean_excess"].iloc[0]) if len(day0_rows) else None
    event_study = {
        "peak_day": peak_day,
        "half_max_day": half_max_day,
        "peak_mean_excess": peak_value if np.isfinite(peak_value) else None,
        "peak_mean_excess_daily": daily_at_peak if np.isfinite(daily_at_peak) else None,
        "day0_mean_excess": day0_value,
        "peak_statistic": (
            "peak_mean_excess is the maximum of the 7-day centred median of the "
            "daily cross-event mean excess curve (the curve used to locate "
            "peak_day); peak_mean_excess_daily is the unsmoothed daily mean at "
            "that day, and day0_mean_excess is the unsmoothed daily mean at t=0"
        ),
        "response_by_day": response_by_day,
        "n_events": int(all_curves["event_id"].nunique()),
        "n_observations": int(len(all_curves)),
        "baseline": "28-day centred rolling mean with +/-14 day event mask (DESIGN.md)",
        "peak_search_window": "[0, +90] days",
        "response_by_day_fixed": [
            {"t": int(row.t), "mean_excess": float(row.mean_excess) if np.isfinite(row.mean_excess) else None}
            for row in fixed_agg.itertuples()
        ] if fixed_agg is not None else [],
        "fixed_baseline_summary": fixed_summary,
        "by_family": family_study,
    }
    artifacts = {
        "event_curves": all_curves,
        "event_study_curve": agg,
        "event_study_curve_fixed": fixed_agg if fixed_agg is not None else pd.DataFrame(),
    }
    return event_study, artifacts


def _pahl_section(panel, event_table: pd.DataFrame, log=print):
    """Primary PAHL, per-family PAHL, per-language PAHL and mapping sensitivity."""
    # precompute the event-specific theatre series and the two family baskets
    theatre_series: Dict[str, Dict[str, np.ndarray]] = {}
    for _, ev in event_table.iterrows():
        arts = [ev["article_en"]] if pd.notna(ev.get("article_en")) else []
        theatre_series[ev["event_id"]] = _event_series(panel, arts[0] if arts else None)

    family_series: Dict[str, Dict[str, np.ndarray]] = {}
    for family in ("war", "peace"):
        arts = [a for a in panel.articles_for_family(family) if a in panel.views.columns.get_level_values(1)]
        family_series[family] = _language_series(panel, arts) if arts else {}

    primary_rows: List[Dict[str, object]] = []
    per_lang_rows: List[Dict[str, object]] = []
    excluded: List[Dict[str, object]] = []
    mapping_by_id = {
        row["event_id"]: row for _, row in event_table.iterrows()
    }
    for _, ev in event_table.iterrows():
        evd = ev.to_dict()
        series = theatre_series.get(ev["event_id"], {})
        if not series:
            res = {"ok": False, "reason": "unmapped", "n_languages": 0}
        else:
            res = metrics.event_pahl_from_series(
                series,
                panel.date_index(ev["event_date"]),
                window=C.PAHL_PRIMARY_WINDOW,
                min_languages=C.PAHL_MIN_LANGUAGES,
            )
        row = _pahl_row(ev, res, mapping_by_id.get(ev["event_id"]))
        if res.get("ok"):
            primary_rows.append(row)
            event_table.loc[event_table["event_id"] == ev["event_id"], "pahl_ok"] = True
            for key in ("pahl_days", "pahl_raw", "lambda", "n_languages", "peak_excess", "peak_offset", "censored_frac"):
                event_table.loc[event_table["event_id"] == ev["event_id"], key] = row.get(key)
            for fit in res.get("per_language", []):
                per_lang_rows.append(
                    {
                        "event_id": ev["event_id"],
                        "language": fit.get("language"),
                        "pahl_days": fit.get("pahl_days"),
                        "pahl_raw": fit.get("pahl_raw"),
                        "lambda": fit.get("lambda"),
                        "censored": fit.get("censored"),
                        "peak_offset": fit.get("peak_offset"),
                        "peak_excess": fit.get("peak_excess"),
                        "r2": fit.get("r2"),
                        "n_points": fit.get("n_points"),
                    }
                )
        else:
            excluded.append(row)

    values = [r["pahl_days"] for r in primary_rows]
    summary = _summary_block(values)
    censored_fraction = (
        float(np.mean([r["censored_frac"] for r in primary_rows if r["censored_frac"] is not None]))
        if primary_rows else None
    )

    # per-language PAHL across events
    by_language: Dict[str, object] = {}
    if per_lang_rows:
        pl = pd.DataFrame(per_lang_rows)
        for lang, g in pl.groupby("language", sort=True):
            vals = pd.to_numeric(g["pahl_days"], errors="coerce").dropna().tolist()
            if not vals:
                continue
            boot = metrics.bootstrap_median_ci(vals, n_boot=C.PAHL_BOOT, seed=C.SEED)
            by_language[lang] = {
                "median": float(np.median(vals)),
                "iqr_low": float(np.percentile(vals, 25)),
                "iqr_high": float(np.percentile(vals, 75)),
                "bootstrap_ci_low": boot["ci_low"],
                "bootstrap_ci_high": boot["ci_high"],
                "n_fitted": int(len(vals)),
            }

    # per-family PAHL
    by_family: Dict[str, object] = {}
    family_values: Dict[str, Dict[str, float]] = {"war": {}, "peace": {}}
    for family in ("war", "peace"):
        series = family_series.get(family, {})
        rows = []
        for _, ev in event_table.iterrows():
            res = metrics.event_pahl_from_series(
                series, panel.date_index(ev["event_date"]),
                window=C.PAHL_PRIMARY_WINDOW, min_languages=C.PAHL_MIN_LANGUAGES,
            )
            if res.get("ok"):
                rows.append({"event_id": ev["event_id"], "pahl_days": res["pahl_days"],
                             "n_languages": res["n_languages"]})
                family_values[family][ev["event_id"]] = float(res["pahl_days"])
        block = _summary_block([r["pahl_days"] for r in rows])
        block["n_events_fitted"] = int(len(rows))
        block["per_event"] = rows
        by_family[family] = block

    # paired war-vs-peace contrast on events with both fits
    paired = [
        {"event_id": eid,
         "war": family_values["war"][eid],
         "peace": family_values["peace"][eid],
         "difference": family_values["war"][eid] - family_values["peace"][eid]}
        for eid in sorted(set(family_values["war"]) & set(family_values["peace"]))
    ]
    paired_block: Dict[str, object] = {"n": len(paired)}
    if paired:
        diffs = [p["difference"] for p in paired]
        paired_block.update(
            {
                "median_difference": float(np.median(diffs)),
                "bootstrap_ci_low": metrics.bootstrap_median_ci(diffs, n_boot=C.PAHL_BOOT, seed=C.SEED)["ci_low"],
                "bootstrap_ci_high": metrics.bootstrap_median_ci(diffs, n_boot=C.PAHL_BOOT, seed=C.SEED)["ci_high"],
                "median_war": float(np.median([p["war"] for p in paired])),
                "median_peace": float(np.median([p["peace"] for p in paired])),
                "per_event": paired,
            }
        )

    # high-confidence mapping subset
    high_conf = [
        r["pahl_days"] for r in primary_rows
        if r.get("mapping_confidence") in ("high", "medium")
    ]
    mapping_sensitivity = {
        "high_confidence_only": _summary_block(high_conf),
        "n_high_confidence": int(len(high_conf)),
        "n_total_fitted": int(len(primary_rows)),
        "mapping_methods": (
            pd.Series([r.get("mapping_method") for r in primary_rows]).value_counts().to_dict()
            if primary_rows else {}
        ),
    }

    # how many fitted events rely on an article whose coverage starts late
    n_partial_events = 0
    for row in primary_rows:
        art = row.get("article_en")
        partial = False
        for lang in C.LANGS:
            arr = panel.series_views(lang, art) if art else None
            if arr is None:
                continue
            finite = np.isfinite(arr)
            if not finite.any():
                continue
            first = int(np.argmax(finite))
            last = int(len(arr) - 1 - np.argmax(finite[::-1]))
            if first > 0 or last < len(arr) - 1:
                partial = True
                break
        if partial:
            n_partial_events += 1

    pahl = {
        "median": summary["median"],
        "iqr_low": summary["iqr_low"],
        "iqr_high": summary["iqr_high"],
        "bootstrap_ci_low": summary["bootstrap_ci_low"],
        "bootstrap_ci_high": summary["bootstrap_ci_high"],
        "mean": summary["mean"],
        "sd": summary["sd"],
        "min": summary["min"],
        "max": summary["max"],
        "n_fitted": summary["n_fitted"],
        "n_boot": summary["n_boot"],
        "n_events_total": int(len(event_table)),
        "n_events_mapped": int(event_table["article_en"].notna().sum()),
        "censored_fraction": censored_fraction,
        "estimator": "Theil-Sen slope of log excess attention over 90 days after the peak; PAHL = ln2/lambda",
        "window_days": C.PAHL_PRIMARY_WINDOW,
        "min_languages": C.PAHL_MIN_LANGUAGES,
        "primary_excess_baseline": "median log attention over [-90,-30] days before the event",
        "per_event": primary_rows,
        "excluded_events": excluded,
        "by_family": by_family,
        "war_vs_peace": paired_block,
        "by_language": by_language,
        "mapping_sensitivity": mapping_sensitivity,
        "n_partial_coverage_events": int(n_partial_events),
        "median_fit_r2": (
            float(np.median([r["r2"] for r in primary_rows if r.get("r2") is not None]))
            if any(r.get("r2") is not None for r in primary_rows) else None
        ),
    }
    artifacts = {
        "pahl_events": pd.DataFrame(primary_rows),
        "pahl_per_language": pd.DataFrame(per_lang_rows),
        "theatre_series": theatre_series,
        "family_series": family_series,
        "family_values": family_values,
    }
    return pahl, artifacts


def _wpar_section(panel, log=print):
    wpar_df = metrics.compute_wpar(panel)
    block = metrics.wpar_by_language(wpar_df, maxlags=C.WPAR_HAC_LAGS)
    global_block = block["global"]
    slope = global_block["trend_slope_per_year"]
    wpar = {
        "trend_slope_per_year": slope,
        "trend_ci_low": global_block["trend_ci_low"],
        "trend_ci_high": global_block["trend_ci_high"],
        "trend_p": global_block["trend_p"],
        "trend_pct_change_per_year": (math.expm1(slope) * 100.0) if slope is not None else None,
        "highest_language": block["highest_language"],
        "highest_value": block["highest_value"],
        "lowest_language": block["lowest_language"],
        "lowest_value": block["lowest_value"],
        "median_wpar_global": global_block["median_wpar"],
        "n_languages": global_block["n_languages"],
        "n_months": global_block["n_months"],
        "cross_language_iqr_median": global_block["cross_language_iqr_median"],
        "seasonality": global_block["seasonality"],
        "by_language": block["by_language"],
        "global_monthly": global_block.get("monthly", []),
        "dispersion_monthly": global_block.get("dispersion", []),
        "hac_maxlags": C.WPAR_HAC_LAGS,
    }
    artifacts = {"wpar_df": wpar_df}
    return wpar, artifacts


def _resumption_section(inputs, event_table: pd.DataFrame, log=print):
    events = inputs["events"].copy()
    aliases = metrics.iso3_aliases(
        events,
        inputs["ucdp_country"],
        mapping=inputs.get("ucdp_mapping"),
        country_label_to_iso3=UCDP_LABEL_TO_ISO3,
    )
    res_df = metrics.code_resumption(
        events,
        inputs["ucdp_country"],
        threshold=C.RESUMPTION_THRESHOLD,
        pre_months=C.RESUMPTION_PRE_MONTHS,
        sustain=C.RESUMPTION_SUSTAIN,
        horizon=C.RESUMPTION_HORIZON,
        aliases=aliases,
    )
    for _, row in res_df.iterrows():
        mask = event_table["event_id"] == row["event_id"]
        event_table.loc[mask, "resumption"] = row["resumption"]
        event_table.loc[mask, "time_to_resumption"] = row["time_to_resumption"]
        event_table.loc[mask, "pre_mean_fatalities"] = row["pre_mean_fatalities"]
        event_table.loc[mask, "resumption_status"] = row["status"]

    coded = res_df[res_df["status"] == "ok"]
    n_coded = int(len(coded))
    n_resumed = int(coded["resumption"].astype(bool).sum()) if n_coded else 0
    base_rate = float(coded["resumption"].astype(bool).mean()) if n_coded else None
    status_counts = res_df["status"].value_counts().to_dict()
    block = {
        "n_coded": n_coded,
        "n_resumed": n_resumed,
        "base_rate": base_rate,
        "n_no_resumption": int(n_coded - n_resumed),
        "n_excluded": int(len(res_df) - n_coded),
        "status_counts": {str(k): int(v) for k, v in status_counts.items()},
        "threshold": C.RESUMPTION_THRESHOLD,
        "pre_months": C.RESUMPTION_PRE_MONTHS,
        "sustain_months": C.RESUMPTION_SUSTAIN,
        "horizon_months": C.RESUMPTION_HORIZON,
        "iso3_aliases": {k: v for k, v in aliases.items() if k != v},
        "degenerate_premean_events": res_df.loc[res_df["degenerate_premean"].astype(bool), "event_id"].tolist(),
        "time_to_resumption_median": float(coded["time_to_resumption"].median()) if n_coded else None,
        "time_to_resumption_iqr": [
            float(coded["time_to_resumption"].quantile(0.25)),
            float(coded["time_to_resumption"].quantile(0.75)),
        ] if n_coded else None,
        "per_event": res_df.to_dict(orient="records"),
    }
    artifacts = {"resumption_df": res_df}
    return block, artifacts


# ===========================================================================
# Spike (attention response) analysis: the companion to the decay placebo.
# Claim A asks whether attention *rises* on ceasefire dates; claim B asks
# whether its decay *rate* is event-specific.  Both are tested against the
# same random-date null, but with different statistics.
# ===========================================================================
def _smoothed_series_by_language(panel, article: str) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Per-language (7-day centred median log, raw log) for one article."""
    out: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}
    for lang in C.LANGS:
        log_series = panel.language_log_series([article], lang)
        if log_series is None:
            continue
        if int(np.isfinite(log_series).sum()) < 60:
            continue
        smoothed = metrics._centred_rolling_median(log_series, metrics.SMOOTH)
        out[lang] = (smoothed, log_series)
    return out


def _peak_excess_statistic(
    smoothed: np.ndarray,
    log_series: np.ndarray,
    t0_pos: int,
    peak_end: int = metrics.PEAK_END,
) -> Optional[float]:
    """Max smoothed excess over [t0, t0+peak_end] above the pre-event baseline.

    Same baseline definition as the PAHL fit (median log attention over the
    90 days before the event, ending 30 days before it), so the spike and the
    decay statistics decompose the same series into level and rate.
    """
    baseline, _ = metrics.fixed_pre_baseline(log_series, t0_pos)
    if not np.isfinite(baseline):
        return None
    lo = max(0, int(t0_pos))
    hi = min(len(smoothed) - 1, int(t0_pos) + int(peak_end))
    if hi < lo:
        return None
    segment = smoothed[lo:hi + 1]
    if not np.isfinite(segment).any():
        return None
    return float(np.nanmax(segment) - baseline)


def _spike_observed(panel, event_table: pd.DataFrame):
    """Observed peak excess per event, averaged across language editions."""
    cache: Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]] = {}
    rows: List[Dict[str, object]] = []
    for _, ev in event_table.iterrows():
        article = ev.get("article_en")
        if pd.isna(article):
            continue
        if article not in cache:
            cache[article] = _smoothed_series_by_language(panel, article)
        series = cache[article]
        if not series:
            continue
        t0_pos = panel.date_index(ev["event_date"])
        peaks = [
            _peak_excess_statistic(smoothed, log_series, t0_pos)
            for smoothed, log_series in series.values()
        ]
        peaks = [p for p in peaks if p is not None and np.isfinite(p)]
        if not peaks:
            continue
        rows.append(
            {
                "event_id": ev["event_id"],
                "event_date": pd.Timestamp(ev["event_date"]).strftime("%Y-%m-%d"),
                "article_en": article,
                "peak_excess_mean": float(np.mean(peaks)),
                "peak_excess_median": float(np.median(peaks)),
                "n_languages": int(len(peaks)),
            }
        )
    return pd.DataFrame(rows), cache


def _spike_placebo(panel, event_table, spike_df: pd.DataFrame, series_cache, log=print):
    """Random same-year dates pushed through the peak-excess statistic."""
    if spike_df.empty:
        return {"observed_peak": None, "placebo_peak_median": None,
                "placebo_peak_p95": None, "empirical_p": None,
                "n_placebo": 0, "pass": None, "per_event": []}, {}
    rng = np.random.default_rng(C.SEED + 101)
    article_by_event = dict(zip(spike_df["event_id"], spike_df["article_en"]))
    observed_by_event = dict(zip(spike_df["event_id"], spike_df["peak_excess_mean"]))
    min_pos = -C.EVENT_STUDY_TMIN + 5
    max_pos = panel.n_days - metrics.PEAK_END - 2
    null_by_event: Dict[str, List[float]] = {}
    per_event_rows: List[Dict[str, object]] = []
    n_draws = 0
    for event_id, observed in observed_by_event.items():
        series = series_cache.get(article_by_event[event_id], {})
        if not series:
            continue
        ev = event_table[event_table["event_id"] == event_id].iloc[0]
        year = pd.Timestamp(ev["event_date"]).year
        dates = pd.date_range("{}-01-01".format(year), "{}-12-31".format(year), freq="D")
        positions = np.array([panel.date_index(d) for d in dates], dtype=int)
        positions = positions[(positions >= min_pos) & (positions <= max_pos)]
        if positions.size == 0:
            continue
        draws = rng.choice(positions, size=C.PLACEBO_PER_EVENT, replace=positions.size < C.PLACEBO_PER_EVENT)
        nulls: List[float] = []
        for pos in draws:
            n_draws += 1
            peaks = [
                _peak_excess_statistic(smoothed, log_series, int(pos))
                for smoothed, log_series in series.values()
            ]
            peaks = [p for p in peaks if p is not None and np.isfinite(p)]
            if peaks:
                nulls.append(float(np.mean(peaks)))
        if not nulls:
            continue
        null_by_event[event_id] = nulls
        arr = np.asarray(nulls, dtype=float)
        per_event_rows.append(
            {
                "event_id": event_id,
                "observed_peak": float(observed),
                "placebo_peak_median": float(np.median(arr)),
                "placebo_peak_q95": float(np.percentile(arr, 95)),
                "p_upper": float((1 + int(np.sum(arr >= observed))) / (1 + len(arr))),
                "n_placebo": int(len(nulls)),
            }
        )
        log("  spike placebo {:>24s} obs={:6.3f} null_med={:6.3f} p={:.3f}".format(
            str(event_id), float(observed), float(np.median(arr)),
            float((1 + int(np.sum(arr >= observed))) / (1 + len(arr))),
        ))
    pooled = np.asarray([v for vals in null_by_event.values() for v in vals], dtype=float)
    observed_values = np.asarray(list(observed_by_event.values()), dtype=float)
    observed_median = float(np.median(observed_values))
    out: Dict[str, object] = {
        "observed_peak": observed_median,
        "observed_peak_mean": float(np.mean(observed_values)),
        "observed_peak_median": observed_median,
        "placebo_peak_median": None,
        "placebo_peak_mean": None,
        "placebo_peak_p95": None,
        "empirical_p": None,
        "n_placebo": int(pooled.size),
        "n_events": int(len(observed_by_event)),
        "n_placebo_draws": int(n_draws),
        "per_event": per_event_rows,
        "method": (
            "Peak excess = max over [0, +14] days of the 7-day centred-median "
            "log attention minus the pre-event baseline ([-90,-30]), averaged "
            "across language editions. 500 random same-year dates per event are "
            "pushed through the identical statistic; the study-level null draws "
            "one placebo per event and takes the median across events."
        ),
    }
    if pooled.size:
        out["placebo_peak_median"] = float(np.median(pooled))
        out["placebo_peak_mean"] = float(np.mean(pooled))
        out["placebo_peak_p95"] = float(np.percentile(pooled, 95))
        events_with_null = list(null_by_event.keys())
        null_medians = np.empty(C.PLACEBO_STUDIES)
        for i in range(C.PLACEBO_STUDIES):
            picks = [null_by_event[eid][rng.integers(0, len(null_by_event[eid]))] for eid in events_with_null]
            null_medians[i] = float(np.median(picks))
        out["null_median_of_medians"] = float(np.median(null_medians))
        out["empirical_p"] = float((1 + int(np.sum(null_medians >= observed_median))) / (1 + null_medians.size))
        out["pass"] = bool(
            out["empirical_p"] is not None
            and out["empirical_p"] < 0.05
            and observed_median > (out["placebo_peak_median"] or 0)
        )
        pvals = [r["p_upper"] for r in per_event_rows]
        out["n_events_p05"] = int(sum(p <= 0.05 for p in pvals))
        out["per_event_p05_fraction"] = float(np.mean([p <= 0.05 for p in pvals])) if pvals else None
        artifacts = {
            "spike_placebo_pooled": pooled,
            "spike_placebo_null_medians": null_medians,
            "spike_placebo_per_event": pd.DataFrame(per_event_rows),
        }
    else:
        artifacts = {
            "spike_placebo_pooled": np.array([]),
            "spike_placebo_null_medians": np.array([]),
            "spike_placebo_per_event": pd.DataFrame(per_event_rows),
        }
    return out, artifacts


def _spike_vs_pahl(pahl: Dict[str, object], spike_df: pd.DataFrame) -> Dict[str, object]:
    """Rank correlation between the peak (spike) and the decay rate (PAHL)."""
    if spike_df.empty or not pahl.get("per_event"):
        return {"rho": None, "p": None, "n": 0}
    pahl_df = pd.DataFrame(
        [{"event_id": r["event_id"], "pahl_days": r["pahl_days"]} for r in pahl["per_event"]]
    )
    merged = pahl_df.merge(spike_df[["event_id", "peak_excess_mean"]], on="event_id", how="inner")
    if len(merged) < 4:
        return {"rho": None, "p": None, "n": int(len(merged))}
    block = models.bootstrap_spearman(
        merged["peak_excess_mean"], merged["pahl_days"], n_boot=C.PAHL_BOOT, seed=C.SEED
    )
    block["n"] = int(len(merged))
    block["bigger_spikes_decay_faster"] = bool(
        block.get("rho") is not None and block["rho"] < 0 and (block.get("p") or 1) < 0.05
    )
    block["interpretation"] = (
        "negative rho means larger announcement spikes have shorter PAHL "
        "(regression to the mean); interpret alongside the spike placebo"
    )
    return block


def _prediction_sample(event_table: pd.DataFrame) -> pd.DataFrame:
    d = event_table[event_table["pahl_ok"] & event_table["resumption"].notna()].copy()
    d["y"] = d["resumption"].astype(float)
    d["log_pre_fatalities"] = np.log1p(d["pre_mean_fatalities"].astype(float).clip(lower=0))
    if "peak_excess_mean" not in d.columns:
        d["peak_excess_mean"] = np.nan
    return d


def _prediction_section(sample: pd.DataFrame, log=print):
    n = int(len(sample))
    out: Dict[str, object] = {
        "n": n,
        "base_rate": float(sample["y"].mean()) if n else None,
        "auc_in_sample": None,
        "auc_cv": None,
        "auc_cv_sd": None,
        "coef": [],
        "primary_model": "resumption ~ z(PAHL) (univariate; auc_in_sample/auc_cv refer to this model)",
        "model_formula": (
            "primary (univariate): P(resumption=1) = logit^-1(a + b * z(PAHL)); "
            "adjusted: + c * log1p(pre-event 6-month mean monthly fatalities) "
            "+ C(agreement_type) + C(region)"
        ),
        "n_pos": int(sample["y"].sum()) if n else 0,
        "n_neg": int(n - sample["y"].sum()) if n else 0,
        "event_ids": sample["event_id"].tolist(),
        "exploratory": True,
        "underpowered": True,
        "note": (
            "n is small and the models are exploratory; no causal interpretation. "
            "Cross-validated AUC is reported alongside in-sample AUC because the "
            "latter is optimistic."
        ),
    }
    if n < 8 or sample["y"].nunique() < 2:
        out["status"] = "insufficient_variation"
        return out, {}

    # ---- univariate PAHL model (primary) ----
    Xu, yu, work_u = models.design_matrix(sample, numeric=["pahl_days"])
    coef_u = models.coefficient_table(Xu, yu, penalty=0.0)
    coef_u["model"] = "univariate"
    fit_u = models.fit_logistic(Xu.to_numpy(dtype=float), yu.to_numpy(dtype=float), penalty=1e-6)
    probs_u = np.asarray(fit_u["fitted"], dtype=float)
    auc_in = models.auc_score(yu, probs_u)
    auc_ci = models.auc_bootstrap_ci(yu, probs_u, n_boot=C.PAHL_BOOT, seed=C.SEED)
    cv_u = models.cross_val_auc(
        Xu, yu, k=C.CV_FOLDS, repeats=C.CV_REPEATS, penalty=C.RIDGE_PENALTY, seed=C.SEED
    )

    # ---- adjusted model ----
    Xa, ya, work_a = models.design_matrix(
        sample,
        numeric=["pahl_days", "log_pre_fatalities"],
        categorical=["agreement_type", "region"],
    )
    penalty_adj = 2.0 * C.RIDGE_PENALTY
    coef_a = models.coefficient_table(Xa, ya, penalty=penalty_adj)
    coef_a["model"] = "adjusted"
    fit_a = models.fit_logistic(Xa.to_numpy(dtype=float), ya.to_numpy(dtype=float), penalty=penalty_adj)
    probs_a = np.asarray(fit_a["fitted"], dtype=float)
    auc_in_a = models.auc_score(ya, probs_a)
    cv_a = models.cross_val_auc(
        Xa, ya, k=C.CV_FOLDS, repeats=C.CV_REPEATS, penalty=penalty_adj, seed=C.SEED
    )

    # ---- univariate inferential extras ----
    spearman = models.bootstrap_spearman(sample["pahl_days"], sample["y"], n_boot=C.PAHL_BOOT, seed=C.SEED)
    median_split = models.median_split_test(sample["pahl_days"], sample["y"])

    coef_rows = coef_u.to_dict(orient="records") + coef_a.to_dict(orient="records")
    pahl_row = coef_u[coef_u["term"] == "pahl_days"]
    or_block: Dict[str, object] = {"term": "pahl_days (standardised)", "n": n}
    if not pahl_row.empty:
        r = pahl_row.iloc[0]
        or_block.update(
            {
                "odds_ratio": r["odds_ratio"],
                "ci_low": r["ci_low"],
                "ci_high": r["ci_high"],
                "coef": r["coef"],
                "std_err": r["std_err"],
                "p": r["p"],
                "method": r["method"],
            }
        )
    # ---- spike (peak excess) univariate model: does the size of the response
    # predict resumption, independently of the decay rate? ----
    spike_model: Dict[str, object] = {"status": "not_estimated"}
    if "peak_excess_mean" in sample.columns and sample["peak_excess_mean"].notna().sum() >= 8:
        ds = sample.dropna(subset=["peak_excess_mean", "y"]).copy()
        if ds["y"].nunique() == 2:
            Xs, ys, _ = models.design_matrix(ds, numeric=["peak_excess_mean"])
            coef_s = models.coefficient_table(Xs, ys, penalty=0.0)
            coef_s["model"] = "spike_univariate"
            cv_s = models.cross_val_auc(
                Xs, ys, k=C.CV_FOLDS, repeats=C.CV_REPEATS,
                penalty=C.RIDGE_PENALTY, seed=C.SEED,
            )
            fit_s = models.fit_logistic(Xs.to_numpy(dtype=float), ys.to_numpy(dtype=float), penalty=1e-6)
            row_s = coef_s[coef_s["term"] == "peak_excess_mean"]
            spike_model = {
                "term": "peak_excess_mean (standardised)",
                "n": int(len(ds)),
                "n_pos": int(ds["y"].sum()),
                "n_neg": int(len(ds) - ds["y"].sum()),
                "base_rate": float(ds["y"].mean()),
                "auc_in_sample": models.auc_score(ys, np.asarray(fit_s["fitted"], dtype=float)),
                "auc_cv": cv_s["auc_cv"],
                "auc_cv_sd": cv_s["auc_cv_sd"],
                "model_formula": "resumption ~ z(peak excess attention)",
            }
            if not row_s.empty:
                rr = row_s.iloc[0]
                spike_model.update(
                    {
                        "coef": rr["coef"],
                        "std_err": rr["std_err"],
                        "odds_ratio": rr["odds_ratio"],
                        "ci_low": rr["ci_low"],
                        "ci_high": rr["ci_high"],
                        "p": rr["p"],
                        "method": rr["method"],
                    }
                )
            coef_rows = coef_rows + coef_s.to_dict(orient="records")

    out.update(
        {
            "spike_model": spike_model,
            "auc_in_sample": auc_in,
            "auc_in_sample_ci_low": auc_ci["ci_low"],
            "auc_in_sample_ci_high": auc_ci["ci_high"],
            "auc_cv": cv_u["auc_cv"],
            "auc_cv_sd": cv_u["auc_cv_sd"],
            "auc_cv_q05": cv_u.get("auc_cv_q05"),
            "auc_cv_q95": cv_u.get("auc_cv_q95"),
            "cv_folds": cv_u.get("k"),
            "cv_repeats": cv_u.get("repeats"),
            "coef": coef_rows,
            "or_pahl": or_block,
            "univariate_auc_in_sample": auc_in,
            "univariate_auc_cv": cv_u["auc_cv"],
            "adjusted_model": {
                "formula": "resumption ~ z(PAHL) + log1p(pre fatalities) + C(agreement_type) + C(region)",
                "n": int(len(ya)),
                "n_parameters": int(Xa.shape[1]),
                "auc_in_sample": auc_in_a,
                "auc_cv": cv_a["auc_cv"],
                "auc_cv_sd": cv_a["auc_cv_sd"],
                "penalty": penalty_adj,
                "method": "ridge-penalised logistic (exploratory; approximate Wald CIs)",
                "coef": coef_a.to_dict(orient="records"),
            },
            "spearman": spearman,
            "median_split": median_split,
        }
    )
    artifacts = {
        "prediction_sample": sample,
        "prediction_Xu": Xu,
        "prediction_yu": yu,
        "prediction_probs_univariate": probs_u,
        "prediction_probs_adjusted": probs_a,
        "prediction_Xa": Xa,
        "prediction_ya": ya,
        "coef_univariate": coef_u,
        "cv_predictions_univariate": cv_u.get("predictions_last_repeat"),
        "cv_predictions_adjusted": cv_a.get("predictions_last_repeat"),
    }
    return out, artifacts


def _survival_section(sample: pd.DataFrame):
    if len(sample) < 8 or sample["y"].nunique() < 2:
        return {"cox_coef_pahl": None, "coef": None, "ci_low": None, "ci_high": None,
                "p": None, "n": int(len(sample)), "method": "failed", "status": "insufficient_variation"}
    z, _, _ = models.standardize(sample["pahl_days"].to_numpy(dtype=float))
    cox = models.cox_ph(
        sample["time_to_resumption"].to_numpy(dtype=float),
        sample["y"].to_numpy(dtype=float),
        z,
        label="z(PAHL)",
    )
    return {
        "cox_coef_pahl": cox["coef"],
        "coef": cox["coef"],
        "ci_low": cox.get("coef_ci_low"),
        "ci_high": cox.get("coef_ci_high"),
        "p": cox["p"],
        "n": cox["n"],
        "n_events": cox["n_events"],
        "hr": cox.get("hr"),
        "hr_ci_low": cox.get("ci_low"),
        "hr_ci_high": cox.get("ci_high"),
        "method": cox.get("method"),
        "covariate": "z(PAHL)",
        "ci_scale": "log hazard (coefficient scale); hr_ci_* are hazard-ratio CIs",
        "duration_definition": "months from event month to first qualifying resumption run; censored at 12",
        "error": cox.get("error"),
    }


def _placebo_section(panel, event_table: pd.DataFrame, pahl: Dict[str, object], log=print):
    """500 random same-year 'pseudo-ceasefires' per fitted event."""
    rng = np.random.default_rng(C.SEED)
    observed_by_event = {
        r["event_id"]: float(r["pahl_days"]) for r in pahl["per_event"]
    }
    null_by_event: Dict[str, List[float]] = {}
    per_event_rows: List[Dict[str, object]] = []
    total_fits = 0
    min_pos = -C.EVENT_STUDY_TMIN + 5          # enough pre-baseline days
    max_pos = panel.n_days - (metrics.PEAK_END + C.PAHL_PRIMARY_WINDOW + 12)
    for _, ev in event_table.iterrows():
        if ev["event_id"] not in observed_by_event:
            continue
        if pd.isna(ev.get("article_en")):
            continue
        series = _event_series(panel, ev["article_en"])
        if not series:
            continue
        year = pd.Timestamp(ev["event_date"]).year
        dates = pd.date_range("{}-01-01".format(year), "{}-12-31".format(year), freq="D")
        positions = np.array([panel.date_index(d) for d in dates], dtype=int)
        positions = positions[(positions >= min_pos) & (positions <= max_pos)]
        if positions.size == 0:
            continue
        k = C.PLACEBO_PER_EVENT
        draws = rng.choice(positions, size=k, replace=positions.size < k)
        nulls: List[float] = []
        for pos in draws:
            total_fits += 1
            res = metrics.event_pahl_from_series(
                series, int(pos), window=C.PAHL_PRIMARY_WINDOW,
                min_languages=C.PAHL_MIN_LANGUAGES,
            )
            if res.get("ok"):
                nulls.append(float(res["pahl_days"]))
        if not nulls:
            continue
        null_arr = np.asarray(nulls, dtype=float)
        null_by_event[ev["event_id"]] = nulls
        obs = observed_by_event[ev["event_id"]]
        p_upper = (1 + int(np.sum(null_arr >= obs))) / (1 + len(null_arr))
        per_event_rows.append(
            {
                "event_id": ev["event_id"],
                "observed_pahl_days": obs,
                "placebo_median": float(np.median(null_arr)),
                "placebo_q05": float(np.percentile(null_arr, 5)),
                "placebo_q95": float(np.percentile(null_arr, 95)),
                "placebo_p_upper": float(p_upper),
                "n_placebo": int(len(nulls)),
            }
        )
        log("  placebo {:>24s} obs={:7.2f} null_med={:7.2f} p={:.3f}".format(
            str(ev["event_id"]), obs, float(np.median(null_arr)), p_upper))

    pooled = np.asarray([v for vals in null_by_event.values() for v in vals], dtype=float)
    observed_median = float(pahl["median"])
    out: Dict[str, object] = {
        "empirical_p": None,
        "observed_median": observed_median,
        "placebo_median": None,
        "n_placebo": int(pooled.size),
        "n_events": len(null_by_event),
        "n_placebo_draws": int(total_fits),
        "n_placebo_studies": C.PLACEBO_STUDIES,
        "per_event": per_event_rows,
        "method": (
            "For each event, 500 random calendar dates in the same year (within "
            "data bounds) are treated as pseudo-ceasefires and PAHL is estimated "
            "with the identical pipeline; the study-level null draws one placebo "
            "PAHL per event and takes the median across events."
        ),
    }
    if pooled.size:
        out["placebo_median"] = float(np.median(pooled))
        out["placebo_iqr"] = [float(np.percentile(pooled, 25)), float(np.percentile(pooled, 75))]
        out["placebo_q95"] = float(np.percentile(pooled, 95))
        # study-level null distribution of the median (events resampled jointly)
        events_with_null = list(null_by_event.keys())
        null_medians = np.empty(C.PLACEBO_STUDIES)
        for i in range(C.PLACEBO_STUDIES):
            picks = [null_by_event[eid][rng.integers(0, len(null_by_event[eid]))] for eid in events_with_null]
            null_medians[i] = float(np.median(picks))
        null_medians = null_medians[np.isfinite(null_medians)]
        out["null_median_of_medians"] = float(np.median(null_medians)) if null_medians.size else None
        out["null_median_q025"] = float(np.percentile(null_medians, 2.5)) if null_medians.size else None
        out["null_median_q975"] = float(np.percentile(null_medians, 97.5)) if null_medians.size else None
        if null_medians.size:
            out["empirical_p"] = float((1 + int(np.sum(null_medians >= observed_median))) / (1 + null_medians.size))
            centered = null_medians - np.median(null_medians)
            out["empirical_p_two_sided"] = float(
                (1 + int(np.sum(np.abs(centered) >= abs(observed_median - np.median(null_medians)))))
                / (1 + null_medians.size)
            )
        pvals = [r["placebo_p_upper"] for r in per_event_rows]
        out["n_events_p05"] = int(sum(p <= 0.05 for p in pvals))
        out["per_event_p05_fraction"] = float(np.mean([p <= 0.05 for p in pvals])) if pvals else None
        out["pass"] = bool(
            out["empirical_p"] is not None
            and out["empirical_p"] < 0.05
            and observed_median > (out["placebo_median"] or 0)
        )
        artifacts = {
            "placebo_pooled": pooled,
            "placebo_null_medians": null_medians,
            "placebo_per_event": pd.DataFrame(per_event_rows),
            "placebo_by_event": null_by_event,
        }
    else:
        artifacts = {
            "placebo_pooled": np.array([]),
            "placebo_null_medians": np.array([]),
            "placebo_per_event": pd.DataFrame(per_event_rows),
            "placebo_by_event": {},
        }
    return out, artifacts


def _robustness_section(panel, event_table, pahl, family_series, prediction, sample, inputs, log=print):
    """Window, baseline, threshold, LOO, permutation, language and mapping checks."""
    theatre_series = {}
    for _, ev in event_table.iterrows():
        if ev["event_id"] in {r["event_id"] for r in pahl["per_event"]}:
            theatre_series[ev["event_id"]] = _event_series(panel, ev["article_en"])

    # ---- decay-window sensitivity ----
    window_blocks: Dict[str, object] = {}
    primary_vals = {r["event_id"]: r["pahl_days"] for r in pahl["per_event"]}
    for window in C.PAHL_WINDOWS:
        vals, ids = [], []
        for eid, series in theatre_series.items():
            ev = event_table[event_table["event_id"] == eid].iloc[0]
            res = metrics.event_pahl_from_series(
                series, panel.date_index(ev["event_date"]),
                window=window, min_languages=C.PAHL_MIN_LANGUAGES,
            )
            if res.get("ok"):
                vals.append(float(res["pahl_days"]))
                ids.append(eid)
        block = _summary_block(vals, seed=C.SEED + window)
        common = [(primary_vals[eid], v) for eid, v in zip(ids, vals) if eid in primary_vals]
        block["spearman_with_primary"] = (
            float(stats.spearmanr([c[0] for c in common], [c[1] for c in common]).correlation)
            if len(common) >= 4 else None
        )
        block["n_common_with_primary"] = len(common)
        block["window_days"] = int(window)
        window_blocks[str(window)] = block

    # non-parametric crossing estimator
    crossing_vals = []
    for eid, series in theatre_series.items():
        ev = event_table[event_table["event_id"] == eid].iloc[0]
        t0 = panel.date_index(ev["event_date"])
        lang_vals = []
        for lang, arr in series.items():
            res = metrics.crossing_half_life(arr, t0, horizon=180)
            if res.get("ok"):
                lang_vals.append(float(res["pahl_days"]))
        if len(lang_vals) >= C.PAHL_MIN_LANGUAGES:
            crossing_vals.append(float(np.median(lang_vals)))
    crossing_block = _summary_block(crossing_vals, seed=C.SEED + 7)
    crossing_block["method"] = "smoothed excess crosses half its peak; horizon 180 days"
    window_blocks["crossing_method"] = crossing_block

    # ---- baseline sensitivity (rolling baseline for the decay fit) ----
    rolling_vals = []
    for eid, series in theatre_series.items():
        ev = event_table[event_table["event_id"] == eid].iloc[0]
        t0 = panel.date_index(ev["event_date"])
        lang_vals = []
        for lang, arr in series.items():
            excess = metrics.excess_attention(arr, t0, mode="rolling")
            res = metrics.fit_decay_from_excess(excess, t0, window=C.PAHL_PRIMARY_WINDOW)
            if res.get("ok"):
                lang_vals.append(float(res["pahl_days"]))
        if len(lang_vals) >= C.PAHL_MIN_LANGUAGES:
            rolling_vals.append(float(np.median(lang_vals)))
    rolling_block = _summary_block(rolling_vals, seed=C.SEED + 11)
    rolling_block["note"] = (
        "decay fitted on excess over the 28-day centred rolling baseline "
        "(vs the fixed pre-event baseline used for the primary estimate)"
    )

    # ---- English-only ----
    english_vals = []
    for eid, series in theatre_series.items():
        if "en" not in series:
            continue
        ev = event_table[event_table["event_id"] == eid].iloc[0]
        res = metrics.event_pahl_from_series(
            {"en": series["en"]}, panel.date_index(ev["event_date"]),
            window=C.PAHL_PRIMARY_WINDOW, min_languages=1,
        )
        if res.get("ok"):
            english_vals.append(float(res["pahl_days"]))
    english_block = _summary_block(english_vals, seed=C.SEED + 13)
    english_block["n_events_with_english"] = int(len(english_vals))
    # per-event English PAHL for the agreement with the multilingual estimate
    english_by_event = {}
    for eid, series in theatre_series.items():
        if "en" not in series:
            continue
        ev = event_table[event_table["event_id"] == eid].iloc[0]
        res = metrics.event_pahl_from_series(
            {"en": series["en"]}, panel.date_index(ev["event_date"]),
            window=C.PAHL_PRIMARY_WINDOW, min_languages=1,
        )
        if res.get("ok"):
            english_by_event[eid] = float(res["pahl_days"])
    common = [(primary_vals[e], english_by_event[e]) for e in english_by_event if e in primary_vals]
    english_block["spearman_with_all_languages"] = (
        float(stats.spearmanr([c[0] for c in common], [c[1] for c in common]).correlation)
        if len(common) >= 4 else None
    )
    english_block["per_event"] = [
        {"event_id": e, "pahl_days": v} for e, v in english_by_event.items()
    ]

    # ---- multilingual-only subset (single-language fits are weaker) ----
    multilingual_vals = [
        r["pahl_days"] for r in pahl["per_event"]
        if (r.get("n_languages") or 0) >= C.PAHL_MULTILINGUAL_MIN
    ]
    multilingual_block = _summary_block(multilingual_vals, seed=C.SEED + 17)
    multilingual_block["min_languages"] = int(C.PAHL_MULTILINGUAL_MIN)

    # ---- leave-one-out ----
    vals = np.asarray([r["pahl_days"] for r in pahl["per_event"]], dtype=float)
    loo_medians = [float(np.median(np.delete(vals, i))) for i in range(len(vals))]
    loo_median_block = {
        "full_median": float(np.median(vals)),
        "n": int(len(vals)),
        "loo_median_min": float(np.min(loo_medians)),
        "loo_median_max": float(np.max(loo_medians)),
        "loo_median_range": float(np.max(loo_medians) - np.min(loo_medians)),
        "loo_median_sd": float(np.std(loo_medians, ddof=1)) if len(loo_medians) > 1 else None,
        "max_abs_shift": float(np.max(np.abs(np.asarray(loo_medians) - np.median(vals)))),
    }
    loo_auc_block: Dict[str, object] = {"n": int(len(sample))}
    try:
        Xu = models.design_matrix(sample, numeric=["pahl_days"])[0]
        yu = sample["y"].to_numpy(dtype=float)
        loo_pred = models.loo_predictions(Xu, yu, penalty=C.RIDGE_PENALTY)
        refit_aucs = []
        for i in range(len(yu)):
            keep = np.ones(len(yu), dtype=bool)
            keep[i] = False
            if len(np.unique(yu[keep])) < 2:
                continue
            fit = models.fit_logistic(
                Xu.to_numpy(dtype=float)[keep], yu[keep], penalty=C.RIDGE_PENALTY
            )
            probs = np.asarray(fit["fitted"], dtype=float)
            refit_aucs.append(models.auc_score(yu[keep], probs))
        loo_auc_block.update(
            {
                "loo_predictive_auc": loo_pred.get("loo_auc"),
                "n_evaluated": loo_pred.get("n_evaluated"),
                "refit_auc_min": float(np.min(refit_aucs)) if refit_aucs else None,
                "refit_auc_max": float(np.max(refit_aucs)) if refit_aucs else None,
                "refit_auc_median": float(np.median(refit_aucs)) if refit_aucs else None,
                "refit_auc_sd": float(np.std(refit_aucs, ddof=1)) if len(refit_aucs) > 1 else None,
            }
        )
    except Exception as exc:  # noqa: BLE001
        loo_auc_block["error"] = str(exc)[:200]
    leave_one_out = {
        "pahl_median": loo_median_block,
        "logistic_auc": loo_auc_block,
        "note": (
            "PAHL LOO: median recomputed with each event deleted. "
            "AUC LOO: leave-one-event-out predictive AUC plus the distribution of "
            "refitted in-sample AUCs on the remaining events."
        ),
    }

    # ---- permutation tests ----
    perm: Dict[str, object] = {"n_perm": C.N_PERM}
    try:
        Xu = models.design_matrix(sample, numeric=["pahl_days"])[0]
        yu = sample["y"].to_numpy(dtype=float)
        perm_coef = models.permutation_coef_test(
            Xu, yu, n_perm=C.N_PERM, penalty=C.RIDGE_PENALTY, coef_index=1, seed=C.SEED
        )
        perm.update(perm_coef)
        perm.update(
            {
                "statistic": "standardised logistic coefficient of PAHL (ridge penalty)",
                "spearman": models.permutation_pvalue(
                    sample["pahl_days"], sample["y"], n_perm=C.N_PERM, seed=C.SEED
                ),
                "n": int(len(sample)),
            }
        )
    except Exception as exc:  # noqa: BLE001
        perm["error"] = str(exc)[:200]
    perm["p"] = perm.get("p")
    perm["n_perm"] = int(perm.get("n_perm", C.N_PERM))

    # ---- resumption-threshold sensitivity ----
    events = inputs["events"].copy()
    aliases = metrics.iso3_aliases(
        events,
        inputs["ucdp_country"],
        mapping=inputs.get("ucdp_mapping"),
        country_label_to_iso3=UCDP_LABEL_TO_ISO3,
    )
    threshold_blocks: Dict[str, object] = {}
    for threshold in C.THRESHOLD_SENSITIVITY:
        res_df = metrics.code_resumption(
            events, inputs["ucdp_country"], threshold=threshold,
            pre_months=C.RESUMPTION_PRE_MONTHS, sustain=C.RESUMPTION_SUSTAIN,
            horizon=C.RESUMPTION_HORIZON, aliases=aliases,
        )
        coded = res_df[res_df["status"] == "ok"]
        merged = sample[["event_id"]].merge(
            coded[["event_id", "resumption", "time_to_resumption"]], on="event_id", how="inner"
        )
        block: Dict[str, object] = {
            "threshold": float(threshold),
            "n_coded": int(len(coded)),
            "n_with_pahl": int(len(merged)),
            "base_rate": float(coded["resumption"].astype(bool).mean()) if len(coded) else None,
            "base_rate_in_prediction_sample": float(merged["resumption"].astype(bool).mean()) if len(merged) else None,
        }
        if len(merged) >= 8 and merged["resumption"].nunique() == 2:
            d = merged.copy()
            d["y"] = d["resumption"].astype(float)
            d = d.merge(sample[["event_id", "pahl_days"]], on="event_id", how="left")
            Xu, yu, _ = models.design_matrix(d, numeric=["pahl_days"])
            coef = models.coefficient_table(Xu, yu, penalty=0.0)
            row = coef[coef["term"] == "pahl_days"].iloc[0]
            cv = models.cross_val_auc(
                Xu, yu, k=C.CV_FOLDS, repeats=C.CV_REPEATS,
                penalty=C.RIDGE_PENALTY, seed=C.SEED,
            )
            fit = models.fit_logistic(Xu.to_numpy(dtype=float), yu.to_numpy(dtype=float), penalty=1e-6)
            block.update(
                {
                    "odds_ratio": row["odds_ratio"],
                    "ci_low": row["ci_low"],
                    "ci_high": row["ci_high"],
                    "p": row["p"],
                    "auc_in_sample": models.auc_score(yu, np.asarray(fit["fitted"], dtype=float)),
                    "auc_cv": cv["auc_cv"],
                    "auc_cv_sd": cv["auc_cv_sd"],
                    "n_prediction_sample": int(len(d)),
                }
            )
        threshold_blocks[str(threshold)] = block

    robustness = {
        "window_sensitivity": window_blocks,
        "threshold_sensitivity": threshold_blocks,
        "leave_one_out": leave_one_out,
        "permutation": perm,
        "english_only": english_block,
        "multilingual_only": multilingual_block,
        "mapping_sensitivity": pahl["mapping_sensitivity"],
        "baseline_sensitivity": rolling_block,
    }
    artifacts = {"window_values": window_blocks, "english_values": english_vals}
    return robustness, artifacts


def _falsification_section(pahl, placebo, prediction, robustness, event_study, wpar):
    checks: Dict[str, object] = {}
    checks["attention_decay_is_event_specific"] = bool(placebo.get("pass"))
    checks["placebo_empirical_p"] = placebo.get("empirical_p")
    orp = prediction.get("or_pahl") or {}
    checks["pahl_predicts_resumption_permutation"] = (
        robustness.get("permutation", {}).get("p") is not None
        and robustness["permutation"]["p"] < 0.05
    )
    checks["permutation_p"] = robustness.get("permutation", {}).get("p")
    checks["cv_auc_above_chance"] = (
        prediction.get("auc_cv") is not None and prediction["auc_cv"] > 0.5
    )
    wvsp = pahl.get("war_vs_peace") or {}
    direction = None
    med_war = wvsp.get("median_war")
    med_peace = wvsp.get("median_peace")
    if med_war is not None and med_peace is not None:
        if abs(med_war - med_peace) < 1e-9:
            direction = "no_detectable_difference_in_basket_medians"
        elif med_war < med_peace:
            direction = "peace_decays_slower (WAR basket median PAHL < PEACE basket median PAHL)"
        else:
            direction = "peace_decays_faster (WAR basket median PAHL > PEACE basket median PAHL)"
    checks["war_vs_peace_direction"] = direction
    checks["war_vs_peace_paired_median_difference_days"] = wvsp.get("median_difference")
    spike_placebo = placebo.get("spike") or {}
    spike_model = prediction.get("spike_model") or {}
    checks["attention_spike_is_event_specific"] = bool(spike_placebo.get("pass"))
    checks["spike_placebo_empirical_p"] = spike_placebo.get("empirical_p")
    checks["spike_predicts_resumption"] = bool(
        spike_model.get("p") is not None and spike_model["p"] < 0.05
    )
    checks["spike_vs_pahl_rho"] = (pahl.get("spike_vs_pahl") or {}).get("rho")
    checks["spike_vs_pahl_p"] = (pahl.get("spike_vs_pahl") or {}).get("p")
    fdr = robustness.get("fdr") or {}
    perm_name = "permutation_pahl_resumption"
    checks["permutation_significant_raw"] = (
        robustness.get("permutation", {}).get("p") is not None
        and robustness["permutation"]["p"] < 0.05
    )
    checks["permutation_significant_after_fdr"] = (
        (fdr.get("adjusted") or {}).get(perm_name) is not None
        and (fdr.get("adjusted") or {})[perm_name] < 0.05
    )

    verdicts: List[str] = []
    if placebo.get("pass") is False:
        verdicts.append("decay_placebo_fail")
    if spike_placebo.get("pass") is False:
        verdicts.append("spike_placebo_fail")
    if prediction.get("auc_cv") is not None and prediction["auc_cv"] <= 0.5:
        verdicts.append("prediction_at_or_below_chance")
    if robustness.get("permutation", {}).get("p") is not None and robustness["permutation"]["p"] >= 0.05:
        verdicts.append("association_not_significant")

    return {
        "checks": checks,
        "verdicts": verdicts,
        "placebo_pass": bool(placebo.get("pass")),
        "summary": (
            "Two placebo tests are reported. The SPIKE placebo asks whether the "
            "attention response itself is event-specific (claim A); the DECAY "
            "placebo asks whether the post-peak decay rate is event-specific "
            "(claim B). They answer different questions and must be read "
            "separately. A failed decay placebo means PAHL should not be "
            "interpreted as an event-specific decay rate even if the spike is "
            "event-specific. A non-significant permutation test means the "
            "PAHL-resumption association does not survive randomisation and no "
            "predictive claim is supported."
        ),
        "event_study" : {
            "peak_day": event_study.get("peak_day"),
            "half_max_day": event_study.get("half_max_day"),
        },
    }


# ===========================================================================
# Tables
# ===========================================================================
def _build_tables(results, artifacts, panel) -> Dict[str, pd.DataFrame]:
    tables: Dict[str, pd.DataFrame] = {}
    event_table = artifacts["event_table"]
    t1_cols = [
        "event_id", "event_name", "event_date", "country_iso3", "conflict_name",
        "agreement_type", "region", "headline_salience", "article_en",
        "mapping_method", "confidence", "pahl_ok", "pahl_days", "n_languages",
        "peak_excess", "resumption", "time_to_resumption", "pre_mean_fatalities",
        "resumption_status",
    ]
    t1 = event_table[[c for c in t1_cols if c in event_table.columns]].copy()
    if "event_date" in t1.columns:
        t1["event_date"] = pd.to_datetime(t1["event_date"]).dt.strftime("%Y-%m-%d")
    tables["table1_events.csv"] = t1.sort_values("event_date")

    pl = artifacts.get("pahl_per_language", pd.DataFrame())
    tables["table2_pahl_by_event_language.csv"] = pl.sort_values(["event_id", "language"]) if not pl.empty else pl

    rows = []
    def _add(scope, block):
        rows.append(
            {
                "scope": scope,
                "median": block.get("median"),
                "iqr_low": block.get("iqr_low"),
                "iqr_high": block.get("iqr_high"),
                "mean": block.get("mean"),
                "sd": block.get("sd"),
                "min": block.get("min"),
                "max": block.get("max"),
                "n": block.get("n_fitted", block.get("n")),
                "bootstrap_ci_low": block.get("bootstrap_ci_low"),
                "bootstrap_ci_high": block.get("bootstrap_ci_high"),
            }
        )
    _add("all_languages_primary", results["pahl"])
    for family in ("war", "peace"):
        _add("family_" + family, results["pahl"]["by_family"][family])
    for window, block in results["robustness"]["window_sensitivity"].items():
        _add("window_" + window, block)
    _add("english_only", results["robustness"]["english_only"])
    _add("multilingual_only", results["robustness"]["multilingual_only"])
    _add("rolling_baseline", results["robustness"]["baseline_sensitivity"])
    _add("high_confidence_mapping", results["pahl"]["mapping_sensitivity"]["high_confidence_only"])
    tables["table3_pahl_summary.csv"] = pd.DataFrame(rows)

    wpar_rows = []
    for lang, block in results["wpar"]["by_language"].items():
        row = {"language": lang}
        row.update(block)
        wpar_rows.append(row)
    wpar_rows.append(
        {
            "language": "GLOBAL",
            "median_wpar": results["wpar"]["median_wpar_global"],
            "median_wpar_log": None,
            "trend_slope_per_year": results["wpar"]["trend_slope_per_year"],
            "trend_ci_low": results["wpar"]["trend_ci_low"],
            "trend_ci_high": results["wpar"]["trend_ci_high"],
            "trend_p": results["wpar"]["trend_p"],
            "n_months": results["wpar"]["n_months"],
        }
    )
    tables["table4_wpar_by_language.csv"] = pd.DataFrame(wpar_rows)

    tables["table5_prediction_coefficients.csv"] = pd.DataFrame(results["prediction"].get("coef", []))
    tables["table6_resumption_coding.csv"] = artifacts["resumption_df"]

    tables["table7_event_study.csv"] = pd.DataFrame(
        results["event_study"].get("response_by_day", [])
    )

    if "placebo_per_event" in artifacts and not artifacts["placebo_per_event"].empty:
        tables["table8_placebo.csv"] = artifacts["placebo_per_event"]
    if "spike_placebo_per_event" in artifacts and not artifacts["spike_placebo_per_event"].empty:
        tables["table10_spike_placebo.csv"] = artifacts["spike_placebo_per_event"]

    rob_rows = []
    for window, block in results["robustness"]["window_sensitivity"].items():
        rob_rows.append(
            {"check": "decay_window", "variant": str(window), "estimate": block.get("median"),
             "n": block.get("n_fitted"), "ci_low": block.get("bootstrap_ci_low"),
             "ci_high": block.get("bootstrap_ci_high"), "p": None}
        )
    for threshold, block in results["robustness"]["threshold_sensitivity"].items():
        rob_rows.append(
            {"check": "resumption_threshold", "variant": str(threshold),
             "estimate": block.get("odds_ratio"), "n": block.get("n_prediction_sample"),
             "ci_low": block.get("ci_low"), "ci_high": block.get("ci_high"), "p": block.get("p")}
        )
    rob_rows.append(
        {"check": "english_only_pahl", "variant": "en",
         "estimate": results["robustness"]["english_only"].get("median"),
         "n": results["robustness"]["english_only"].get("n_fitted"),
         "ci_low": results["robustness"]["english_only"].get("bootstrap_ci_low"),
         "ci_high": results["robustness"]["english_only"].get("bootstrap_ci_high"), "p": None}
    )
    rob_rows.append(
        {"check": "loo_pahl_median_range", "variant": "min", "estimate":
         results["robustness"]["leave_one_out"]["pahl_median"].get("loo_median_min"), "n": None,
         "ci_low": None, "ci_high": None, "p": None}
    )
    rob_rows.append(
        {"check": "loo_pahl_median_range", "variant": "max", "estimate":
         results["robustness"]["leave_one_out"]["pahl_median"].get("loo_median_max"), "n": None,
         "ci_low": None, "ci_high": None, "p": None}
    )
    rob_rows.append(
        {"check": "permutation_pahl_resumption", "variant": "1000 permutations",
         "estimate": results["robustness"]["permutation"].get("coef_obs"),
         "n": results["robustness"]["permutation"].get("n"),
         "ci_low": results["robustness"]["permutation"].get("null_q025"),
         "ci_high": results["robustness"]["permutation"].get("null_q975"),
         "p": results["robustness"]["permutation"].get("p")}
    )
    tables["table9_robustness.csv"] = pd.DataFrame(rob_rows)
    return tables


# ===========================================================================
# Main
# ===========================================================================
def run_analysis(inputs: Dict[str, pd.DataFrame], log=print) -> Tuple[Dict[str, object], Dict[str, object]]:
    t_start = time.time()
    events = inputs["events"].copy()
    articles = inputs["articles"]

    log("building attention panel ...")
    panel = metrics.build_attention_panel(
        inputs["pageviews"], articles, inputs.get("langlinks"),
        langs=C.LANGS, date_start=C.STUDY_START, date_end=C.STUDY_END,
    )
    log("  panel: {} series, {} days, {} positive observations".format(
        panel.n_series(), panel.n_days, panel.diagnostics["n_obs_positive"]))

    event_table = _mapping_and_events(events, articles, panel)
    n_mapped = int(event_table["article_en"].notna().sum())
    log("  events: {} total, {} mapped to a conflict article".format(len(event_table), n_mapped))

    log("event study ...")
    event_study, es_artifacts = _event_study(panel, event_table, log)

    log("PAHL ...")
    pahl, pahl_artifacts = _pahl_section(panel, event_table, log)
    log("  PAHL fitted for {}/{} events; median={} IQR=[{}, {}]".format(
        pahl["n_fitted"], pahl["n_events_total"], pahl["median"], pahl["iqr_low"], pahl["iqr_high"]))

    log("spike (attention response) ...")
    spike_df, spike_cache = _spike_observed(panel, event_table)
    if not spike_df.empty:
        event_table["peak_excess_mean"] = event_table["event_id"].map(
            dict(zip(spike_df["event_id"], spike_df["peak_excess_mean"]))
        )
        pahl["spike_summary"] = {
            "n_events": int(len(spike_df)),
            "observed_peak_mean": float(spike_df["peak_excess_mean"].mean()),
            "observed_peak_median": float(spike_df["peak_excess_mean"].median()),
            "median_languages_per_event": float(spike_df["n_languages"].median()),
        }
    pahl["spike_vs_pahl"] = _spike_vs_pahl(pahl, spike_df)
    log("  spike observed for {} events; spike vs PAHL rho={}".format(
        len(spike_df), pahl["spike_vs_pahl"].get("rho")))

    log("WPAR ...")
    wpar, wpar_artifacts = _wpar_section(panel, log)
    log("  global WPAR trend per year = {} (p={})".format(wpar["trend_slope_per_year"], wpar["trend_p"]))

    log("resumption coding ...")
    resumption, res_artifacts = _resumption_section(inputs, event_table, log)
    log("  n_coded={} base_rate={}".format(resumption["n_coded"], resumption["base_rate"]))

    sample = _prediction_sample(event_table)
    log("prediction sample n={} base_rate={}".format(len(sample), sample["y"].mean() if len(sample) else None))

    log("prediction models ...")
    prediction, pred_artifacts = _prediction_section(sample, log)
    log("  univariate OR={} CV AUC={}".format(
        prediction.get("or_pahl", {}).get("odds_ratio"), prediction.get("auc_cv")))

    log("survival model ...")
    survival = _survival_section(sample)

    log("robustness checks ...")
    robustness, rob_artifacts = _robustness_section(
        panel, event_table, pahl, pahl_artifacts["family_series"], prediction, sample, inputs, log
    )

    log("placebo test (500 random same-year dates per event) ...")
    placebo, placebo_artifacts = _placebo_section(panel, event_table, pahl, log)
    log("  placebo: observed_median={} placebo_median={} empirical_p={} pass={}".format(
        placebo["observed_median"], placebo["placebo_median"], placebo["empirical_p"], placebo.get("pass")))

    log("spike placebo (peak excess on 500 random same-year dates per event) ...")
    spike_placebo, spike_placebo_artifacts = _spike_placebo(
        panel, event_table, spike_df, spike_cache, log
    )
    placebo["spike"] = spike_placebo
    placebo_artifacts.update(spike_placebo_artifacts)
    log("  spike placebo: observed_peak={} placebo_peak_median={} empirical_p={} pass={}".format(
        spike_placebo.get("observed_peak"), spike_placebo.get("placebo_peak_median"),
        spike_placebo.get("empirical_p"), spike_placebo.get("pass")))

    # multiple-testing bookkeeping across the reported hypothesis tests
    pvals = {
        "permutation_pahl_resumption": robustness["permutation"].get("p"),
        "prediction_or_pahl": (prediction.get("or_pahl") or {}).get("p"),
        "survival_cox_pahl": survival.get("p"),
        "wpar_trend": wpar.get("trend_p"),
        "placebo_two_sided": placebo.get("empirical_p_two_sided"),
        "threshold_010_or": robustness["threshold_sensitivity"].get("0.1", {}).get("p"),
        "threshold_050_or": robustness["threshold_sensitivity"].get("0.5", {}).get("p"),
        "spearman_pahl_resumption": (prediction.get("spearman") or {}).get("p"),
        "spike_predicts_resumption": (prediction.get("spike_model") or {}).get("p"),
        "spike_placebo_onesided": (placebo.get("spike") or {}).get("empirical_p"),
    }
    test_names = [name for name, v in pvals.items() if v is not None]
    available = [pvals[name] for name in test_names]
    fdr = models.bh_fdr(available)
    robustness["fdr"] = {
        "tests": pvals,
        "adjusted": {name: adj for name, adj in zip(test_names, fdr["adjusted"])},
        "n_tests": fdr["n_tests"],
        "n_significant": fdr["n_significant"],
        "alpha": fdr["alpha"],
    }

    falsification = _falsification_section(pahl, placebo, prediction, robustness, event_study, wpar)

    meta = {
        "n_events": int(len(event_table)),
        "n_events_mapped": n_mapped,
        "n_events_with_pahl": int(pahl["n_fitted"]),
        "n_events_with_resumption": int(resumption["n_coded"]),
        "n_events_in_prediction": int(prediction["n"]),
        "n_languages": int(panel.diagnostics["languages"].__len__()),
        "n_articles": int(panel.diagnostics["n_articles"]),
        "date_start": panel.diagnostics["date_start"],
        "date_end": panel.diagnostics["date_end"],
        "n_obs": int(panel.diagnostics["n_obs_positive"]),
        "n_series": int(panel.n_series()),
        "n_series_observed": panel.diagnostics.get("n_series_observed"),
        "n_series_unobserved": panel.diagnostics.get("n_series_unobserved"),
        "n_series_partial": panel.diagnostics.get("n_series_partial_coverage"),
        "n_days": int(panel.n_days),
        "n_obs_missing": panel.diagnostics.get("n_obs_missing"),
        "unmapped_events": [
            str(eid) for eid, art in zip(event_table["event_id"], event_table["article_en"])
            if pd.isna(art)
        ],
        "languages": panel.diagnostics["languages"],
        "analysis_version": ANALYSIS_VERSION,
        "generated_at_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "study_start": C.STUDY_START,
        "study_end": C.STUDY_END,
    }

    results = {
        "meta": meta,
        "pahl": pahl,
        "placebo": placebo,
        "prediction": prediction,
        "survival": survival,
        "wpar": wpar,
        "resumption": resumption,
        "robustness": robustness,
        "event_study": event_study,
        "falsification": falsification,
    }

    artifacts = {
        "panel": panel,
        "event_table": event_table,
        "sample": sample,
        "event_study": event_study,
        **es_artifacts,
        **pahl_artifacts,
        **wpar_artifacts,
        **res_artifacts,
        **pred_artifacts,
        **rob_artifacts,
        **placebo_artifacts,
    }
    tables = _build_tables(results, artifacts, panel)
    artifacts["tables"] = tables

    results = _round_floats(_plain(results), nd=6)
    log("analysis finished in {:.1f}s".format(time.time() - t_start))
    return results, artifacts
