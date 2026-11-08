#!/usr/bin/env python3
"""Self-tests for the measurement and modelling code (no data required).

Run with::

    .venv/bin/python analysis/selftest.py

The tests build small synthetic datasets with known answers and verify the
core functions in :mod:`src.metrics`, :mod:`src.models` and
:mod:`analysis.pipeline`.  They are deliberately dependency-free (plain
asserts, no pytest) and are the guard against silent regressions in the
statistics that produce ``analysis/results.json``.
"""

from __future__ import annotations

import math
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

# make the project importable whether run from the root or the analysis dir
PROJECT_ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(PROJECT_ROOT), str(PROJECT_ROOT / "analysis")):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import config_analysis as C  # noqa: E402
import pipeline  # noqa: E402
from src import metrics, models  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _dates(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="D")


def _synthetic_inputs():
    """Two concept articles + one conflict article created mid-period."""
    dates = _dates("2016-01-01", "2018-12-31")
    created = pd.Timestamp("2017-01-01")
    rows = []
    for date in dates:
        rows.append(("en", "War", "War", date.strftime("%Y-%m-%d"), 100))
        rows.append(("en", "War", "War (moved title)", date.strftime("%Y-%m-%d"), 10))
        rows.append(("en", "Peace", "Peace", date.strftime("%Y-%m-%d"), 50))
        rows.append(("fr", "War", "Guerre", date.strftime("%Y-%m-%d"), 40))
        rows.append(("fr", "Peace", "Paix", date.strftime("%Y-%m-%d"), 20))
    for date in dates:
        if date >= created:
            rows.append(("en", "Test conflict", "Test conflict", date.strftime("%Y-%m-%d"), 30))
            rows.append(("fr", "Test conflict", "Conflit test", date.strftime("%Y-%m-%d"), 10))
    pageviews = pd.DataFrame(rows, columns=["lang", "article_en", "article_local", "date", "views"])
    articles = pd.DataFrame(
        [
            {"article_en": "War", "family": "war", "conflict": None, "country_iso3": None, "region": None},
            {"article_en": "Peace", "family": "peace", "conflict": None, "country_iso3": None, "region": None},
            {"article_en": "Test conflict", "family": "conflict", "conflict": "Test conflict",
             "country_iso3": "TST", "region": "Testland"},
        ]
    )
    langlinks = pd.DataFrame(
        [
            {"article_en": a, "lang": l, "has_langlink": 1}
            for a in ("War", "Peace", "Test conflict")
            for l in ("en", "fr")
        ]
    )
    return pageviews, articles, langlinks


def _synthetic_decay_series(t0_pos: int, pahl_days: float, baseline_views: float = 50.0,
                            amplitude_log: float = 2.0, n: int = 500) -> np.ndarray:
    """Views whose log excess decays exponentially with a known half-life."""
    lam = math.log(2.0) / pahl_days
    t = np.arange(n) - t0_pos
    log_views = np.log1p(baseline_views) + np.where(t >= 0, amplitude_log * np.exp(-lam * np.maximum(t, 0)), 0.0)
    return log_views


def _synthetic_ucdp():
    months = pd.period_range("2014-01", "2025-12", freq="M").astype(str).tolist()
    rows = []
    for m in months:
        rows.append(("TST", m, 0.0, 0))
    # high pre-event violence, then quiet (no resumption)
    for m in months:
        if "2019-01" <= m <= "2019-06":
            rows.append(("TST", m, 100.0, 5))
    # a country that resumes two months after a quiet spell
    for m in months:
        rows.append(("TS2", m, 0.0, 0))
    for m in months:
        if "2019-01" <= m <= "2019-06":
            rows.append(("TS2", m, 100.0, 5))
        if m in ("2019-10", "2019-11", "2019-12"):
            rows.append(("TS2", m, 80.0, 5))
    df = pd.DataFrame(rows, columns=["iso3", "month", "fatalities", "events"])
    return df.groupby(["iso3", "month"], as_index=False)[["fatalities", "events"]].sum()


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def test_title_matching() -> None:
    assert metrics.normalize_title("Côte d’Ivoire – conflict") == "cote divoire conflict"
    assert metrics.title_similarity("India-Pakistan (Kashmir)", "Kashmir conflict") > 0.3
    assert metrics.title_similarity("Israel-Iran war (June 2025)", "Hezbollah–Israel conflict") < 0.5
    articles = pd.DataFrame(
        [
            {"article_en": "Kashmir conflict", "family": "conflict", "conflict": "Kashmir conflict",
             "country_iso3": "IND"},
            {"article_en": "War in Sudan (2023)", "family": "conflict",
             "conflict": "Sudanese civil war", "country_iso3": "SDN"},
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": "k", "conflict_name": "India-Pakistan (Kashmir)", "country_iso3": "PAK"},
            {"event_id": "s", "conflict_name": "Sudan civil war (SAF-RSF)", "country_iso3": "SDN"},
        ]
    )
    mapping = metrics.map_events_to_articles(events, articles).set_index("event_id")
    assert mapping.loc["k", "article_en"] == "Kashmir conflict"
    assert mapping.loc["s", "article_en"] == "War in Sudan (2023)"


def test_panel_existence_and_sums() -> None:
    pageviews, articles, langlinks = _synthetic_inputs()
    panel = metrics.build_attention_panel(
        pageviews, articles, langlinks,
        langs=["en", "fr"], date_start="2016-01-01", date_end="2018-12-31",
    )
    en_war = panel.series_views("en", "War")
    assert abs(en_war[0] - 110.0) < 1e-9, "duplicate titles must be summed"
    created = pd.Timestamp("2017-01-01")
    pos_before = panel.date_index("2016-06-15")
    pos_after = panel.date_index("2017-06-15")
    assert np.isnan(panel.series_views("en", "Test conflict")[pos_before]), \
        "article did not exist before its first pageview and must be missing"
    assert panel.series_views("en", "Test conflict")[pos_after] == 30.0
    assert panel.series_log("en", "Test conflict")[pos_before] is None or np.isnan(
        panel.series_log("en", "Test conflict")[pos_before]
    )
    assert panel.date_index(created) == (created - panel.dates[0]).days


def test_rolling_helpers() -> None:
    x = np.arange(20, dtype=float)
    mean = metrics._centred_rolling_mean(x, 5, min_periods=3)
    assert abs(mean[10] - 10.0) < 1e-9
    median = metrics._centred_rolling_median(x, 5)
    assert abs(median[10] - 10.0) < 1e-9
    with_nan = x.copy()
    with_nan[8] = np.nan
    base, pre = metrics.rolling_baseline(with_nan, t0_pos=10)
    assert np.isfinite(base).all()


def test_theil_sen() -> None:
    x = np.arange(50, dtype=float)
    y = 3.0 - 0.25 * x + np.random.default_rng(0).normal(0, 1e-6, len(x))
    slope, intercept = metrics.theil_sen_slope(x, y)
    assert abs(slope + 0.25) < 1e-3
    assert abs(intercept - 3.0) < 1e-2


def test_pahl_recovery() -> None:
    t0 = 200
    pahl_true = 25.0
    log_views = _synthetic_decay_series(t0, pahl_true)
    fit = metrics.fit_pahl_series(log_views, t0, window=90)
    assert fit["ok"], fit
    assert abs(fit["pahl_raw"] - pahl_true) / pahl_true < 0.10, fit["pahl_raw"]
    assert abs(fit["lambda"] - math.log(2) / pahl_true) < 0.01
    # windowed version must agree
    fit_w = metrics.fit_pahl_windowed(log_views, t0, window=90)
    assert abs(fit_w["pahl_raw"] - fit["pahl_raw"]) < 1e-9


def test_pahl_rejects_flat_and_growing() -> None:
    flat = np.full(500, math.log1p(50.0))
    assert metrics.fit_pahl_series(flat, 200)["ok"] is False
    growing = np.log1p(np.linspace(10, 500, 500))
    assert metrics.fit_pahl_series(growing, 200)["ok"] is False


def test_crossing_estimator() -> None:
    t0 = 200
    log_views = _synthetic_decay_series(t0, 20.0, amplitude_log=2.0)
    fit = metrics.crossing_half_life(log_views, t0, horizon=180)
    assert fit["ok"]
    assert 5.0 < fit["pahl_days"] < 60.0


def test_summaries_and_bootstrap() -> None:
    vals = list(np.linspace(1, 100, 25))
    summary = metrics.pahl_summary(vals, n_boot=300, seed=0)
    assert summary["iqr_low"] <= summary["median"] <= summary["iqr_high"]
    assert summary["bootstrap_ci_low"] <= summary["median"] <= summary["bootstrap_ci_high"]
    assert summary["n_fitted"] == 25
    empty = metrics.pahl_summary([], n_boot=10)
    assert empty["median"] is None and empty["n_fitted"] == 0


def test_wpar_and_trend() -> None:
    pageviews, articles, langlinks = _synthetic_inputs()
    panel = metrics.build_attention_panel(
        pageviews, articles, langlinks, langs=["en", "fr"],
        date_start="2016-01-01", date_end="2018-12-31",
    )
    wpar = metrics.compute_wpar(panel)
    assert not wpar.empty
    en_rows = wpar[wpar["lang"] == "en"]
    # War (110 incl. moved title) / Peace (50) = 2.2
    assert abs(en_rows["wpar"].median() - 2.2) < 0.05
    years = np.linspace(2016, 2018, len(en_rows))
    trend = metrics.ols_hac_trend(en_rows["wpar_log"].to_numpy(), years)
    assert trend["slope_per_year"] is not None
    assert trend["ci_low"] <= trend["slope_per_year"] <= trend["ci_high"]
    block = metrics.wpar_by_language(wpar)
    assert block["highest_language"] in ("en", "fr")
    assert block["by_language"]["en"]["n_months"] >= 30


def test_resumption_coding() -> None:
    ucdp = _synthetic_ucdp()
    events = pd.DataFrame(
        [
            {"event_id": "quiet", "event_date": "2019-07-15", "country_iso3": "TST"},
            {"event_id": "resumes", "event_date": "2019-07-15", "country_iso3": "TS2"},
            {"event_id": "late", "event_date": "2025-08-01", "country_iso3": "TST"},
        ]
    )
    coded = metrics.code_resumption(events, ucdp).set_index("event_id")
    assert coded.loc["quiet", "resumption"] is False or coded.loc["quiet", "resumption"] == False
    assert coded.loc["resumes", "resumption"] is True or coded.loc["resumes", "resumption"] == True
    assert coded.loc["resumes", "time_to_resumption"] == 3
    assert coded.loc["late", "status"] == "insufficient_followup"
    assert coded.loc["late", "resumption"] is None or pd.isna(coded.loc["late", "resumption"])


def test_auc_and_logistic() -> None:
    assert models.auc_score([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
    assert models.auc_score([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]) == 0.0
    assert models.auc_score([0, 0, 1, 1], [1, 1, 1, 1]) == 0.5
    rng = np.random.default_rng(0)
    x = rng.normal(size=60)
    y = (x + rng.normal(scale=0.5, size=60) > 0).astype(int)
    if len(np.unique(y)) < 2:
        return
    fit = models.fit_logistic(np.column_stack([np.ones(60), x]), y)
    assert fit["converged"]
    assert fit["beta"][1] > 0
    X = pd.DataFrame({"x": x})
    cv = models.cross_val_auc(X, pd.Series(y), k=5, repeats=10, penalty=1.0, seed=0)
    assert cv["auc_cv"] is None or (0.0 <= cv["auc_cv"] <= 1.0)
    if cv["auc_cv"] is not None:
        assert cv["auc_cv"] > 0.7
    loo = models.loo_predictions(X, pd.Series(y), penalty=1.0)
    assert loo["loo_auc"] is None or 0.0 <= loo["loo_auc"] <= 1.0
    perm = models.permutation_coef_test(X, pd.Series(y), n_perm=200, penalty=1.0, seed=0)
    assert 0.0 <= perm["p"] <= 1.0
    assert perm["coef_obs"] > 0


def test_bh_fdr() -> None:
    block = models.bh_fdr([0.01, 0.02, 0.5, 0.9])
    assert block["n_tests"] == 4
    assert all(0.0 <= a <= 1.0 for a in block["adjusted"])
    assert block["n_significant"] >= 2


def test_cox() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=40)
    durations = np.clip(8.0 - 2.0 * x + rng.normal(scale=0.5, size=40), 1.0, 12.0)
    observed = rng.random(40) < 0.8
    cox = models.cox_ph(durations, observed.astype(int), x)
    assert cox["method"] in ("cox-phreg", "failed")
    if cox["method"] == "cox-phreg":
        assert cox["coef"] is not None and math.isfinite(cox["coef"])
        assert cox["hr"] > 0


def test_plain_json() -> None:
    obj = {"a": np.float64(np.nan), "b": np.int64(3), "c": np.array([1.0, np.inf])}
    plain = pipeline._plain(obj)
    assert plain["a"] is None and plain["b"] == 3
    assert plain["c"][0] == 1.0 and plain["c"][1] is None
    import json
    json.dumps(plain, allow_nan=False)


def test_design_matrix() -> None:
    df = pd.DataFrame(
        {
            "y": [0, 1, 0, 1, 1, 0, 1, 0],
            "x": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
            "g": ["a", "a", "b", "b", "a", "b", "a", "b"],
        }
    )
    X, y, clean = models.design_matrix(df, numeric=["x"], categorical=["g"])
    assert "const" in X.columns and "g_b" in X.columns
    assert len(X) == len(y) == len(clean)


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
TESTS = [
    test_title_matching,
    test_panel_existence_and_sums,
    test_rolling_helpers,
    test_theil_sen,
    test_pahl_recovery,
    test_pahl_rejects_flat_and_growing,
    test_crossing_estimator,
    test_summaries_and_bootstrap,
    test_wpar_and_trend,
    test_resumption_coding,
    test_auc_and_logistic,
    test_bh_fdr,
    test_cox,
    test_plain_json,
    test_design_matrix,
]


def main() -> int:
    failures = 0
    for test in TESTS:
        try:
            test()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print("FAIL  {}: {}".format(test.__name__, exc))
            traceback.print_exc()
        else:
            print("ok    {}".format(test.__name__))
    print("\n{} tests, {} failures".format(len(TESTS), failures))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
