"""Statistical models for *The Half-Life of Peace*.

The event-level analysis is deliberately small (tens of ceasefires), so the
emphasis is on effect sizes with honest uncertainty and on resampling
inference, not on p-value hunting.  Every function reports enough detail to
regenerate every number quoted in the paper.

No scikit-learn dependency: AUC, (penalised) logistic regression, repeated
stratified cross-validation, leave-one-out validation, permutation tests and a
Cox proportional-hazards fit are implemented with numpy/statsmodels.  The
penalised logistic is a ridge-penalised Newton/IRLS solver; the MLE and its
confidence intervals come from statsmodels when the model is estimable.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats

Z_975 = 1.959963984540054


# ===========================================================================
# Ranking metric
# ===========================================================================
def auc_score(y_true: Sequence[float], scores: Sequence[float]) -> float:
    """Area under the ROC curve via the Mann-Whitney rank statistic.

    Handles ties through mid-ranks.  Returns ``nan`` if only one class is
    present.
    """
    y = np.asarray(y_true, dtype=float)
    s = np.asarray(scores, dtype=float)
    mask = np.isfinite(y) & np.isfinite(s)
    y, s = y[mask], s[mask]
    y = (y > 0.5).astype(int)
    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = stats.rankdata(s)  # average ranks for ties
    sum_pos = float(ranks[y == 1].sum())
    auc = (sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def auc_bootstrap_ci(
    y_true: Sequence[float],
    scores: Sequence[float],
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Percentile-bootstrap CI for an AUC (observations resampled)."""
    y = np.asarray(y_true, dtype=float)
    s = np.asarray(scores, dtype=float)
    mask = np.isfinite(y) & np.isfinite(s)
    y, s = y[mask], s[mask]
    out: Dict[str, object] = {
        "auc": auc_score(y, s), "ci_low": None, "ci_high": None,
        "n": int(len(y)), "n_boot": int(n_boot),
    }
    if len(y) < 6:
        return out
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if len(np.unique(y[idx])) < 2:
            continue
        boots.append(auc_score(y[idx], s[idx]))
    boots = np.asarray([b for b in boots if np.isfinite(b)], dtype=float)
    if boots.size:
        out["ci_low"] = float(np.percentile(boots, 100 * alpha / 2))
        out["ci_high"] = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return out


# ===========================================================================
# Logistic regression (ridge-penalised IRLS, no sklearn)
# ===========================================================================
def standardize(x: Sequence[float]) -> Tuple[np.ndarray, float, float]:
    """z-standardise with ddof=0; zero-variance columns become zeros."""
    arr = np.asarray(x, dtype=float)
    mean = float(np.nanmean(arr)) if len(arr) else 0.0
    sd = float(np.nanstd(arr)) if len(arr) else 0.0
    if not np.isfinite(sd) or sd == 0:
        return np.zeros_like(arr), mean, 1.0
    return (arr - mean) / sd, mean, sd


def _sigmoid(eta: np.ndarray) -> np.ndarray:
    eta = np.clip(eta, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-eta))


def fit_logistic(
    X: np.ndarray,
    y: Sequence[float],
    *,
    penalty: float = 0.0,
    max_iter: int = 200,
    tol: float = 1e-10,
) -> Dict[str, object]:
    """Newton/IRLS logistic regression with an optional L2 penalty.

    ``X`` must already include an intercept column in position 0; the
    intercept is never penalised.  Returns coefficients, standard errors
    (from the penalised observed information; approximate for ``penalty>0``),
    convergence diagnostics and fitted probabilities.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    y = (y > 0.5).astype(float)
    n, p = X.shape
    out: Dict[str, object] = {
        "beta": None, "se": None, "converged": False, "n_iter": 0,
        "fitted": None, "n": int(n), "penalty": float(penalty),
    }
    if n == 0 or p == 0:
        return out
    beta = np.zeros(p)
    if 0 < y.mean() < 1:
        beta[0] = math.log(y.mean() / (1 - y.mean()))
    penalty_vec = np.full(p, float(penalty))
    penalty_vec[0] = 0.0
    converged = False
    for it in range(1, max_iter + 1):
        eta = X @ beta
        mu = _sigmoid(eta)
        w = np.clip(mu * (1.0 - mu), 1e-9, None)
        grad = X.T @ (y - mu) - penalty_vec * beta
        hess = X.T @ (X * w[:, None])
        hess = hess + np.diag(penalty_vec + 1e-9 * np.eye(p).diagonal())
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:  # pragma: no cover
            step = np.linalg.lstsq(hess, grad, rcond=None)[0]
        # step-halving keeps the penalised objective monotone
        old_obj = _neg_loglik(X, y, beta, penalty_vec)
        scale = 1.0
        accepted = False
        for _ in range(25):
            cand = beta + scale * step
            if _neg_loglik(X, y, cand, penalty_vec) <= old_obj + 1e-12:
                beta = cand
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            beta = beta + step
        if np.max(np.abs(step)) < tol:
            converged = True
            out["n_iter"] = it
            break
    out["n_iter"] = it
    out["converged"] = bool(converged)
    out["beta"] = beta
    try:
        eta = X @ beta
        mu = _sigmoid(eta)
        w = np.clip(mu * (1.0 - mu), 1e-9, None)
        hess = X.T @ (X * w[:, None]) + np.diag(penalty_vec + 1e-9)
        cov = np.linalg.inv(hess)
        out["se"] = np.sqrt(np.clip(np.diag(cov), 0, None))
    except np.linalg.LinAlgError:  # pragma: no cover
        out["se"] = np.full(p, np.nan)
    out["fitted"] = _sigmoid(X @ beta)
    out["loglik"] = float(-_neg_loglik(X, y, beta, penalty_vec))
    return out


def _neg_loglik(X: np.ndarray, y: np.ndarray, beta: np.ndarray, penalty_vec: np.ndarray) -> float:
    eta = np.clip(X @ beta, -35.0, 35.0)
    # stable log-likelihood
    ll = float(np.sum(y * eta - np.logaddexp(0.0, eta)))
    pen = 0.5 * float(np.sum(penalty_vec * beta * beta))
    return -ll + pen


def design_matrix(
    df: pd.DataFrame,
    numeric: Sequence[str],
    categorical: Sequence[str] = (),
    *,
    drop_first: bool = True,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Build a numeric design matrix (intercept first) from a tidy frame.

    Numeric columns are standardised before entering the model.  Categorical
    columns become dummy variables with the first level dropped.  Rows with
    missing outcomes or predictors are dropped.  Returns
    ``(X_with_intercept, y, cleaned_frame)``.
    """
    cols = list(numeric) + list(categorical)
    work = df[["y"] + cols].copy()
    work = work.replace([np.inf, -np.inf], np.nan).dropna()
    X_parts = [pd.Series(1.0, index=work.index, name="const")]
    for col in numeric:
        z, _, _ = standardize(work[col].astype(float))
        X_parts.append(pd.Series(z, index=work.index, name=col))
    for col in categorical:
        dummies = pd.get_dummies(
            work[col].astype(str), prefix=col, drop_first=drop_first, dtype=float
        )
        # drop zero-variance dummies (levels absent after listwise deletion)
        dummies = dummies.loc[:, dummies.std(ddof=0) > 0]
        X_parts.extend([dummies[c] for c in dummies.columns])
    X = pd.concat(X_parts, axis=1)
    y = work["y"].astype(float)
    return X, y, work


def statsmodels_logit(
    X: pd.DataFrame, y: Sequence[float]
) -> Dict[str, object]:
    """Unpenalised MLE via statsmodels, with Wald CIs; robust to non-convergence."""
    import warnings

    import statsmodels.api as sm

    X = pd.DataFrame(X).astype(float)
    y = np.asarray(y, dtype=float)
    out: Dict[str, object] = {
        "params": None, "bse": None, "pvalues": None,
        "converged": False, "n": int(len(y)), "error": None,
    }
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.Logit(y, X.to_numpy()).fit(disp=False, maxiter=300)
        out["params"] = np.asarray(model.params, dtype=float)
        out["bse"] = np.asarray(model.bse, dtype=float)
        out["pvalues"] = np.asarray(model.pvalues, dtype=float)
        out["converged"] = bool(model.mle_retvals.get("converged", True))
        out["n"] = int(model.nobs)
        out["loglik"] = float(model.llf)
    except Exception as exc:  # noqa: BLE001 - separation is expected at n~20
        out["error"] = str(exc)[:300]
    return out


def coefficient_table(
    X: pd.DataFrame,
    y: Sequence[float],
    *,
    penalty: float = 0.0,
    method: str = "statsmodels",
) -> pd.DataFrame:
    """Tidy coefficient table: coef, SE, OR, 95% CI, p, n.

    Uses the statsmodels MLE when it converges (``penalty=0``); otherwise the
    ridge-penalised IRLS solver with Wald CIs from the penalised information.
    The ``method`` column says which was used for each row group.
    """
    X = pd.DataFrame(X).astype(float)
    y = np.asarray(y, dtype=float)
    names = list(X.columns)
    fitted_method = method
    if penalty == 0 and method == "statsmodels":
        mle = statsmodels_logit(X, y)
        if mle["params"] is not None and mle["converged"]:
            beta = np.asarray(mle["params"], float)
            se = np.asarray(mle["bse"], float)
            pvals = np.asarray(mle["pvalues"], float)
            fitted_method = "statsmodels-mle"
        else:
            fit = fit_logistic(X.to_numpy(), y, penalty=1e-4)
            beta = np.asarray(fit["beta"], float)
            se = np.asarray(fit["se"], float)
            pvals = 2 * stats.norm.sf(np.abs(beta / se))
            fitted_method = "ridge-irls (mle failed)"
    else:
        fit = fit_logistic(X.to_numpy(), y, penalty=penalty)
        beta = np.asarray(fit["beta"], float)
        se = np.asarray(fit["se"], float)
        pvals = 2 * stats.norm.sf(np.abs(beta / np.where(se == 0, np.nan, se)))
        fitted_method = "ridge-irls"

    rows = []
    for i, name in enumerate(names):
        b = float(beta[i])
        s = float(se[i]) if i < len(se) else float("nan")
        if name == "const":
            odds = float("nan")
            ci_low = ci_high = float("nan")
            or_ci_low = or_ci_high = float("nan")
        else:
            odds = float(math.exp(b)) if abs(b) < 700 else float("inf")
            ci_low, ci_high = b - Z_975 * s, b + Z_975 * s
            or_ci_low = float(math.exp(ci_low)) if abs(ci_low) < 700 else float("inf")
            or_ci_high = float(math.exp(ci_high)) if abs(ci_high) < 700 else float("inf")
        rows.append(
            {
                "term": name,
                "coef": b,
                "std_err": s,
                "odds_ratio": odds,
                "ci_low": or_ci_low if name != "const" else None,
                "ci_high": or_ci_high if name != "const" else None,
                "coef_ci_low": ci_low if name != "const" else None,
                "coef_ci_high": ci_high if name != "const" else None,
                "p": float(pvals[i]) if np.isfinite(pvals[i]) else None,
                "n": int(len(y)),
                "method": fitted_method,
            }
        )
    return pd.DataFrame(rows)


# ===========================================================================
# Cross-validation
# ===========================================================================
def _stratified_folds(y: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Assign fold labels stratified by class; each class shuffled then dealt."""
    folds = np.empty(len(y), dtype=int)
    for cls in np.unique(y):
        idx = np.flatnonzero(y == cls)
        rng.shuffle(idx)
        folds[idx] = np.arange(len(idx)) % k
    return folds


def _fit_predict_auc(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    *,
    penalty: float,
) -> np.ndarray:
    """Standardise on train, fit ridge logistic, return test probabilities."""
    mean = X_train.mean(axis=0)
    sd = X_train.std(axis=0)
    sd = np.where((sd == 0) | ~np.isfinite(sd), 1.0, sd)
    Xtr = (X_train - mean) / sd
    Xte = (X_test - mean) / sd
    Xtr = np.column_stack([np.ones(len(Xtr)), Xtr])
    Xte = np.column_stack([np.ones(len(Xte)), Xte])
    fit = fit_logistic(Xtr, y_train, penalty=penalty)
    beta = np.asarray(fit["beta"], dtype=float)
    eta = np.clip(Xte @ beta, -35.0, 35.0)
    return _sigmoid(eta)


def cross_val_auc(
    X: pd.DataFrame,
    y: Sequence[float],
    *,
    k: int = 5,
    repeats: int = 100,
    penalty: float = 1.0,
    seed: int = 0,
) -> Dict[str, object]:
    """Repeated stratified k-fold cross-validated AUC.

    For each repeat every observation is predicted exactly once out-of-fold;
    the AUC is computed on the pooled out-of-fold predictions, giving one AUC
    per repeat.  The reported ``auc_cv`` is the mean across repeats and
    ``auc_cv_sd`` its between-repeat standard deviation (a stability measure,
    not a sampling SE).
    """
    X = pd.DataFrame(X).astype(float)
    y = np.asarray(y, dtype=float)
    y = (y > 0.5).astype(int)
    out: Dict[str, object] = {
        "auc_cv": None, "auc_cv_sd": None, "n": int(len(y)),
        "k": int(k), "repeats": int(repeats), "penalty": float(penalty),
        "n_pos": int(y.sum()), "n_neg": int(len(y) - y.sum()),
        "fold_aucs": [], "status": "",
    }
    n_min_class = int(min(y.sum(), len(y) - y.sum()))
    if n_min_class < 2 or len(y) < 6:
        out["status"] = "insufficient_class_support"
        return out
    k_eff = int(max(2, min(k, n_min_class)))
    out["k"] = k_eff
    rng = np.random.default_rng(seed)
    Xv = X.to_numpy(dtype=float)
    aucs: List[float] = []
    preds_last: Optional[np.ndarray] = None
    for _ in range(repeats):
        folds = _stratified_folds(y, k_eff, rng)
        preds = np.full(len(y), np.nan)
        for f in range(k_eff):
            test = folds == f
            train = ~test
            if len(np.unique(y[train])) < 2 or len(np.unique(y[test])) < 2:
                # cannot evaluate this fold; leave its predictions out
                continue
            preds[test] = _fit_predict_auc(
                Xv[train], y[train], Xv[test], penalty=penalty
            )
        preds_last = preds.copy()
        ok = np.isfinite(preds)
        if len(np.unique(y[ok])) == 2:
            aucs.append(auc_score(y[ok], preds[ok]))
    aucs_arr = np.asarray([a for a in aucs if np.isfinite(a)], dtype=float)
    if aucs_arr.size:
        out["auc_cv"] = float(np.mean(aucs_arr))
        out["auc_cv_sd"] = float(np.std(aucs_arr, ddof=1)) if aucs_arr.size > 1 else 0.0
        out["fold_aucs"] = aucs_arr.tolist()
        out["status"] = "ok"
        out["auc_cv_q05"] = float(np.percentile(aucs_arr, 5))
        out["auc_cv_q95"] = float(np.percentile(aucs_arr, 95))
    else:
        out["status"] = "all_repeats_failed"
    out["predictions_last_repeat"] = (
        preds_last.tolist() if preds_last is not None else None
    )
    return out


def loo_predictions(
    X: pd.DataFrame,
    y: Sequence[float],
    *,
    penalty: float = 1.0,
) -> Dict[str, object]:
    """Leave-one-out out-of-sample probabilities and their AUC."""
    X = pd.DataFrame(X).astype(float)
    y = np.asarray(y, dtype=float)
    y = (y > 0.5).astype(int)
    Xv = X.to_numpy(dtype=float)
    preds = np.full(len(y), np.nan)
    for i in range(len(y)):
        train = np.ones(len(y), dtype=bool)
        train[i] = False
        if len(np.unique(y[train])) < 2:
            continue
        preds[i] = _fit_predict_auc(
            Xv[train], y[train], Xv[i:i + 1], penalty=penalty
        )[0]
    ok = np.isfinite(preds)
    return {
        "loo_auc": float(auc_score(y[ok], preds[ok])) if ok.sum() == len(y) else None,
        "predictions": preds.tolist(),
        "n": int(len(y)),
        "n_evaluated": int(ok.sum()),
    }


# ===========================================================================
# Permutation inference
# ===========================================================================
def permutation_coef_test(
    X: pd.DataFrame,
    y: Sequence[float],
    *,
    n_perm: int = 1000,
    penalty: float = 1.0,
    coef_index: int = 1,
    seed: int = 0,
    two_sided: bool = True,
) -> Dict[str, object]:
    """Permutation test on a single logistic coefficient.

    The statistic is the standardised logistic coefficient at
    ``coef_index`` (default: the first regressor, i.e. standardised PAHL).
    ``y`` is permuted ``n_perm`` times; the p-value is the fraction of
    |null statistic| at least as large as |observed| (two-sided), with the
    standard +1 correction.  The ridge penalty is used throughout so that
    separation in permuted samples cannot produce infinite statistics.
    """
    X = pd.DataFrame(X).astype(float)
    y = np.asarray(y, dtype=float)
    y = (y > 0.5).astype(int)
    # allow callers to pass predictors without an intercept
    if "const" not in X.columns:
        X = pd.concat([pd.Series(1.0, index=X.index, name="const"), X], axis=1)
    Xv = X.to_numpy(dtype=float)
    fit = fit_logistic(Xv, y, penalty=penalty)
    beta = np.asarray(fit["beta"], dtype=float)
    obs = float(beta[coef_index])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for i in range(n_perm):
        y_perm = rng.permutation(y)
        if len(np.unique(y_perm)) < 2:
            null[i] = np.nan
            continue
        fit_perm = fit_logistic(Xv, y_perm, penalty=penalty)
        null[i] = float(np.asarray(fit_perm["beta"], dtype=float)[coef_index])
    null = null[np.isfinite(null)]
    if null.size == 0:
        return {"p": None, "coef_obs": obs, "n_perm": 0, "null_sd": None}
    if two_sided:
        p = (1 + int(np.sum(np.abs(null) >= abs(obs)))) / (1 + len(null))
    else:
        p = (1 + int(np.sum(null >= obs))) / (1 + len(null))
    return {
        "p": float(p),
        "coef_obs": obs,
        "null_sd": float(np.std(null, ddof=1)),
        "null_q025": float(np.percentile(null, 2.5)),
        "null_q975": float(np.percentile(null, 97.5)),
        "n_perm": int(len(null)),
        "two_sided": bool(two_sided),
    }


def bh_fdr(pvalues: Sequence[float], alpha: float = 0.05) -> Dict[str, object]:
    """Benjamini-Hochberg FDR adjustment for a family of reported tests."""
    p = np.asarray([x for x in pvalues if x is not None and np.isfinite(x)], dtype=float)
    out: Dict[str, object] = {
        "n_tests": int(len(p)), "alpha": float(alpha),
        "adjusted": [], "n_significant": None,
    }
    if len(p) == 0:
        out["n_significant"] = 0
        return out
    order = np.argsort(p)
    ranked = p[order]
    m = len(p)
    adj = np.empty(m)
    adj_sorted = ranked * m / np.arange(1, m + 1)
    # enforce monotonicity from the largest p downwards
    adj_sorted = np.minimum.accumulate(adj_sorted[::-1])[::-1]
    adj[order] = np.clip(adj_sorted, 0, 1)
    out["adjusted"] = adj.tolist()
    out["n_significant"] = int(np.sum(adj <= alpha))
    return out


# ===========================================================================
# Survival: Cox proportional hazards
# ===========================================================================
def cox_ph(
    durations: Sequence[float],
    event_observed: Sequence[int],
    x: Sequence[float],
    *,
    label: str = "pahl_z",
) -> Dict[str, object]:
    """Single-covariate Cox proportional-hazards fit via statsmodels PHReg.

    Returns the log hazard coefficient, its hazard ratio, CI and p, and
    ``method`` (``cox-phreg`` or ``failed``).  Coefficients are on the same
    scale as a log-odds coefficient in direction (positive = longer PAHL
    associated with higher hazard of resumption).
    """
    import warnings

    d = np.asarray(durations, dtype=float)
    e = np.asarray(event_observed, dtype=float)
    xv = np.asarray(x, dtype=float)
    mask = np.isfinite(d) & np.isfinite(e) & np.isfinite(xv)
    d, e, xv = d[mask], e[mask], xv[mask]
    out: Dict[str, object] = {
        "coef": None, "hr": None, "ci_low": None, "ci_high": None,
        "p": None, "n": int(len(d)), "n_events": int(np.sum(e > 0.5)),
        "method": "failed", "covariate": label, "error": None,
    }
    if len(d) < 8 or out["n_events"] < 2 or out["n_events"] >= len(d):
        out["error"] = "insufficient variation for survival model"
        return out
    try:
        from statsmodels.duration.hazard_regression import PHReg

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = PHReg(d, xv.reshape(-1, 1), status=e.astype(int))
            fit = model.fit(disp=False)
        coef = float(fit.params[0])
        se = float(fit.bse[0])
        out.update(
            {
                "coef": coef,
                "hr": float(math.exp(coef)) if abs(coef) < 700 else float("inf"),
                "ci_low": float(math.exp(coef - Z_975 * se)) if abs(coef - Z_975 * se) < 700 else float("inf"),
                "ci_high": float(math.exp(coef + Z_975 * se)) if abs(coef + Z_975 * se) < 700 else float("inf"),
                "coef_ci_low": coef - Z_975 * se,
                "coef_ci_high": coef + Z_975 * se,
                "p": float(fit.pvalues[0]),
                "method": "cox-phreg",
            }
        )
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)[:300]
    return out


# ===========================================================================
# Legacy resampling helpers kept from the project skeleton
# ===========================================================================
def bootstrap_spearman(
    x: Sequence[float],
    y: Sequence[float],
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Spearman rank correlation with a percentile bootstrap CI."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    out: Dict[str, object] = {
        "rho": None, "p": None, "ci_low": None, "ci_high": None, "n": int(n),
    }
    if n < 4 or len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return out
    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(x[idx])) < 2 or len(np.unique(y[idx])) < 2:
            continue
        boots.append(stats.spearmanr(x[idx], y[idx]).correlation)
    boots = np.asarray([b for b in boots if np.isfinite(b)], dtype=float)
    out.update(
        {
            "rho": float(rho),
            "p": float(p),
            "ci_low": float(np.percentile(boots, 100 * alpha / 2)) if boots.size else None,
            "ci_high": float(np.percentile(boots, 100 * (1 - alpha / 2))) if boots.size else None,
            "n_boot": int(boots.size),
        }
    )
    return out


def permutation_pvalue(
    x: Sequence[float],
    y: Sequence[float],
    n_perm: int = 1000,
    seed: int = 0,
) -> Dict[str, object]:
    """Two-sided permutation test for a Spearman correlation."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    out: Dict[str, object] = {"rho": None, "p_perm": None, "n": int(len(x))}
    if len(x) < 4:
        return out
    observed = abs(stats.spearmanr(x, y).correlation)
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_perm):
        permuted = rng.permutation(y)
        if abs(stats.spearmanr(x, permuted).correlation) >= observed:
            count += 1
    out.update(
        {
            "rho": float(np.sign(stats.spearmanr(x, y).correlation) * observed),
            "p_perm": (count + 1) / (n_perm + 1),
        }
    )
    return out


def median_split_test(
    values: Sequence[float],
    outcome: Sequence[int],
) -> Dict[str, object]:
    """Fisher exact test comparing resumption rates above vs below the median."""
    values = np.asarray(values, dtype=float)
    outcome = np.asarray(outcome, dtype=float)
    mask = np.isfinite(values) & np.isfinite(outcome)
    values, outcome = values[mask], outcome[mask]
    out: Dict[str, object] = {"p": None, "n": int(len(values))}
    if len(values) < 6 or len(np.unique(outcome)) < 2:
        return out
    threshold = float(np.median(values))
    high = outcome[values > threshold]
    low = outcome[values <= threshold]
    table = [
        [int(high.sum()), int(len(high) - high.sum())],
        [int(low.sum()), int(len(low) - low.sum())],
    ]
    odds, p = stats.fisher_exact(table)
    out.update(
        {
            "threshold": threshold,
            "n_high": int(len(high)),
            "n_low": int(len(low)),
            "resumption_rate_high": float(high.mean()) if len(high) else None,
            "resumption_rate_low": float(low.mean()) if len(low) else None,
            "odds_ratio": float(odds) if np.isfinite(odds) else None,
            "odds_ratio_infinite": bool(not np.isfinite(odds)),
            "p": float(p),
        }
    )
    return out
