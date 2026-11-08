"""Publication figures for *The Half-Life of Peace*.

Ten figures, saved at 300 dpi as both PNG and PDF.  A single restrained
palette is used throughout (navy ``#12395C`` as the accent, greys as the
secondary series), with no chartjunk: no top/right spines, no background
grid except a faint horizontal rule, direct labelling where it helps.

Every figure function takes the ``results`` dict and the ``artifacts`` dict
returned by :mod:`analysis.pipeline` and never invents a number.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import config_analysis as C
from src import metrics as _metrics

# --- palette ---------------------------------------------------------------
NAVY = "#12395C"
INK = "#1F2933"
GREY = "#8C8C8C"
LIGHT = "#D5DBE1"
PALE = "#EEF1F4"
ACCENT = "#A9542C"
FAILED = "#8C3B3B"
HELD = NAVY


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "grid.color": LIGHT,
            "grid.linewidth": 0.5,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def _save(fig, name: str, outdir: Path) -> Dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for ext in ("png", "pdf"):
        path = outdir / "{}.{}".format(name, ext)
        fig.savefig(path, dpi=300, bbox_inches="tight")
        paths[ext] = str(path)
    plt.close(fig)
    return paths


def _num(x, nd=2):
    return "—" if x is None or (isinstance(x, float) and not math.isfinite(x)) else ("{:." + str(nd) + "f}").format(x)


# ===========================================================================
# Fig 1 — event-study attention response
# ===========================================================================
def fig1_attention_response(results, artifacts, outdir) -> Dict[str, str]:
    df = artifacts.get("event_study_curve")
    if df is None or df.empty:
        return {}
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    t = df["t"].to_numpy(dtype=float)
    daily = df["mean_excess"].to_numpy(dtype=float)
    se = df["se"].to_numpy(dtype=float)
    smoothed = np.asarray(_metrics._centred_rolling_median(daily, 7), dtype=float)
    ax.fill_between(t, daily - 1.96 * se, daily + 1.96 * se, color=LIGHT, lw=0,
                    label="95% CI of daily mean")
    ax.plot(t, daily, color=GREY, lw=0.9, alpha=0.9,
            label="Daily cross-event mean excess")
    ax.plot(t, smoothed, color=NAVY, lw=1.9,
            label="7-day centred median (peak detection series)")
    ax.axhline(0.0, color=GREY, lw=0.7)
    ax.axvline(0.0, color=INK, lw=0.8, ls=(0, (4, 3)))
    peak = results["event_study"].get("peak_day")
    half = results["event_study"].get("half_max_day")
    smoothed_peak = results["event_study"].get("peak_mean_excess")
    daily_peak = results["event_study"].get("peak_mean_excess_daily")
    day0 = results["event_study"].get("day0_mean_excess")
    if peak is not None:
        ax.axvline(peak, color=ACCENT, lw=1.0, ls=(0, (1, 2)))
        y_annot = smoothed_peak if smoothed_peak is not None else float(np.nanmax(smoothed))
        ax.scatter([peak], [y_annot], s=26, color=ACCENT, zorder=5)
        label = "smoothed peak = {:.3f} on day {}".format(y_annot, peak)
        if daily_peak is not None:
            label += "\n(daily mean at peak = {:.3f})".format(daily_peak)
        if day0 is not None:
            label += "; daily mean at t=0 = {:.3f}".format(day0)
        ax.annotate(
            label, xy=(peak, y_annot), xytext=(peak + 20, y_annot * 1.02),
            fontsize=8, color=ACCENT, va="center",
            arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.6),
        )
    if half is not None:
        ax.axvline(half, color=ACCENT, lw=1.0, ls=(0, (1, 2)))
        ax.annotate("half-peak day {}".format(half), xy=(half, 0.02),
                    xytext=(half + 6, 0.02), fontsize=8, color=ACCENT, va="center")
    ax.set_xlabel("Days relative to ceasefire announcement")
    ax.set_ylabel("Excess log attention (mean across events)")
    n_events = results["event_study"].get("n_events")
    ax.set_title("Attention to ceasefire theatres, aligned at announcement (n = {} events)".format(n_events))
    ax.set_xlim(-90, 365)
    ax.legend(loc="upper right")
    return _save(fig, "fig1_attention_response", outdir)


# ===========================================================================
# Fig 2 — PAHL distribution
# ===========================================================================
def fig2_pahl_distribution(results, artifacts, outdir) -> Dict[str, str]:
    ev = artifacts.get("pahl_events")
    if ev is None or ev.empty:
        return {}
    vals = pd.to_numeric(ev["pahl_days"], errors="coerce").dropna().to_numpy(dtype=float)
    if vals.size == 0:
        return {}
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    bins = np.linspace(0, max(vals.max() * 1.08, 10), min(22, max(8, int(np.sqrt(len(vals)) * 3))))
    ax.hist(vals, bins=bins, color=PALE, edgecolor=GREY, lw=0.7, label="Events")
    rng = np.random.default_rng(1)
    y = rng.uniform(0.4, 0.85, size=len(vals)) * ax.get_ylim()[1] * 0.45
    ax.scatter(vals, y, s=16, color=NAVY, alpha=0.75, zorder=3, label="Per event")
    med = results["pahl"]["median"]
    lo, hi = results["pahl"]["iqr_low"], results["pahl"]["iqr_high"]
    ax.axvline(med, color=ACCENT, lw=1.6)
    ax.axvspan(lo, hi, color=ACCENT, alpha=0.10, lw=0)
    ax.annotate(
        "median {:.1f} d\nIQR {:.1f}–{:.1f}".format(med, lo, hi),
        xy=(med, ax.get_ylim()[1] * 0.86),
        xytext=(med + max(vals) * 0.06, ax.get_ylim()[1] * 0.86),
        fontsize=8, color=ACCENT, va="center",
    )
    ax.set_xlabel("Peace Attention Half-Life (days)")
    ax.set_ylabel("Number of events")
    ax.set_title("PAHL per event (median across language editions)")
    ax.legend(loc="upper right")
    return _save(fig, "fig2_pahl_distribution", outdir)


# ===========================================================================
# Fig 3 — PAHL vs resumption
# ===========================================================================
def fig3_pahl_vs_resumption(results, artifacts, outdir) -> Dict[str, str]:
    sample = artifacts.get("sample")
    if sample is None or sample.empty:
        return {}
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    failed = sample[sample["y"] < 0.5]
    held = sample[sample["y"] > 0.5]
    ax.scatter(held["pahl_days"], np.log1p(held["pre_mean_fatalities"]),
               s=34, color=NAVY, edgecolor="white", lw=0.6, label="Held (no resumption)", zorder=3)
    ax.scatter(failed["pahl_days"], np.log1p(failed["pre_mean_fatalities"]),
               s=34, color=FAILED, marker="^", edgecolor="white", lw=0.6, label="Resumed", zorder=3)
    # univariate logistic probability surface (secondary axis)
    probs = artifacts.get("prediction_probs_univariate")
    if probs is not None and len(probs) == len(sample):
        order = np.argsort(sample["pahl_days"].to_numpy(dtype=float))
        ax2 = ax.twinx()
        ax2.plot(sample["pahl_days"].to_numpy(dtype=float)[order],
                 np.asarray(probs, dtype=float)[order],
                 color=GREY, lw=1.2, ls=(0, (3, 2)))
        ax2.set_ylabel("Modelled P(resumption)", color=GREY)
        ax2.tick_params(axis="y", colors=GREY)
        ax2.set_ylim(0, 1)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(True)
        ax2.spines["right"].set_color(GREY)
    ax.set_xlabel("Peace Attention Half-Life (days)")
    ax.set_ylabel("log(1 + pre-event monthly fatalities)")
    n = results["prediction"].get("n")
    orp = results["prediction"].get("or_pahl", {})
    or_txt = _num(orp.get("odds_ratio"), 2) if orp.get("odds_ratio") is not None else "—"
    ci = ""
    if orp.get("ci_low") is not None:
        ci = " (95% CI {:.2f}–{:.2f})".format(orp["ci_low"], orp["ci_high"])
    ax.set_title("PAHL and ceasefire resumption (n = {}; univariate OR {}{})".format(n, or_txt, ci))
    ax.legend(loc="upper left")
    return _save(fig, "fig3_pahl_vs_resumption", outdir)


# ===========================================================================
# Fig 4 — WPAR monthly series
# ===========================================================================
def fig4_wpar_timeseries(results, artifacts, outdir) -> Dict[str, str]:
    wpar_df = artifacts.get("wpar_df")
    if wpar_df is None or wpar_df.empty:
        return {}
    df = wpar_df.copy()
    df["date"] = pd.PeriodIndex(df["month"].astype(str), freq="M").to_timestamp()
    highlight = ["en", "ru", "ar", "fr", "zh", "es"]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for lang in highlight:
        g = df[df["lang"] == lang].sort_values("date")
        if g.empty:
            continue
        ax.plot(g["date"], g["wpar"], color=LIGHT if lang != "en" else GREY,
                lw=0.9 if lang != "en" else 1.1, alpha=0.9)
    global_med = df.groupby("date")["wpar_log"].median().apply(math.exp)
    ax.plot(global_med.index, global_med.to_numpy(), color=NAVY, lw=2.0,
            label="Median across languages")
    # label the last point of each highlighted language
    for lang in highlight:
        g = df[df["lang"] == lang].sort_values("date")
        if g.empty:
            continue
        ax.annotate(lang, xy=(g["date"].iloc[-1], g["wpar"].iloc[-1]),
                    xytext=(4, 0), textcoords="offset points", fontsize=7,
                    color=GREY, va="center")
    slope = results["wpar"].get("trend_slope_per_year")
    p = results["wpar"].get("trend_p")
    pct = results["wpar"].get("trend_pct_change_per_year")
    if slope is not None:
        ax.set_title("War–Peace Attention Ratio, monthly (trend {:+.2f} log/yr, {:+.1f}%/yr, p = {:.3g})".format(
            slope, pct if pct is not None else float("nan"), p if p is not None else float("nan")))
    ax.set_yscale("log")
    ax.set_ylabel("WAR basket views / PEACE basket views (log scale)")
    ax.set_xlabel("Month")
    ax.legend(loc="upper left")
    return _save(fig, "fig4_wpar_timeseries", outdir)


# ===========================================================================
# Fig 5 — event × day excess-attention heatmap
# ===========================================================================
def fig5_event_heatmap(results, artifacts, outdir) -> Dict[str, str]:
    curves = artifacts.get("event_curves")
    ev = artifacts.get("pahl_events")
    if curves is None or curves.empty or ev is None or ev.empty:
        return {}
    order = ev.sort_values("pahl_days")["event_id"].tolist()
    order = [e for e in order if e in set(curves["event_id"])]
    sub = curves[(curves["t"] >= -21) & (curves["t"] <= 180)]
    mat = sub.pivot_table(index="event_id", columns="t", values="mean_excess", aggfunc="mean")
    mat = mat.reindex(order)
    mat = mat.dropna(how="all")
    if mat.empty:
        return {}
    fig, ax = plt.subplots(figsize=(7.4, 0.19 * len(mat) + 1.6))
    vmax = float(np.nanpercentile(np.abs(mat.to_numpy(dtype=float)), 95))
    im = ax.imshow(mat.to_numpy(dtype=float), aspect="auto", cmap="RdBu_r",
                   vmin=-vmax, vmax=vmax, interpolation="nearest")
    ax.set_yticks(np.arange(len(mat)))
    labels = []
    pahl_map = dict(zip(ev["event_id"], ev["pahl_days"]))
    for eid in mat.index:
        val = pahl_map.get(eid)
        labels.append("{}  ({:.0f} d)".format(eid.replace("_", " "), val) if val is not None else eid)
    ax.set_yticklabels(labels, fontsize=7)
    xticks = np.arange(0, mat.shape[1], max(1, mat.shape[1] // 8))
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(int(mat.columns[i])) for i in xticks])
    ax.axvline(np.argmin(np.abs(mat.columns.to_numpy(dtype=int) - 0)), color=INK, lw=0.8, ls=(0, (4, 3)))
    ax.set_xlabel("Days relative to announcement")
    ax.set_title("Excess attention by event (rows ordered by PAHL)")
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Excess log attention", fontsize=8)
    return _save(fig, "fig5_event_heatmap", outdir)


# ===========================================================================
# Fig 6 — PAHL by region
# ===========================================================================
def fig6_regional_pahl(results, artifacts, outdir) -> Dict[str, str]:
    ev = artifacts.get("pahl_events")
    if ev is None or ev.empty:
        return {}
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    regions = ev["region"].astype(str)
    order = list(ev.groupby("region")["pahl_days"].median().sort_values().index)
    data = [ev.loc[regions == r, "pahl_days"].dropna().to_numpy(dtype=float) for r in order]
    positions = np.arange(len(order))
    ax.boxplot(data, positions=positions, widths=0.45, patch_artist=True,
               boxprops=dict(facecolor=PALE, edgecolor=GREY, lw=0.8),
               medianprops=dict(color=NAVY, lw=1.3),
               whiskerprops=dict(color=GREY, lw=0.7),
               capprops=dict(color=GREY, lw=0.7),
               flierprops=dict(marker="", ls="none"))
    rng = np.random.default_rng(2)
    for i, vals in enumerate(data):
        jitter = rng.uniform(-0.13, 0.13, size=len(vals))
        ax.scatter(positions[i] + jitter, vals, s=14, color=NAVY, alpha=0.8, zorder=3)
    ax.set_xticks(positions)
    ax.set_xticklabels(["{} (n={})".format(r, len(np.asarray(d).ravel())) for r, d in zip(order, data)],
                       rotation=0, fontsize=8)
    ax.axhline(results["pahl"]["median"], color=ACCENT, lw=1.0, ls=(0, (2, 2)))
    ax.set_ylabel("PAHL (days)")
    ax.set_title("Peace Attention Half-Life by region")
    return _save(fig, "fig6_regional_pahl", outdir)


# ===========================================================================
# Fig 7 — placebo distribution
# ===========================================================================
def fig7_placebo_distribution(results, artifacts, outdir) -> Dict[str, str]:
    pooled = artifacts.get("placebo_pooled")
    null_medians = artifacts.get("placebo_null_medians")
    if pooled is None or len(pooled) == 0:
        return {}
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.hist(pooled, bins=50, color=LIGHT, edgecolor=GREY, lw=0.4, density=True,
            label="Placebo PAHL ({} fits)".format(len(pooled)))
    if null_medians is not None and len(null_medians) > 0:
        ax.hist(null_medians, bins=30, color=GREY, alpha=0.55, density=True,
                label="Null study medians ({} draws)".format(len(null_medians)))
    obs = results["placebo"].get("observed_median")
    if obs is not None:
        ax.axvline(obs, color=ACCENT, lw=2.0, label="Observed median {:.1f} d".format(obs))
    p = results["placebo"].get("empirical_p")
    if p is not None:
        ax.annotate("empirical p = {:.4f}".format(p), xy=(0.62, 0.86), xycoords="axes fraction",
                    fontsize=9, color=ACCENT)
    ax.set_xlabel("PAHL (days)")
    ax.set_ylabel("Density")
    ax.set_title("Placebo test: PAHL at random same-year dates")
    ax.legend(loc="upper right")
    return _save(fig, "fig7_placebo_distribution", outdir)


# ===========================================================================
# Fig 8 — ROC curves for the prediction model
# ===========================================================================
def fig8_roc_prediction(results, artifacts, outdir) -> Dict[str, str]:
    y = artifacts.get("prediction_yu")
    probs = artifacts.get("prediction_probs_univariate")
    if y is None or probs is None or len(y) < 6:
        return {}
    y = np.asarray(y, dtype=float)
    probs = np.asarray(probs, dtype=float)
    from src import models as _models

    def _roc(y_true, score):
        order = np.argsort(-score)
        y_sorted = y_true[order]
        score_sorted = score[order]
        distinct = np.where(np.diff(score_sorted))[0] + 1
        thresholds = np.r_[0, distinct]
        tpr = [0.0]
        fpr = [0.0]
        n_pos = max(y_true.sum(), 1)
        n_neg = max(len(y_true) - n_pos, 1)
        for idx in thresholds:
            pred = np.zeros(len(y_true))
            pred[:idx] = 1
            tpr.append((pred * y_sorted).sum() / n_pos)
            fpr.append(((1 - y_sorted) * pred).sum() / n_neg)
        return np.asarray(fpr), np.asarray(tpr)

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    fpr, tpr = _roc(y, probs)
    ax.plot(fpr, tpr, color=NAVY, lw=1.8, label="PAHL model (in-sample)")
    cv_probs = artifacts.get("cv_predictions_univariate")
    if cv_probs is not None:
        mask = np.isfinite(np.asarray(cv_probs, dtype=float))
        if mask.sum() == len(y) and len(np.unique(y[mask])) == 2:
            fpr_cv, tpr_cv = _roc(y[mask], np.asarray(cv_probs, dtype=float)[mask])
            ax.plot(fpr_cv, tpr_cv, color=GREY, lw=1.4, ls=(0, (3, 2)),
                    label="PAHL model (out-of-fold)")
    ax.plot([0, 1], [0, 1], color=LIGHT, lw=1.0, ls=(0, (1, 1)))
    auc_in = results["prediction"].get("auc_in_sample")
    auc_cv = results["prediction"].get("auc_cv")
    sd = results["prediction"].get("auc_cv_sd")
    txt = []
    if auc_in is not None:
        txt.append("In-sample AUC = {:.3f}".format(auc_in))
    if auc_cv is not None:
        txt.append("CV AUC = {:.3f}".format(auc_cv) + (" ± {:.3f}".format(sd) if sd is not None else ""))
    txt.append("n = {}".format(results["prediction"].get("n")))
    ax.text(0.52, 0.18, "\n".join(txt), fontsize=8, color=INK)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Resumption prediction")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right")
    return _save(fig, "fig8_roc_prediction", outdir)


# ===========================================================================
# Fig 9 — PAHL by language edition
# ===========================================================================
def fig9_language_pahl(results, artifacts, outdir) -> Dict[str, str]:
    by_lang = results["pahl"].get("by_language", {})
    if not by_lang:
        return {}
    rows = []
    for lang, block in by_lang.items():
        rows.append((lang, block.get("median"), block.get("bootstrap_ci_low"),
                     block.get("bootstrap_ci_high"), block.get("n_fitted")))
    rows = [r for r in rows if r[1] is not None]
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(6.8, max(3.6, 0.28 * len(rows) + 1.4)))
    y = np.arange(len(rows))
    med = np.array([r[1] for r in rows])
    lo = np.array([r[2] if r[2] is not None else r[1] for r in rows])
    hi = np.array([r[3] if r[3] is not None else r[1] for r in rows])
    ax.errorbar(med, y, xerr=[med - lo, hi - med], fmt="o", color=NAVY, ecolor=GREY,
                elinewidth=1.0, capsize=2, ms=4)
    ax.axvline(results["pahl"]["median"], color=ACCENT, lw=1.0, ls=(0, (2, 2)))
    ax.set_yticks(y)
    ax.set_yticklabels(["{:s}  (n={})".format(r[0], r[4]) for r in rows], fontsize=8)
    ax.set_xlabel("PAHL (days), median across events")
    ax.set_title("Attention half-life by language edition (bootstrap 95% CI)")
    return _save(fig, "fig9_language_pahl", outdir)


# ===========================================================================
# Fig 10 — robustness of the PAHL estimate
# ===========================================================================
def fig10_robustness(results, artifacts, outdir) -> Dict[str, str]:
    rob = results["robustness"]
    rows = [
        ("Primary (fixed baseline, 90 d)", results["pahl"].get("median"),
         results["pahl"].get("bootstrap_ci_low"), results["pahl"].get("bootstrap_ci_high")),
    ]
    for label, key in (("30-day decay window", "30"), ("270-day decay window", "270"),
                       ("Crossing estimator", "crossing_method")):
        blk = rob["window_sensitivity"].get(key, {})
        rows.append((label, blk.get("median"), blk.get("bootstrap_ci_low"), blk.get("bootstrap_ci_high")))
    rows.append(("English only", rob["english_only"].get("median"),
                 rob["english_only"].get("bootstrap_ci_low"), rob["english_only"].get("bootstrap_ci_high")))
    rows.append(("Rolling baseline", rob["baseline_sensitivity"].get("median"),
                 rob["baseline_sensitivity"].get("bootstrap_ci_low"),
                 rob["baseline_sensitivity"].get("bootstrap_ci_high")))
    hc = results["pahl"]["mapping_sensitivity"]["high_confidence_only"]
    rows.append(("High-confidence mapping", hc.get("median"),
                 hc.get("bootstrap_ci_low"), hc.get("bootstrap_ci_high")))
    rows = [r for r in rows if r[1] is not None]
    fig, ax = plt.subplots(figsize=(6.8, 0.42 * len(rows) + 1.5))
    y = np.arange(len(rows))
    for i, (label, med, lo, hi) in enumerate(rows):
        lo2 = lo if lo is not None else med
        hi2 = hi if hi is not None else med
        color = NAVY if i == 0 else GREY
        ax.errorbar(med, i, xerr=[[med - lo2], [hi2 - med]], fmt="o", color=color,
                    ecolor=color, elinewidth=1.0, capsize=2, ms=4)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("PAHL median (days)")
    ax.set_title("Robustness of the attention half-life estimate")
    return _save(fig, "fig10_robustness", outdir)


# ===========================================================================
# driver
# ===========================================================================
FIGURE_FUNCTIONS = (
    fig1_attention_response,
    fig2_pahl_distribution,
    fig3_pahl_vs_resumption,
    fig4_wpar_timeseries,
    fig5_event_heatmap,
    fig6_regional_pahl,
    fig7_placebo_distribution,
    fig8_roc_prediction,
    fig9_language_pahl,
    fig10_robustness,
)


def make_all(results, artifacts, outdir: Optional[Path] = None, log=print) -> Dict[str, Dict[str, str]]:
    """Render every figure to PNG + PDF; returns {name: {png, pdf}}."""
    _style()
    outdir = Path(outdir) if outdir is not None else C.FIGURES_DIR
    made: Dict[str, Dict[str, str]] = {}
    for func in FIGURE_FUNCTIONS:
        try:
            paths = func(results, artifacts, outdir)
        except Exception as exc:  # noqa: BLE001 - one broken plot must not kill the run
            log("  figure {} FAILED: {}".format(func.__name__, exc))
            continue
        if not paths:
            log("  figure {} skipped (missing data)".format(func.__name__))
            continue
        made[func.__name__] = paths
        log("  wrote {} (.png + .pdf)".format(Path(paths["png"]).name))
    return made
