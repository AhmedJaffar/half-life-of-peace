"""Metric definitions for *The Half-Life of Peace*.

This module is the measurement layer of the analysis.  It contains no
hard-coded results: every function takes data and returns numbers.

Definitions
-----------
**Excess attention.**  For article ``a``, language edition ``l`` and day ``t``

    E(a,l,t) = log(1 + views(a,l,t)) - B(a,l,t)

Two baselines are provided and used deliberately for different purposes:

* ``rolling`` -- a 28-day centred rolling mean of the log series in which the
  +/-14 days surrounding the event are masked out (DESIGN.md).  Used for the
  event-study response curves, where a local baseline is wanted.
* ``fixed``  -- the median log attention over the pre-event window
  (``[-90, -30]`` days).  Used for the PAHL decay fit, because the object being
  estimated is the return of attention *to its pre-event level*; a rolling
  baseline would itself move down with the decay and bias ``lambda`` towards
  zero.

**PAHL (Peace Attention Half-Life).**  For one series around one event: smooth
the log series with a centred 7-day median, find the post-announcement peak in
``[t0, t0 + 14]``, then on the decay window ``[peak + 1, peak + W]`` fit

    E_t = A * exp(-lambda * (t - peak_pos))

on the days with ``E_t > floor`` by robust log-linear regression.  The primary
estimator is the Theil-Sen slope of ``log E_t`` on days-since-peak (median of
pairwise slopes; breakdown point ~29%); a Huber IRLS fit is returned as a
sensitivity.  ``PAHL = ln(2) / lambda`` days.  Fits with ``lambda <= 0`` are
invalid; fits with ``PAHL > W`` are right-censored at ``W`` (the half-life is
not resolved inside the observed decay window) and flagged.

**WPAR (War-Peace Attention Ratio).**  Monthly, per language edition:

    WPAR(l,m) = sum_{a in WAR} views(a,l,m) / sum_{a in PEACE} views(a,l,m)

The unit of analysis is the raw monthly view sum of each concept basket, as
specified in the analysis plan.

**Resumption.**  A ceasefire resumes after the event if, within the 12 months
beginning with the event month, monthly fatalities in the theatre country
exceed ``threshold`` (default 25%) of the mean of the 6 pre-event months for at
least 2 consecutive months.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from . import config

# ---------------------------------------------------------------------------
# default analysis constants (overridable by callers / analysis config)
# ---------------------------------------------------------------------------
LANGS: List[str] = list(config.LANGS)
STUDY_START = "2015-07-01"
STUDY_END = "2025-11-01"

PRE_START = int(config.PRE_BASELINE_START)      # -90
PRE_END = int(config.PRE_BASELINE_END)          # -30
PEAK_END = int(config.PEAK_WINDOW_END)          # +14
SMOOTH = int(config.SMOOTH_WINDOW)              # 7-day centred median
ROLLING_WINDOW = 28
EVENT_HALFWIDTH = 14
T_MIN = -90
T_MAX = 365

PRIMARY_DECAY_WINDOW = 90
DECAY_WINDOWS = (30, 90, 270)
MIN_AMPLITUDE_LOG = 0.10       # peak must exceed baseline by >= 0.10 log units
MIN_FLOOR_FRAC = 0.05          # only days with excess > 5% of peak enter the fit
MIN_FIT_POINTS = 10
MIN_PEAK_VIEWS = 5.0
MIN_BASELINE_VIEWS = 1.0

RESUMPTION_THRESHOLD = 0.25
RESUMPTION_PRE_MONTHS = 6
RESUMPTION_SUSTAIN = 2
RESUMPTION_HORIZON = 12


# ===========================================================================
# 1. Title matching: map a ceasefire event to the conflict article that
#    covers its theatre.  The event table's conflict_name and the article
#    table's conflict label come from different curators, so matching is
#    deliberately fuzzy but auditable: every mapping records its method and
#    score, and the analysis reports a high-confidence-only sensitivity.
# ===========================================================================
_GENERIC_TOKENS = {
    "conflict", "conflicts", "war", "wars", "civil", "the", "of", "in", "and",
    "a", "an", "to", "for", "on", "at", "with", "between", "present", "ongoing",
    "crisis", "insurgency", "rebellion", "dispute",
}


def normalize_title(text: object) -> str:
    """Lower-case, accent-free, punctuation-collapsed title form."""
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return ""
    s = unicodedata.normalize("NFKD", str(text))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.replace("\u2013", "-").replace("\u2014", "-").replace("/", " ")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_tokens(text: object) -> set:
    """Content tokens of a title (generic conflict words and years removed)."""
    toks = set()
    for tok in normalize_title(text).split():
        if tok in _GENERIC_TOKENS:
            continue
        if re.fullmatch(r"(19|20)\d{2}", tok):
            continue
        if len(tok) <= 2:
            continue
        toks.add(tok)
    return toks


def title_similarity(a: object, b: object) -> float:
    """Similarity in [0, 1] combining token Jaccard and string proximity.

    Token overlap carries most weight because curators word titles
    differently; sequence similarity breaks ties between titles that share
    the same proper nouns (e.g. two Sudan conflicts).
    """
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = title_tokens(a), title_tokens(b)
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    from difflib import SequenceMatcher
    seq = SequenceMatcher(None, na, nb).ratio()
    return float(0.75 * jaccard + 0.25 * seq)


# Minimum score for a name-based mapping, and for a country-unique fallback.
NAME_MAP_MIN_SCORE = 0.34
COUNTRY_FALLBACK_MIN_SCORE = 0.20


def map_events_to_articles(
    events: pd.DataFrame,
    articles: pd.DataFrame,
    article_names: Optional[Iterable[str]] = None,
    *,
    require_observed: bool = True,
) -> pd.DataFrame:
    """Map each ceasefire event to one conflict article covering its theatre.

    Strategy, in order:

    1. exact normalised match between ``event.conflict_name`` and
       ``article.conflict`` (score 1.0);
    2. fuzzy name match above ``NAME_MAP_MIN_SCORE``;
    3. if the event's country has exactly one conflict article, use it
       (method ``country_unique``, lower confidence);
    4. otherwise leave the event unmapped (``article_en`` is ``None``).

    ``article_names`` optionally restricts candidates to articles actually
    present in the pageview panel (useful when a conflict article failed to
    resolve).

    Returns one row per event with ``event_id``, ``article_en``,
    ``mapping_method``, ``mapping_score``, ``confidence`` and ``n_candidates``.
    """
    cand = articles.copy()
    cand = cand[cand["family"].astype(str) == "conflict"].copy()
    if article_names is not None:
        observed = set(article_names)
        cand = cand[cand["article_en"].isin(observed)]
    if cand.empty:
        return pd.DataFrame(
            {
                "event_id": events["event_id"].tolist(),
                "article_en": [None] * len(events),
                "mapping_method": ["unmapped"] * len(events),
                "mapping_score": [0.0] * len(events),
                "confidence": ["none"] * len(events),
                "n_candidates": [0] * len(events),
            }
        )

    cand = cand.drop_duplicates("article_en").reset_index(drop=True)
    cand_norm = [normalize_title(c) for c in cand["article_en"]]
    cand_conflict_norm = [normalize_title(c) for c in cand["conflict"]]
    country_index: Dict[str, List[int]] = {}
    for i, iso in enumerate(cand.get("country_iso3", pd.Series([None] * len(cand)))):
        key = str(iso) if pd.notna(iso) else ""
        country_index.setdefault(key, []).append(i)

    rows = []
    for _, ev in events.iterrows():
        conflict = ev.get("conflict_name", "")
        iso = ev.get("country_iso3", None)
        best_score = -1.0
        best_i: Optional[int] = None
        exact = False
        norm_conflict = normalize_title(conflict)
        for i in range(len(cand)):
            if norm_conflict and norm_conflict in (cand_norm[i], cand_conflict_norm[i]):
                best_score, best_i, exact = 1.0, i, True
                break
            score = max(
                title_similarity(conflict, cand["article_en"].iloc[i]),
                title_similarity(conflict, cand["conflict"].iloc[i]),
            )
            if score > best_score:
                best_score, best_i = score, i

        method, confidence = "unmapped", "none"
        article = None
        if best_i is not None and exact:
            article = cand["article_en"].iloc[best_i]
            method, confidence = "exact_name", "high"
            best_score = 1.0
        elif best_i is not None and best_score >= NAME_MAP_MIN_SCORE:
            article = cand["article_en"].iloc[best_i]
            method = "fuzzy_name"
            confidence = "high" if best_score >= 0.55 else "medium"
            if best_score <= COUNTRY_FALLBACK_MIN_SCORE + 1e-12:
                confidence = "low"
        else:
            iso_key = str(iso) if pd.notna(iso) else ""
            idxs = country_index.get(iso_key, [])
            if len(idxs) == 1 and best_score < NAME_MAP_MIN_SCORE:
                i = idxs[0]
                article = cand["article_en"].iloc[i]
                method, confidence = "country_unique", "low"
            elif len(idxs) >= 1:
                # multiple articles share the theatre country: take the best
                # name score among them rather than guessing
                def _local_score(j: int) -> float:
                    return max(
                        title_similarity(conflict, cand["article_en"].iloc[j]),
                        title_similarity(conflict, cand["conflict"].iloc[j]),
                    )

                local_best = max(_local_score(j) for j in idxs)
                if local_best > 0:
                    i = max(idxs, key=_local_score)
                    article = cand["article_en"].iloc[i]
                    best_score = float(local_best)
                    method, confidence = "country_multi_best", "low"

        n_cand = len(country_index.get(str(iso) if pd.notna(iso) else "", []))
        rows.append(
            {
                "event_id": ev["event_id"],
                "article_en": article,
                "mapping_method": method,
                "mapping_score": float(max(best_score, 0.0)),
                "confidence": confidence,
                "n_candidates": int(n_cand),
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# 2. Panel construction
# ===========================================================================
class AttentionPanel:
    """Daily attention panel, wide by (language, article) and daily by row.

    ``views`` and ``log_views`` are DataFrames indexed by date with a
    MultiIndex ``(lang, article_en)``.  Missing calendar days inside a series
    that existed are filled with 0 (see :func:`build_attention_panel`).
    """

    def __init__(
        self,
        views: pd.DataFrame,
        dates: pd.DatetimeIndex,
        meta: pd.DataFrame,
        diagnostics: Optional[Dict[str, object]] = None,
    ) -> None:
        self.views = views
        self.log_views = np.log1p(views.astype(float))
        self.dates = dates
        self.meta = meta
        self.diagnostics = diagnostics or {}
        self._langs_by_article: Dict[str, List[str]] = {}
        for lang, art in views.columns:
            self._langs_by_article.setdefault(str(art), []).append(str(lang))

    # -- basic accessors ----------------------------------------------------
    def date_index(self, date: object) -> int:
        """Position of ``date`` in the daily index (nearest day)."""
        ts = pd.Timestamp(date).normalize()
        return int(np.searchsorted(self.dates.values, ts.to_datetime64()))

    def series_log(self, lang: str, article_en: str) -> Optional[np.ndarray]:
        key = (str(lang), str(article_en))
        if key not in self.log_views.columns:
            return None
        return self.log_views[key].to_numpy(dtype=float)

    def series_views(self, lang: str, article_en: str) -> Optional[np.ndarray]:
        key = (str(lang), str(article_en))
        if key not in self.views.columns:
            return None
        return self.views[key].to_numpy(dtype=float)

    def languages_for(self, article_en: str) -> List[str]:
        langs = sorted(self._langs_by_article.get(str(article_en), []))
        order = {lang: i for i, lang in enumerate(LANGS)}
        return sorted(langs, key=lambda x: order.get(x, 999))

    def language_log_series(
        self, article_ens: Sequence[str], lang: str
    ) -> Optional[np.ndarray]:
        """log1p of the summed views of ``article_ens`` in one language.

        The sum is over raw views (the constructed series warning in the data
        dictionary: several titles may feed one article after page moves) and
        the log is taken afterwards.
        """
        total: Optional[np.ndarray] = None
        for art in article_ens:
            arr = self.series_views(lang, art)
            if arr is None:
                continue
            total = arr.copy() if total is None else total + arr
        if total is None:
            return None
        return np.log1p(total)

    def articles_for_family(self, family: str) -> List[str]:
        return sorted(
            self.meta.index[self.meta["family"].astype(str) == str(family)].tolist()
        )

    def family_monthly(self, family: str) -> pd.DataFrame:
        """Monthly total views per language for one concept family."""
        arts = [a for a in self.articles_for_family(family) if a in self.views.columns.get_level_values(1)]
        if not arts:
            raise ValueError("no articles for family {!r}".format(family))
        sub = self.views.loc[:, (slice(None), arts)]
        # sum across articles, keep language level
        per_lang = sub.T.groupby(level=0).sum().T
        per_lang.index = pd.DatetimeIndex(per_lang.index)
        monthly = per_lang.resample("MS").sum(min_count=1)
        monthly.index = monthly.index.strftime("%Y-%m")
        return monthly

    def n_series(self) -> int:
        return int(self.views.shape[1])

    @property
    def n_days(self) -> int:
        return int(len(self.dates))


def build_attention_panel(
    pageviews: pd.DataFrame,
    articles: pd.DataFrame,
    langlinks: Optional[pd.DataFrame] = None,
    *,
    langs: Sequence[str] = LANGS,
    date_start: str = STUDY_START,
    date_end: str = STUDY_END,
) -> AttentionPanel:
    """Build the daily attention panel from raw pageviews + article metadata.

    Parameters
    ----------
    pageviews
        Long table with ``lang, article_en, date, views`` (extra columns are
        ignored).  Duplicate ``(lang, article_en, date)`` rows are summed --
        this is the documented treatment of article moves, where several
        local titles contribute to one constructed series.
    articles
        Article metadata with ``article_en, family, conflict, country_iso3,
        region``.  For any article present in the pageviews but absent from
        the metadata a row with ``family='other'`` is added.
    langlinks
        Optional ``article_en, lang, has_langlink`` table used as the
        existence proxy: a series that has a langlink but no observed
        pageviews is retained as an all-zero series, so a failed fetch cannot
        masquerade as a non-existent article.  Without it, existence is taken
        from observed pageviews.
    """
    required = {"lang", "article_en", "date", "views"}
    missing = required - set(pageviews.columns)
    if missing:
        raise ValueError("pageviews missing columns: {}".format(sorted(missing)))

    pv = pageviews[["lang", "article_en", "date", "views"]].copy()
    pv["lang"] = pv["lang"].astype(str)
    pv["article_en"] = pv["article_en"].astype(str)
    pv["date"] = pd.to_datetime(pv["date"], errors="coerce").dt.normalize()
    pv["views"] = pd.to_numeric(pv["views"], errors="coerce")
    n_bad_rows = int(pv["date"].isna().sum() + pv["views"].isna().sum())
    pv = pv.dropna(subset=["date", "views"])
    n_negative = int((pv["views"] < 0).sum())
    pv = pv[pv["views"] >= 0]
    pv = pv[pv["lang"].isin(set(langs))]
    pv = (
        pv.groupby(["lang", "article_en", "date"], as_index=False)["views"].sum()
    )

    dates = pd.date_range(pd.Timestamp(date_start), pd.Timestamp(date_end), freq="D")
    dates = pd.DatetimeIndex(dates)

    # -- metadata -----------------------------------------------------------
    meta_cols = ["article_en", "family", "conflict", "country_iso3", "region"]
    meta = articles.copy()
    for col in meta_cols:
        if col not in meta.columns:
            meta[col] = None
    meta = meta[meta_cols].drop_duplicates("article_en").set_index("article_en")
    for art in sorted(set(pv["article_en"]) - set(meta.index)):
        meta.loc[art] = {"family": "other", "conflict": None, "country_iso3": None, "region": None}
    meta = meta.sort_index()

    # -- existence keys -----------------------------------------------------
    observed_keys = set(map(tuple, pv[["lang", "article_en"]].drop_duplicates().to_numpy()))
    existence_keys = set(observed_keys)
    n_zero_only = 0
    if langlinks is not None and not langlinks.empty:
        ll = langlinks.copy()
        ll["lang"] = ll["lang"].astype(str)
        ll["article_en"] = ll["article_en"].astype(str)
        if "has_langlink" in ll.columns:
            ll = ll[pd.to_numeric(ll["has_langlink"], errors="coerce").fillna(0).astype(int) == 1]
        ll = ll[ll["lang"].isin(set(langs))]
        linked = set(map(tuple, ll[["lang", "article_en"]].drop_duplicates().to_numpy()))
        n_zero_only = len(linked - observed_keys)
        existence_keys |= linked

    # restrict to articles we know about (observed always kept)
    existence_keys = {(lg, art) for (lg, art) in existence_keys if art in meta.index}

    # -- pivot to wide ------------------------------------------------------
    wide = pv.pivot(index="date", columns=["lang", "article_en"], values="views")
    wide = wide.reindex(dates).fillna(0.0)
    # add linked-but-unobserved series as zeros
    existing_cols = set(wide.columns)
    add_cols = []
    for key in sorted(existence_keys - existing_cols):
        add_cols.append(key)
    if add_cols:
        block = pd.DataFrame(0.0, index=dates, columns=pd.MultiIndex.from_tuples(add_cols))
        wide = pd.concat([wide, block], axis=1)
    wide = wide.sort_index(axis=1)
    wide.columns = pd.MultiIndex.from_tuples(
        [(str(l), str(a)) for (l, a) in wide.columns], names=["lang", "article_en"]
    )
    wide = wide.astype(float)

    n_obs_positive = int((wide.to_numpy() > 0).sum())
    n_series = int(wide.shape[1])
    diagnostics = {
        "n_series": n_series,
        "n_days": int(len(dates)),
        "n_obs_positive": n_obs_positive,
        "n_series_zero_only": int(n_zero_only),
        "n_articles_expected_from_langlinks": int(len(existence_keys)),
        "n_bad_rows_dropped": n_bad_rows,
        "n_negative_rows_dropped": n_negative,
        "date_start": str(dates[0].date()),
        "date_end": str(dates[-1].date()),
        "languages": sorted(set(l for l, _ in wide.columns)),
        "n_articles": int(len(set(a for _, a in wide.columns))),
    }
    return AttentionPanel(views=wide, dates=dates, meta=meta, diagnostics=diagnostics)


# ===========================================================================
# 3. Rolling / baselines and excess attention
# ===========================================================================
def _centred_rolling_mean(x: np.ndarray, window: int, min_periods: int) -> np.ndarray:
    """Centred rolling nan-mean over ``window`` days, nan if too few finite."""
    from numpy.lib.stride_tricks import sliding_window_view

    x = np.asarray(x, dtype=float)
    n = len(x)
    left = (window - 1) // 2
    right = window - 1 - left
    pad = np.full(left, np.nan)
    suffix = np.full(right, np.nan)
    xp = np.concatenate([pad, x, suffix])
    view = sliding_window_view(xp, window)
    finite = np.isfinite(view)
    counts = finite.sum(axis=1)
    sums = np.where(finite, view, 0.0).sum(axis=1)
    out = np.full(n, np.nan)
    ok = counts >= min_periods
    out[ok] = sums[ok] / counts[ok]
    return out


def _centred_rolling_median(x: np.ndarray, window: int) -> np.ndarray:
    """Centred rolling median that tolerates edge padding."""
    from numpy.lib.stride_tricks import sliding_window_view

    x = np.asarray(x, dtype=float)
    n = len(x)
    left = (window - 1) // 2
    right = window - 1 - left
    xp = np.concatenate([np.full(left, np.nan), x, np.full(right, np.nan)])
    view = sliding_window_view(xp, window)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            out = np.nanmedian(view, axis=1)
    return out


def fixed_pre_baseline(
    log_views: np.ndarray,
    t0_pos: int,
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    min_days: int = 15,
) -> Tuple[float, int]:
    """Median log attention in the pre-event window, plus days used.

    Returns ``(nan, n_days)`` when too few days predate the event (e.g. an
    event a few weeks after the pageview series begins).
    """
    start = max(0, t0_pos + pre_start)
    end = max(start, t0_pos + pre_end)
    seg = log_views[start:end]
    seg = seg[np.isfinite(seg)]
    if len(seg) < min_days:
        return float("nan"), int(len(seg))
    return float(np.median(seg)), int(len(seg))


def rolling_baseline(
    log_views: np.ndarray,
    t0_pos: int,
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    window: int = ROLLING_WINDOW,
    event_halfwidth: int = EVENT_HALFWIDTH,
    min_periods: int = 10,
) -> Tuple[np.ndarray, float]:
    """The DESIGN.md baseline: 28-day centred rolling mean, event masked.

    The +/- ``event_halfwidth`` days around the event are set to nan before the
    rolling mean, so the announcement spike cannot contaminate its own
    baseline.  Inside the masked window the pre-event median is used instead.
    Returns ``(baseline, pre_baseline)``.
    """
    x = np.asarray(log_views, dtype=float).copy()
    n = len(x)
    pre_value, _ = fixed_pre_baseline(x, t0_pos, pre_start, pre_end)
    lo = max(0, t0_pos - event_halfwidth)
    hi = min(n, t0_pos + event_halfwidth + 1)
    masked = x.copy()
    masked[lo:hi] = np.nan
    base = _centred_rolling_mean(masked, window, min_periods)
    # fill the masked window from the pre-event baseline
    if np.isfinite(pre_value):
        base[lo:hi] = pre_value
    else:
        base[lo:hi] = np.nan
    # fill residual nan at the array edges by nearest finite value
    finite = np.isfinite(base)
    if finite.any():
        idx = np.arange(n)
        base[~finite] = np.interp(
            idx[~finite], idx[finite], base[finite]
        )
    return base, pre_value


def excess_attention(
    log_views: np.ndarray,
    t0_pos: int,
    *,
    mode: str = "fixed",
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    window: int = ROLLING_WINDOW,
    event_halfwidth: int = EVENT_HALFWIDTH,
) -> np.ndarray:
    """log attention minus baseline (``mode`` = ``'fixed'`` or ``'rolling'``)."""
    if mode == "fixed":
        base_value, _ = fixed_pre_baseline(log_views, t0_pos, pre_start, pre_end)
        return np.asarray(log_views, float) - base_value
    if mode == "rolling":
        base, _ = rolling_baseline(
            log_views, t0_pos, pre_start, pre_end, window, event_halfwidth
        )
        return np.asarray(log_views, float) - base
    raise ValueError("mode must be 'fixed' or 'rolling'")


# ===========================================================================
# 4. PAHL
# ===========================================================================
def theil_sen_slope(x: Sequence[float], y: Sequence[float]) -> Tuple[float, float]:
    """Theil-Sen slope and intercept: median of all pairwise slopes.

    Implemented directly (numpy) because the placebo exercise calls it tens of
    thousands of times.  For very long series the pair set is deterministically
    subsampled to keep the cost bounded; the analysis never hits that branch
    (fits have <= 91 points).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 2:
        return float("nan"), float("nan")
    if n > 300:
        rng = np.random.default_rng(0)
        take = np.sort(rng.choice(n, 300, replace=False))
        x, y = x[take], y[take]
        n = 300
    dx = x[None, :] - x[:, None]
    dy = y[None, :] - y[:, None]
    iu = np.triu_indices(n, 1)
    slopes = dy[iu] / dx[iu]
    slopes = slopes[np.isfinite(slopes)]
    if slopes.size == 0:
        return float("nan"), float("nan")
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * x))
    return slope, intercept


def huber_slope(
    x: Sequence[float], y: Sequence[float], c: float = 1.345, max_iter: int = 50
) -> Tuple[float, float]:
    """Huber-IRLS slope/intercept, used as a sensitivity to Theil-Sen."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 3:
        return float("nan"), float("nan")
    X = np.column_stack([np.ones_like(x), x])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    for _ in range(max_iter):
        resid = y - X @ beta
        sigma = 1.4826 * np.median(np.abs(resid - np.median(resid)))
        if not np.isfinite(sigma) or sigma <= 0:
            break
        u = resid / (c * sigma)
        w = np.ones_like(u)
        big = np.abs(u) > 1
        w[big] = 1.0 / np.abs(u[big])
        Xw = X * np.sqrt(w)[:, None]
        yw = y * np.sqrt(w)
        beta_new = np.linalg.lstsq(Xw, yw, rcond=None)[0]
        if np.max(np.abs(beta_new - beta)) < 1e-9:
            beta = beta_new
            break
        beta = beta_new
    return float(beta[1]), float(beta[0])


def fit_pahl_series(
    log_views: np.ndarray,
    t0_pos: int,
    *,
    window: int = PRIMARY_DECAY_WINDOW,
    peak_end: int = PEAK_END,
    smooth: int = SMOOTH,
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    min_amplitude: float = MIN_AMPLITUDE_LOG,
    floor_frac: float = MIN_FLOOR_FRAC,
    min_points: int = MIN_FIT_POINTS,
    min_peak_views: float = MIN_PEAK_VIEWS,
    min_baseline_views: float = MIN_BASELINE_VIEWS,
) -> Dict[str, object]:
    """Fit the exponential decay of excess attention for one series.

    Returns a dict with ``ok`` (bool) and, when usable:

    ``pahl_days`` (censored at ``window``), ``pahl_raw`` (uncensored fit),
    ``lambda`` (per day), ``censored``, ``peak_pos`` (index), ``peak_offset``
    (days after t0), ``peak_excess``, ``baseline_log``, ``n_points``,
    ``r2``, ``amplitude_log`` and ``estimator``.

    ``ok`` is False with a ``reason`` for series with no baseline, no
    measurable spike, or no resolvable decay.
    """
    x = np.asarray(log_views, dtype=float)
    n = len(x)
    if n == 0 or not np.isfinite(x).any():
        return {"ok": False, "reason": "empty_series"}

    baseline_log, base_days = fixed_pre_baseline(x, t0_pos, pre_start, pre_end)
    if not np.isfinite(baseline_log):
        return {"ok": False, "reason": "insufficient_pre_baseline", "baseline_days": base_days}
    if math.expm1(baseline_log) < min_baseline_views:
        return {"ok": False, "reason": "baseline_too_small", "baseline_log": baseline_log}

    smoothed = _centred_rolling_median(x, smooth)
    peak_lo = max(0, t0_pos)
    peak_hi = min(n - 1, t0_pos + peak_end)
    if peak_hi <= peak_lo:
        return {"ok": False, "reason": "insufficient_post_event_window"}
    seg = smoothed[peak_lo:peak_hi + 1]
    if not np.isfinite(seg).any():
        return {"ok": False, "reason": "no_post_event_data"}
    rel = int(np.nanargmax(seg))
    peak_pos = peak_lo + rel
    peak_excess = float(smoothed[peak_pos] - baseline_log)
    peak_views = float(math.expm1(x[peak_pos]))

    if not np.isfinite(peak_excess) or peak_excess < min_amplitude:
        return {
            "ok": False,
            "reason": "no_spike",
            "peak_excess": peak_excess,
            "baseline_log": baseline_log,
        }
    if peak_views < min_peak_views:
        return {"ok": False, "reason": "peak_too_small", "peak_views": peak_views}

    fit_lo = peak_pos + 1
    fit_hi = min(n - 1, peak_pos + window)
    if fit_hi <= fit_lo:
        return {"ok": False, "reason": "insufficient_decay_window"}
    t = np.arange(1, fit_hi - fit_lo + 2, dtype=float)  # days after peak
    excess = smoothed[fit_lo:fit_hi + 1] - baseline_log
    floor = max(1e-6, floor_frac * peak_excess)
    good = np.isfinite(excess) & (excess > floor)
    n_points = int(good.sum())
    if n_points < min_points:
        return {
            "ok": False,
            "reason": "insufficient_decay_points",
            "n_points": n_points,
            "peak_excess": peak_excess,
        }

    log_excess = np.log(excess[good])
    slope_ts, intercept_ts = theil_sen_slope(t[good], log_excess)
    slope_hu, _ = huber_slope(t[good], log_excess)
    if not np.isfinite(slope_ts):
        return {"ok": False, "reason": "fit_failed", "n_points": n_points}

    lam = -slope_ts
    lam_huber = -slope_hu
    pahl_raw = float(math.log(2.0) / lam) if lam > 0 else float("inf")
    if not np.isfinite(pahl_raw) or pahl_raw <= 0:
        return {
            "ok": False,
            "reason": "no_decay",
            "lambda": float(lam) if np.isfinite(lam) else None,
            "n_points": n_points,
        }
    censored = bool(pahl_raw > window)
    pahl_days = float(window if censored else pahl_raw)

    # fit quality on the log scale
    pred = intercept_ts + slope_ts * t[good]
    ss_res = float(np.sum((log_excess - pred) ** 2))
    ss_tot = float(np.sum((log_excess - np.mean(log_excess)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {
        "ok": True,
        "pahl_days": pahl_days,
        "pahl_raw": float(pahl_raw),
        "lambda": float(lam),
        "lambda_huber": float(lam_huber) if np.isfinite(lam_huber) else None,
        "pahl_huber": float(math.log(2.0) / lam_huber) if lam_huber > 0 else None,
        "censored": censored,
        "peak_pos": int(peak_pos),
        "peak_offset": int(peak_pos - t0_pos),
        "peak_excess": peak_excess,
        "peak_views": peak_views,
        "baseline_log": float(baseline_log),
        "baseline_views": float(math.expm1(baseline_log)),
        "n_points": n_points,
        "r2": float(r2),
        "estimator": "theil-sen on log excess",
        "window_days": int(window),
        "fit_t": t[good].tolist(),
        "fit_log_excess": log_excess.tolist(),
    }


def crossing_half_life(
    log_views: np.ndarray,
    t0_pos: int,
    *,
    horizon: int = 180,
    peak_end: int = PEAK_END,
    smooth: int = SMOOTH,
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    min_amplitude: float = MIN_AMPLITUDE_LOG,
) -> Dict[str, object]:
    """Non-parametric alternative to the exponential fit.

    PAHL is the number of days after the peak at which the smoothed excess
    first falls to half its peak value; censored at ``horizon``.  Reported as
    a robustness check on the functional form of the decay.
    """
    x = np.asarray(log_views, dtype=float)
    n = len(x)
    baseline_log, _ = fixed_pre_baseline(x, t0_pos, pre_start, pre_end)
    if not np.isfinite(baseline_log):
        return {"ok": False, "reason": "insufficient_pre_baseline"}
    smoothed = _centred_rolling_median(x, smooth)
    peak_lo, peak_hi = max(0, t0_pos), min(n - 1, t0_pos + peak_end)
    if peak_hi <= peak_lo:
        return {"ok": False, "reason": "insufficient_post_event_window"}
    seg = smoothed[peak_lo:peak_hi + 1]
    if not np.isfinite(seg).any():
        return {"ok": False, "reason": "no_post_event_data"}
    peak_pos = peak_lo + int(np.nanargmax(seg))
    peak_excess = float(smoothed[peak_pos] - baseline_log)
    if not np.isfinite(peak_excess) or peak_excess < min_amplitude:
        return {"ok": False, "reason": "no_spike"}
    target = baseline_log + peak_excess / 2.0
    end = min(n - 1, peak_pos + horizon)
    for pos in range(peak_pos + 1, end + 1):
        if smoothed[pos] < target:
            return {
                "ok": True,
                "pahl_days": float(pos - peak_pos),
                "censored": False,
                "peak_pos": int(peak_pos),
                "peak_offset": int(peak_pos - t0_pos),
                "peak_excess": peak_excess,
            }
    return {
        "ok": True,
        "pahl_days": float(horizon),
        "censored": True,
        "peak_pos": int(peak_pos),
        "peak_offset": int(peak_pos - t0_pos),
        "peak_excess": peak_excess,
    }


# ---------------------------------------------------------------------------
# PAHL summaries
# ---------------------------------------------------------------------------
def summarise_values(values: Sequence[float]) -> Dict[str, object]:
    """Median, IQR and related distributional summaries for finite values."""
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    if len(v) == 0:
        return {
            "median": None, "iqr_low": None, "iqr_high": None,
            "mean": None, "sd": None, "min": None, "max": None, "n": 0,
        }
    return {
        "median": float(np.median(v)),
        "iqr_low": float(np.percentile(v, 25)),
        "iqr_high": float(np.percentile(v, 75)),
        "mean": float(np.mean(v)),
        "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None,
        "min": float(np.min(v)),
        "max": float(np.max(v)),
        "n": int(len(v)),
    }


def bootstrap_median_ci(
    values: Sequence[float],
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Percentile bootstrap CI for the median of ``values``.

    The resampling unit is the value itself (for PAHL: the event), i.e. a
    cluster bootstrap over events.  Returns plain floats/ints.
    """
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    out: Dict[str, object] = {
        "median": None, "ci_low": None, "ci_high": None,
        "se": None, "n": int(len(v)), "n_boot": int(n_boot),
    }
    if len(v) == 0:
        return out
    med = float(np.median(v))
    out["median"] = med
    if len(v) == 1:
        out["ci_low"] = out["ci_high"] = med
        return out
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n_boot, len(v)))
    boots = np.median(v[idx], axis=1)
    out["ci_low"] = float(np.percentile(boots, 100 * alpha / 2))
    out["ci_high"] = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    out["se"] = float(np.std(boots, ddof=1))
    return out


def pahl_summary(values: Sequence[float], n_boot: int = 2000, seed: int = 0) -> Dict[str, object]:
    """Distribution summary + cluster-bootstrap CI for a set of PAHL values."""
    s = summarise_values(values)
    b = bootstrap_median_ci(values, n_boot=n_boot, seed=seed)
    s.update(
        {
            "bootstrap_ci_low": b["ci_low"],
            "bootstrap_ci_high": b["ci_high"],
            "bootstrap_se": b["se"],
            "n_fitted": s["n"],
            "n_boot": b["n_boot"],
        }
    )
    return s


def per_language_pahl(
    panel: AttentionPanel,
    article_ens: Sequence[str],
    event_date: object,
    *,
    window: int = PRIMARY_DECAY_WINDOW,
    langs: Optional[Sequence[str]] = None,
    **fit_kwargs,
) -> pd.DataFrame:
    """Fit PAHL for each language edition covering ``article_ens``.

    Returns one row per language with the fit dict flattened plus
    ``language`` and ``ok``.
    """
    t0_pos = panel.date_index(event_date)
    languages = [
        lang for lang in (langs if langs is not None else LANGS)
        if panel.language_log_series(article_ens, lang) is not None
    ]
    rows: List[Dict[str, object]] = []
    for lang in languages:
        log_series = panel.language_log_series(article_ens, lang)
        if log_series is None:
            continue
        fit = fit_pahl_series(log_series, t0_pos, window=window, **fit_kwargs)
        row = {"language": lang, "event_t0_pos": int(t0_pos)}
        row.update({k: v for k, v in fit.items() if k not in ("fit_t", "fit_log_excess")})
        rows.append(row)
    return pd.DataFrame(rows)


def event_pahl(
    panel: AttentionPanel,
    article_ens: Sequence[str],
    event_date: object,
    *,
    window: int = PRIMARY_DECAY_WINDOW,
    min_languages: int = 1,
    langs: Optional[Sequence[str]] = None,
    **fit_kwargs,
) -> Dict[str, object]:
    """Multilingual PAHL for one event: median of the per-language fits.

    Returns a dict with ``ok``, ``pahl_days`` (median across valid language
    fits), ``lambda`` (implied ``ln2 / pahl_days``), ``n_languages`` and the
    per-language estimates.  The event estimate is only marked usable when at
    least ``min_languages`` language editions produced a valid fit.
    """
    per_lang = per_language_pahl(
        panel, article_ens, event_date, window=window, langs=langs, **fit_kwargs
    )
    if per_lang.empty:
        return {"ok": False, "reason": "no_language_series", "n_languages": 0}
    valid = per_lang[per_lang["ok"].astype(bool)] if "ok" in per_lang else per_lang.iloc[0:0]
    values = pd.to_numeric(valid.get("pahl_days"), errors="coerce").to_numpy(dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < max(1, min_languages):
        return {
            "ok": False,
            "reason": "too_few_language_fits",
            "n_languages": int(len(values)),
            "per_language": valid.to_dict(orient="records"),
        }
    median_pahl = float(np.median(values))
    lam = float(math.log(2.0) / median_pahl) if median_pahl > 0 else float("nan")
    return {
        "ok": True,
        "pahl_days": median_pahl,
        "lambda": lam,
        "n_languages": int(len(values)),
        "languages": valid["language"].tolist(),
        "censored_frac": float(np.mean(valid["censored"].astype(bool)))
        if "censored" in valid
        else None,
        "per_language": valid.to_dict(orient="records"),
        "per_language_all": per_lang.to_dict(orient="records"),
    }


# ===========================================================================
# 5. Event study curves
# ===========================================================================
def event_excess_curve(
    panel: AttentionPanel,
    article_ens: Sequence[str],
    event_date: object,
    *,
    mode: str = "rolling",
    t_min: int = T_MIN,
    t_max: int = T_MAX,
    pre_start: int = PRE_START,
    pre_end: int = PRE_END,
    window: int = ROLLING_WINDOW,
    event_halfwidth: int = EVENT_HALFWIDTH,
) -> Optional[pd.DataFrame]:
    """Language-averaged excess attention around one event.

    Computes ``E(l,t)`` for every language edition that carries the article,
    then averages across languages with equal weight (so English does not
    dominate the event curve).  Returns a frame with ``t``,
    ``mean_excess``, ``n_languages`` and the per-language columns, or ``None``
    when no language has the article.
    """
    t0_pos = panel.date_index(event_date)
    languages = [
        lang for lang in LANGS if panel.language_log_series(article_ens, lang) is not None
    ]
    if not languages:
        return None
    offsets = np.arange(t_min, t_max + 1)
    positions = t0_pos + offsets
    keep = (positions >= 0) & (positions < panel.n_days)
    columns: Dict[str, np.ndarray] = {}
    for lang in languages:
        log_series = panel.language_log_series(article_ens, lang)
        if log_series is None:
            continue
        excess = excess_attention(
            log_series, t0_pos, mode=mode, pre_start=pre_start, pre_end=pre_end,
            window=window, event_halfwidth=event_halfwidth,
        )
        columns[lang] = excess[positions[keep]]
    if not columns:
        return None
    frame = pd.DataFrame(columns)
    frame.insert(0, "t", offsets[keep])
    frame["mean_excess"] = frame[languages].mean(axis=1, skipna=True)
    frame["n_languages"] = frame[languages].notna().sum(axis=1)
    return frame


# ===========================================================================
# 6. WPAR
# ===========================================================================
def compute_wpar(panel: AttentionPanel) -> pd.DataFrame:
    """Monthly War-Peace Attention Ratio per language edition.

    ``wpar = war_views / peace_views`` over the raw monthly sums of the two
    concept baskets.  Returns a long frame with ``lang``, ``month``
    (``YYYY-MM``), ``war_views``, ``peace_views``, ``wpar`` and ``wpar_log``.
    """
    war = panel.family_monthly("war")
    peace = panel.family_monthly("peace")
    war = war.reindex(index=peace.index.union(war.index))
    peace = peace.reindex(index=war.index)
    common = [c for c in war.columns if c in peace.columns]
    months = war.index
    rows = []
    for lang in common:
        w = war[lang].to_numpy(dtype=float)
        p = peace[lang].to_numpy(dtype=float)
        for i, month in enumerate(months):
            if not np.isfinite(w[i]) or not np.isfinite(p[i]) or p[i] <= 0:
                continue
            ratio = float(w[i] / p[i])
            rows.append(
                {
                    "lang": lang,
                    "month": month,
                    "war_views": float(w[i]),
                    "peace_views": float(p[i]),
                    "wpar": ratio,
                    "wpar_log": float(math.log(ratio)) if ratio > 0 else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def ols_hac_trend(
    y: Sequence[float],
    x_years: Sequence[float],
    *,
    maxlags: int = 12,
    extra_design: Optional[pd.DataFrame] = None,
) -> Dict[str, object]:
    """OLS trend with Newey-West (HAC) standard errors.

    ``y`` is typically ``log(WPAR)`` and ``x_years`` is time in decimal years,
    so the slope is the change in log WPAR per year.  ``extra_design`` may add
    columns (e.g. month-of-year dummies, or a ``log`` crash indicator); the
    reported slope/CI always refer to the first regressor (time).
    """
    import statsmodels.api as sm

    y = np.asarray(y, dtype=float)
    x = np.asarray(x_years, dtype=float)
    mask = np.isfinite(y) & np.isfinite(x)
    y, x = y[mask], x[mask]
    out: Dict[str, object] = {
        "slope_per_year": None, "ci_low": None, "ci_high": None,
        "p": None, "n": int(len(y)), "r2": None, "method": "HAC-OLS",
    }
    if len(y) < 6 or np.std(x) == 0:
        return out

    design = pd.DataFrame({"year": x})
    if extra_design is not None:
        extra = extra_design.loc[mask].reset_index(drop=True)
        design = pd.concat([design, extra], axis=1)
    X = sm.add_constant(design.astype(float).to_numpy(), has_constant="add")
    try:
        model = sm.OLS(y, X).fit(
            cov_type="HAC", cov_kwds={"maxlags": int(maxlags), "use_correction": True}
        )
    except Exception:  # pragma: no cover
        return out
    slope = float(model.params[1])
    se = float(model.bse[1])
    out.update(
        {
            "slope_per_year": slope,
            "ci_low": slope - 1.959963984540054 * se,
            "ci_high": slope + 1.959963984540054 * se,
            "p": float(model.pvalues[1]),
            "n": int(model.nobs),
            "r2": float(model.rsquared),
            "se": se,
            "maxlags": int(maxlags),
        }
    )
    return out


def wpar_by_language(
    wpar_df: pd.DataFrame,
    *,
    maxlags: int = 12,
) -> Dict[str, object]:
    """Per-language WPAR level and trend, plus the pooled global series."""
    if wpar_df.empty:
        return {"by_language": {}, "global": {}}
    df = wpar_df.copy()
    # decimal year for the trend
    dt = pd.PeriodIndex(df["month"].astype(str), freq="M").to_timestamp()
    df["year"] = dt.year + (dt.month - 0.5) / 12.0

    by_language: Dict[str, object] = {}
    for lang, g in df.groupby("lang", sort=True):
        g = g.sort_values("month")
        trend = ols_hac_trend(g["wpar_log"], g["year"], maxlags=maxlags)
        by_language[lang] = {
            "median_wpar": float(np.exp(np.median(g["wpar_log"]))),
            "median_wpar_log": float(np.median(g["wpar_log"])),
            "trend_slope_per_year": trend["slope_per_year"],
            "trend_ci_low": trend["ci_low"],
            "trend_ci_high": trend["ci_high"],
            "trend_p": trend["p"],
            "n_months": int(len(g)),
            "first_month": str(g["month"].iloc[0]),
            "last_month": str(g["month"].iloc[-1]),
        }

    # global: median across languages per month, then trend of that series
    global_series = (
        df.groupby("month", as_index=False)["wpar_log"].median().sort_values("month")
    )
    gdt = pd.PeriodIndex(global_series["month"].astype(str), freq="M").to_timestamp()
    global_series["year"] = gdt.year + (gdt.month - 0.5) / 12.0
    g_trend = ols_hac_trend(global_series["wpar_log"], global_series["year"], maxlags=maxlags)
    # cross-language dispersion
    disp = df.groupby("month")["wpar_log"].agg(
        iqr=lambda s: float(s.quantile(0.75) - s.quantile(0.25)),
        n="count",
    )

    # month-of-year seasonality on the global series
    months = pd.PeriodIndex(global_series["month"].astype(str), freq="M").month
    seasonal: Dict[str, object] = {}
    try:
        import statsmodels.api as sm
        dummies = pd.get_dummies(pd.Series(months), prefix="m", drop_first=True).astype(float)
        X = sm.add_constant(
            pd.concat(
                [global_series["year"].reset_index(drop=True), dummies.reset_index(drop=True)],
                axis=1,
            ).to_numpy()
        )
        fit = sm.OLS(global_series["wpar_log"].to_numpy(), X).fit(
            cov_type="HAC", cov_kwds={"maxlags": int(maxlags)}
        )
        month_effects = {"m1": 0.0}
        for col in dummies.columns:
            month_effects[col] = float(fit.params[list(dummies.columns).index(col) + 2])
        seasonal = {
            "amplitude_log": float(max(month_effects.values()) - min(month_effects.values())),
            "month_of_year_log": month_effects,
        }
    except Exception:  # pragma: no cover
        seasonal = {}

    highest = max(by_language.items(), key=lambda kv: kv[1]["median_wpar"])
    lowest = min(by_language.items(), key=lambda kv: kv[1]["median_wpar"])
    return {
        "by_language": by_language,
        "global": {
            "median_wpar": float(np.exp(np.median(global_series["wpar_log"]))),
            "trend_slope_per_year": g_trend["slope_per_year"],
            "trend_ci_low": g_trend["ci_low"],
            "trend_ci_high": g_trend["ci_high"],
            "trend_p": g_trend["p"],
            "n_months": int(len(global_series)),
            "cross_language_iqr_median": float(disp["iqr"].median()),
            "n_languages": int(df["lang"].nunique()),
            "seasonality": seasonal,
        },
        "highest_language": highest[0],
        "highest_value": highest[1]["median_wpar"],
        "lowest_language": lowest[0],
        "lowest_value": lowest[1]["median_wpar"],
        "monthly": global_series.to_dict(orient="records"),
        "dispersion": disp.reset_index().to_dict(orient="records"),
    }


# ===========================================================================
# 7. Resumption coding
# ===========================================================================
def _country_month_frame(ucdp_country: pd.DataFrame) -> Tuple[Dict[str, pd.Series], List[str]]:
    """Dense monthly fatality series per ISO3 (UCDP drops zero-event months)."""
    required = {"iso3", "month", "fatalities"}
    missing = required - set(ucdp_country.columns)
    if missing:
        raise ValueError("ucdp_country missing columns: {}".format(sorted(missing)))
    df = ucdp_country.copy()
    df["month"] = df["month"].astype(str)
    df["iso3"] = df["iso3"].astype(str)
    df["fatalities"] = pd.to_numeric(df["fatalities"], errors="coerce").fillna(0.0)
    all_months = pd.period_range(
        pd.Period(df["month"].min(), freq="M"),
        pd.Period(df["month"].max(), freq="M"),
        freq="M",
    ).astype(str).tolist()
    series_by_iso: Dict[str, pd.Series] = {}
    for iso, g in df.groupby("iso3"):
        s = g.groupby("month")["fatalities"].sum()
        series_by_iso[iso] = s.reindex(all_months).fillna(0.0).astype(float)
    return series_by_iso, all_months


def iso3_aliases(
    events: pd.DataFrame,
    ucdp_country: pd.DataFrame,
    mapping: Optional[pd.DataFrame] = None,
    *,
    country_label_to_iso3: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Map theatre ISO3 codes onto the ISO3 codes present in UCDP.

    Identity mapping where possible.  For theatres absent from GED (notably
    ``PSE``: GED codes Gaza/West Bank events under Israel) the explicit
    curator mapping file ``data/processed/ucdp_country_mapping.csv`` is used
    when available, together with the GED country-label -> ISO3 table from
    :mod:`src.ucdp`.  Falls back to the documented ``PSE -> ISR`` proxy.
    """
    present = set(ucdp_country["iso3"].astype(str))
    aliases: Dict[str, str] = {}
    for iso in sorted(set(events["country_iso3"].astype(str))):
        if iso in present:
            aliases[iso] = iso
            continue
        aliases[iso] = "ISR" if iso == "PSE" else iso
    if mapping is not None and not mapping.empty:
        label_to_iso = dict(country_label_to_iso3 or {})
        for _, row in mapping.iterrows():
            theatre = str(row.get("theatre_iso3", "")).strip()
            label = str(row.get("ucdp_country", "")).strip()
            if not theatre or theatre in present:
                continue
            target = label_to_iso.get(label)
            if target is None:
                target = "ISR" if theatre == "PSE" else None
            if target in present:
                aliases[theatre] = str(target)
    return aliases


def code_resumption(
    events: pd.DataFrame,
    ucdp_country: pd.DataFrame,
    *,
    threshold: float = RESUMPTION_THRESHOLD,
    pre_months: int = RESUMPTION_PRE_MONTHS,
    sustain: int = RESUMPTION_SUSTAIN,
    horizon: int = RESUMPTION_HORIZON,
    aliases: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Code ceasefire resumption from monthly UCDP fatalities.

    For each event with theatre ``iso3`` (after aliasing):

    * pre-window = the ``pre_months`` calendar months immediately before the
      event month; ``pre_mean`` = mean monthly fatalities;
    * resumption threshold = ``threshold * pre_mean`` (if ``pre_mean`` is 0
      any fatality is above threshold; such events are flagged
      ``degenerate_premean``);
    * the event resumes if in the 12 months beginning with the event month at
      least ``sustain`` consecutive months exceed the threshold;
    * ``time_to_resumption`` is the 0-based month index (0 = event month) of
      the first month of that run, or ``horizon`` if censored.

    Events whose follow-up or pre-window is not fully covered by the UCDP
    sample are marked ``resumption=None`` with a ``status`` explaining why
    (they cannot enter the prediction models).
    """
    series_by_iso, all_months = _country_month_frame(ucdp_country)
    aliases = aliases or {}
    rows = []
    for _, ev in events.iterrows():
        iso = str(ev.get("country_iso3"))
        target_iso = aliases.get(iso, iso)
        event_date = pd.Timestamp(ev.get("event_date"))
        event_month = pd.Period(event_date, freq="M")
        out = {
            "event_id": ev.get("event_id"),
            "country_iso3": iso,
            "ucdp_iso3": target_iso,
            "event_date": event_date.strftime("%Y-%m-%d"),
            "event_month": str(event_month),
            "threshold": float(threshold),
            "resumption": None,
            "time_to_resumption": None,
            "status": "",
            "pre_mean_fatalities": None,
            "threshold_abs": None,
            "pre_months_used": 0,
            "followup_months_available": 0,
            "peak_fatalities_post": None,
            "degenerate_premean": False,
            "resumption_months": [],
        }
        series = series_by_iso.get(target_iso)
        if series is None:
            out["status"] = "no_ucdp_country"
            rows.append(out)
            continue
        month_index = {m: i for i, m in enumerate(series.index)}
        event_pos = month_index.get(str(event_month))
        if event_pos is None:
            out["status"] = "event_month_outside_ucdp"
            rows.append(out)
            continue
        pre_positions = list(range(event_pos - pre_months, event_pos))
        pre_available = [p for p in pre_positions if 0 <= p < len(series)]
        post_positions = list(range(event_pos, event_pos + horizon))
        post_available = [p for p in post_positions if 0 <= p < len(series)]
        out["pre_months_used"] = int(len(pre_available))
        out["followup_months_available"] = int(len(post_available))
        if len(pre_available) < pre_months:
            out["status"] = "insufficient_pre_window"
            rows.append(out)
            continue
        pre_values = series.iloc[pre_available].to_numpy(dtype=float)
        pre_mean = float(np.mean(pre_values))
        out["pre_mean_fatalities"] = pre_mean
        out["threshold_abs"] = float(threshold * pre_mean)
        out["degenerate_premean"] = bool(pre_mean <= 0)
        if len(post_available) < horizon:
            # partial follow-up: record what is observable but do not code a
            # binary outcome (it would confound censoring with no-resumption)
            out["status"] = "insufficient_followup"
            out["peak_fatalities_post"] = (
                float(series.iloc[post_available].max()) if post_available else None
            )
            rows.append(out)
            continue
        post_values = series.iloc[post_available].to_numpy(dtype=float)
        out["peak_fatalities_post"] = float(post_values.max())
        above = post_values > (threshold * pre_mean)
        resumed = False
        t_res = horizon
        if sustain <= 1:
            hits = np.flatnonzero(above)
            if hits.size:
                resumed, t_res = True, int(hits[0])
        else:
            run = 0
            for i, flag in enumerate(above):
                run = run + 1 if flag else 0
                if run >= sustain:
                    resumed = True
                    t_res = int(i - sustain + 1)
                    break
        out["resumption"] = bool(resumed)
        out["time_to_resumption"] = int(t_res)
        out["resumption_months"] = [
            str(series.index[p])
            for i, p in enumerate(post_available)
            if above[i]
        ]
        out["status"] = "ok"
        rows.append(out)
    return pd.DataFrame(rows)


# ===========================================================================
# 8. Backwards-compatible helpers kept from the project skeleton
# ===========================================================================
def normalised_decay_curve(
    decay_curve: Sequence[float], baseline: float, peak: float
) -> np.ndarray:
    """Map a decay curve onto a 0-baseline / 1-peak attention index."""
    curve = np.asarray(decay_curve, dtype=float)
    denom = peak - baseline
    if denom <= 0:
        return np.full_like(curve, np.nan)
    return (curve - baseline) / denom
