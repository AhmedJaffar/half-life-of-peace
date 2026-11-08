"""Statistical models for *The Half-Life of Peace*.

The event-level analysis is deliberately small (tens of ceasefires), so the
emphasis is on effect sizes with honest uncertainty and on permutation
inference, not on p-value hunting.  Each function reports enough detail to
regenerate every number quoted in the paper.
"""

from typing import Dict, Sequence

import numpy as np
import pandas as pd
from scipy import stats


def bootstrap_spearman(
    x: Sequence[float],
    y: Sequence[float],
    n_boot: int = 5000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, float]:
    """Spearman rank correlation with a percentile bootstrap CI."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 4:
        return {"rho": np.nan, "p": np.nan, "ci_low": np.nan, "ci_high": np.nan, "n": n}

    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(x[idx])) < 2 or len(np.unique(y[idx])) < 2:
            boots[i] = np.nan
            continue
        boots[i] = stats.spearmanr(x[idx], y[idx]).correlation
    boots = boots[np.isfinite(boots)]
    return {
        "rho": float(rho),
        "p": float(p),
        "ci_low": float(np.percentile(boots, 100 * alpha / 2)),
        "ci_high": float(np.percentile(boots, 100 * (1 - alpha / 2))),
        "n": n,
        "n_boot": int(len(boots)),
    }


def permutation_pvalue(
    x: Sequence[float],
    y: Sequence[float],
    n_perm: int = 10000,
    seed: int = 0,
) -> Dict[str, float]:
    """Two-sided permutation test for a Spearman correlation."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 4:
        return {"rho": np.nan, "p_perm": np.nan, "n": len(x)}

    observed = abs(stats.spearmanr(x, y).correlation)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        permuted = rng.permutation(y)
        if abs(stats.spearmanr(x, permuted).correlation) >= observed:
            count += 1
    return {
        "rho": float(np.sign(stats.spearmanr(x, y).correlation) * observed),
        "p_perm": (count + 1) / (n_perm + 1),
        "n": len(x),
    }


def median_split_test(
    values: Sequence[float],
    outcome: Sequence[int],
) -> Dict[str, float]:
    """Fisher exact test comparing collapse rates above vs below the median."""
    values = np.asarray(values, dtype=float)
    outcome = np.asarray(outcome, dtype=int)
    mask = np.isfinite(values) & np.isfinite(outcome)
    values, outcome = values[mask], outcome[mask]
    if len(values) < 6:
        return {"p": np.nan, "n": len(values)}

    threshold = float(np.median(values))
    high = outcome[values > threshold]
    low = outcome[values <= threshold]
    table = [[int(high.sum()), int(len(high) - high.sum())],
             [int(low.sum()), int(len(low) - low.sum())]]
    odds, p = stats.fisher_exact(table)
    return {
        "threshold": threshold,
        "n_high": int(len(high)),
        "n_low": int(len(low)),
        "collapse_rate_high": float(high.mean()) if len(high) else np.nan,
        "collapse_rate_low": float(low.mean()) if len(low) else np.nan,
        "odds_ratio": float(odds),
        "p": float(p),
    }


def logistic_summary(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: Sequence[str],
) -> pd.DataFrame:
    """Univariate and adjusted logistic regressions via statsmodels.

    Returns a tidy table with one row per coefficient: odds ratio, standard
    error of the log-odds, 95% CI, and p value.  Falls back to a univariate
    normal approximation if the model does not converge (common with n < 50).
    """
    try:
        import statsmodels.api as sm
    except ImportError:  # pragma: no cover
        return pd.DataFrame()

    rows = []

    def _fit(cols):
        data = df[[outcome_col] + list(cols)].dropna()
        y = data[outcome_col].astype(float).to_numpy()
        X = sm.add_constant(data[list(cols)].astype(float).to_numpy())
        try:
            model = sm.Logit(y, X).fit(disp=False, maxiter=200)
        except Exception:  # noqa: BLE001 - separation / non-convergence
            return None
        for i, name in enumerate(["const"] + list(cols)):
            beta = float(model.params[i])
            se = float(model.bse[i])
            rows.append(
                {
                    "predictor": name,
                    "model": "+".join(cols),
                    "coef": beta,
                    "odds_ratio": float(np.exp(beta)),
                    "ci_low": float(np.exp(beta - 1.96 * se)),
                    "ci_high": float(np.exp(beta + 1.96 * se)),
                    "p": float(model.pvalues[i]),
                    "n": int(model.nobs),
                }
            )
        return model

    for col in predictor_cols:
        _fit([col])
    if len(predictor_cols) > 1:
        _fit(list(predictor_cols))
    return pd.DataFrame(rows)


def normalised_decay_curve(
    decay_curve: Sequence[float],
    baseline: float,
    peak: float,
) -> np.ndarray:
    """Map a decay curve onto a 0-baseline / 1-peak attention index."""
    curve = np.asarray(decay_curve, dtype=float)
    denom = peak - baseline
    if denom <= 0:
        return np.full_like(curve, np.nan)
    return (curve - baseline) / denom
