"""Uncertainty for within-subject contrasts.

Participants are the resampling unit. A bootstrap draw takes participants
with replacement and keeps each person's four conditions together. Sign-flip
and label-permutation tests use the same unit. Trial-level regression is
reported only with subject-clustered standard errors, and those errors are
compared with the naive errors that treat trials as independent people.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from hbedb_sway.constants import CONTRASTS

CONDITION_FORMULA = (
    "{outcome} ~ C(vision, Treatment(reference='Open'))"
    " * C(surface, Treatment(reference='Firm'))"
)
AGE_FORMULA = (
    "{outcome} ~ C(vision, Treatment(reference='Open'))"
    " * C(surface, Treatment(reference='Firm'))"
    " * C(age_group, Treatment(reference='Young'))"
)


def stable_seed(master: int, *parts: object) -> int:
    text = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(f"{master}|{text}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little")


def _percentile_interval(samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    low, high = np.percentile(samples, [2.5, 97.5], axis=0, method="linear")
    return np.asarray(low, dtype=float), np.asarray(high, dtype=float)


def signflip_p(values: np.ndarray, n_perm: int, seed: int) -> float:
    """Two-sided sign-flip p for the mean, with the +1 correction."""
    values = np.asarray(values, dtype=float)
    observed = float(values.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, values.size))
    permuted = (signs * values).mean(axis=1)
    count = int(np.sum(np.abs(permuted) >= abs(observed) - 1e-12))
    return (count + 1) / (n_perm + 1)


def permutation_diff_p(young: np.ndarray, old: np.ndarray, n_perm: int, seed: int) -> float:
    """Two-sided label-permutation p for the difference in means, old minus young."""
    young = np.asarray(young, dtype=float)
    old = np.asarray(old, dtype=float)
    observed = float(old.mean() - young.mean())
    pooled = np.concatenate([young, old])
    n_young = young.size
    rng = np.random.default_rng(seed)
    keys = rng.random((n_perm, pooled.size))
    order = np.argsort(keys, axis=1)
    shuffled = pooled[order]
    diffs = shuffled[:, n_young:].mean(axis=1) - shuffled[:, :n_young].mean(axis=1)
    count = int(np.sum(np.abs(diffs) >= abs(observed) - 1e-12))
    return (count + 1) / (n_perm + 1)


def summarize_contrasts(
    frame: pd.DataFrame,
    outcome: str,
    n_boot: int,
    n_perm: int,
    seed: int,
) -> pd.DataFrame:
    columns = [key for key, _label in CONTRASTS]
    values = frame[columns].to_numpy(dtype=float)
    n = values.shape[0]
    if n < 3:
        raise ValueError("At least three participants are required.")
    rng = np.random.default_rng(stable_seed(seed, outcome, "bootstrap"))
    draw = rng.integers(0, n, size=(n_boot, n))
    boot_means = values[draw].mean(axis=1)
    boot_medians = np.median(values[draw], axis=1)
    mean = values.mean(axis=0)
    median = np.median(values, axis=0)
    low, high = _percentile_interval(boot_means)
    median_low, median_high = _percentile_interval(boot_medians)
    boot_se = boot_means.std(axis=0, ddof=1)
    rows = []
    for index, (key, label) in enumerate(CONTRASTS):
        column = values[:, index]
        deviation = float(column.std(ddof=1))
        t_critical = float(stats.t.ppf(0.975, n - 1))
        t_se = deviation / np.sqrt(n)
        if deviation < 1e-12:
            skewness = float("nan")
        else:
            skewness = float(stats.skew(column, bias=False))
        rows.append(
            {
                "outcome": outcome,
                "contrast": key,
                "contrast_label": label,
                "n_subjects": int(n),
                "n_positive": int(np.sum(column > 0)),
                "n_negative": int(np.sum(column < 0)),
                "mean": float(mean[index]),
                "boot_se": float(boot_se[index]),
                "ci_low": float(low[index]),
                "ci_high": float(high[index]),
                "t_ci_low": float(mean[index] - t_critical * t_se),
                "t_ci_high": float(mean[index] + t_critical * t_se),
                "median": float(median[index]),
                "median_ci_low": float(median_low[index]),
                "median_ci_high": float(median_high[index]),
                "dz": float(mean[index] / deviation) if deviation > 0 else np.nan,
                "skewness": skewness,
                "perm_p": signflip_p(
                    column,
                    n_perm,
                    stable_seed(seed, outcome, key, "signflip"),
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_age_differences(
    frame: pd.DataFrame,
    outcome: str,
    n_boot: int,
    n_perm: int,
    seed: int,
) -> pd.DataFrame:
    columns = [key for key, _label in CONTRASTS]
    young = frame.loc[frame["age_group"].eq("Young"), columns].to_numpy(dtype=float)
    old = frame.loc[frame["age_group"].eq("Old"), columns].to_numpy(dtype=float)
    if len(young) < 2 or len(old) < 2:
        raise ValueError("Each age group needs at least two participants.")
    rng = np.random.default_rng(stable_seed(seed, outcome, "age-bootstrap"))
    young_draw = rng.integers(0, len(young), size=(n_boot, len(young)))
    old_draw = rng.integers(0, len(old), size=(n_boot, len(old)))
    diffs = old[old_draw].mean(axis=1) - young[young_draw].mean(axis=1)
    observed = old.mean(axis=0) - young.mean(axis=0)
    low, high = _percentile_interval(diffs)
    boot_se = diffs.std(axis=0, ddof=1)
    rows = []
    for index, (key, label) in enumerate(CONTRASTS):
        rows.append(
            {
                "outcome": outcome,
                "contrast": key,
                "contrast_label": label,
                "n_young": int(len(young)),
                "n_old": int(len(old)),
                "diff_old_minus_young": float(observed[index]),
                "boot_se": float(boot_se[index]),
                "ci_low": float(low[index]),
                "ci_high": float(high[index]),
                "perm_p": permutation_diff_p(
                    young[:, index],
                    old[:, index],
                    n_perm,
                    stable_seed(seed, outcome, key, "age-perm"),
                ),
            }
        )
    return pd.DataFrame(rows)


def _slope(x: np.ndarray, y: np.ndarray) -> float:
    x_centered = x - x.mean()
    y_centered = y - y.mean()
    denominator = float(np.dot(x_centered, x_centered))
    if denominator <= 0:
        return float("nan")
    return float(np.dot(x_centered, y_centered) / denominator)


def age_slopes(
    frame: pd.DataFrame,
    outcome: str,
    n_boot: int,
    seed: int,
    contrasts: Sequence[str] | None = None,
) -> pd.DataFrame:
    keys = list(contrasts) if contrasts is not None else [key for key, _label in CONTRASTS]
    labels = dict(CONTRASTS)
    age = frame["age_years"].to_numpy(dtype=float)
    rows = []
    for key in keys:
        response = frame[key].to_numpy(dtype=float)
        observed = _slope(age, response)
        rng = np.random.default_rng(stable_seed(seed, outcome, key, "slope"))
        draw = rng.integers(0, age.size, size=(n_boot, age.size))
        slopes = np.empty(n_boot, dtype=float)
        for index in range(n_boot):
            slopes[index] = _slope(age[draw[index]], response[draw[index]])
        low, high = _percentile_interval(slopes)
        rows.append(
            {
                "outcome": outcome,
                "contrast": key,
                "contrast_label": labels[key],
                "n_subjects": int(age.size),
                "slope_per_year": observed,
                "ci_low": float(low),
                "ci_high": float(high),
            }
        )
    return pd.DataFrame(rows)


def condition_cell_means(means: pd.DataFrame, outcome: str, n_boot: int, seed: int) -> pd.DataFrame:
    """Bootstrap CI for the mean of participant-level condition means."""
    rows = []
    groups = [
        ("All", means),
        ("Young", means[means["age_group"].eq("Young")]),
        ("Old", means[means["age_group"].eq("Old")]),
    ]
    for group_name, group in groups:
        for vision in ("Open", "Closed"):
            for surface in ("Firm", "Foam"):
                values = group.loc[
                    group["vision"].eq(vision) & group["surface"].eq(surface),
                    outcome,
                ].to_numpy(dtype=float)
                rng = np.random.default_rng(
                    stable_seed(seed, outcome, group_name, vision, surface, "cell")
                )
                draw = rng.integers(0, values.size, size=(n_boot, values.size))
                boot = values[draw].mean(axis=1)
                low, high = _percentile_interval(boot)
                rows.append(
                    {
                        "outcome": outcome,
                        "age_group": group_name,
                        "vision": vision,
                        "surface": surface,
                        "n": int(values.size),
                        "mean": float(values.mean()),
                        "ci_low": float(low),
                        "ci_high": float(high),
                        "median": float(np.median(values)),
                        "q25": float(np.percentile(values, 25, method="linear")),
                        "q75": float(np.percentile(values, 75, method="linear")),
                    }
                )
    return pd.DataFrame(rows)


def repetition_reliability(trials: pd.DataFrame, outcome: str = "mv_cm_s") -> pd.DataFrame:
    """One-way random ICC for participants with the same number of valid repetitions."""
    kept = trials.loc[~trials["exclude"]].copy()
    rows = []
    for (vision, surface), group in kept.groupby(["vision", "surface"], sort=False):
        counts = group.groupby("subject").size()
        if counts.empty:
            continue
        k = int(counts.mode().iloc[0])
        usable_ids = counts[counts == k].index
        if k < 2 or len(usable_ids) < 3:
            continue
        subset = group[group["subject"].isin(usable_ids)].sort_values(["subject", "trial"])
        matrix = subset.pivot(index="subject", columns="rep_index", values=outcome).to_numpy(dtype=float)
        if matrix.shape[1] != k or np.isnan(matrix).any():
            continue
        n_people = matrix.shape[0]
        grand = float(matrix.mean())
        person_means = matrix.mean(axis=1)
        msb = k * np.sum((person_means - grand) ** 2) / (n_people - 1)
        msw = np.sum((matrix - person_means[:, None]) ** 2) / (n_people * (k - 1))
        icc = (msb - msw) / (msb + (k - 1) * msw) if (msb + (k - 1) * msw) != 0 else np.nan
        sem = float(np.sqrt(msw))
        rows.append(
            {
                "vision": vision,
                "surface": surface,
                "n_subjects": int(n_people),
                "k": int(k),
                "icc": float(icc),
                "sem_cm_s": sem,
                "se_of_mean_cm_s": sem / np.sqrt(k),
                "mean_mv": float(matrix.mean()),
            }
        )
    return pd.DataFrame(rows)


def _find_term(names: list[str], closed: bool, foam: bool, old: bool = False) -> str:
    hits = []
    for name in names:
        if name == "Intercept":
            continue
        if ("T.Closed" in name) != closed:
            continue
        if ("T.Foam" in name) != foam:
            continue
        if ("T.Old" in name) != old:
            continue
        hits.append(name)
    if len(hits) != 1:
        raise RuntimeError(f"Could not identify a model term (closed={closed}, foam={foam}, old={old}): {hits}")
    return hits[0]


def linear_combination(result, weights: dict[str, float]) -> dict[str, float]:
    names = list(result.params.index)
    row = np.zeros(len(names))
    for name, weight in weights.items():
        row[names.index(name)] = weight
    test = result.t_test(row)
    interval = np.asarray(test.conf_int(), dtype=float).reshape(-1)
    return {
        "estimate": float(np.asarray(test.effect).reshape(-1)[0]),
        "se": float(np.asarray(test.sd).reshape(-1)[0]),
        "ci_low": float(interval[0]),
        "ci_high": float(interval[1]),
        "p": float(np.asarray(test.pvalue).reshape(-1)[0]),
    }


def _estimand_weights(names: list[str], include_age: bool = False) -> dict[str, dict[str, float]]:
    closed = _find_term(names, closed=True, foam=False, old=False)
    foam = _find_term(names, closed=False, foam=True, old=False)
    interaction = _find_term(names, closed=True, foam=True, old=False)
    return {
        "vision_on_firm": {closed: 1.0},
        "vision_on_foam": {closed: 1.0, interaction: 1.0},
        "surface_eyes_open": {foam: 1.0},
        "surface_eyes_closed": {foam: 1.0, interaction: 1.0},
        "interaction": {interaction: 1.0},
    }


def fit_factorial(
    frame: pd.DataFrame,
    outcome: str,
    cluster: str = "subject",
):
    model_data = frame[[outcome, "vision", "surface", cluster]].dropna().copy()
    formula = CONDITION_FORMULA.format(outcome=outcome)
    model = smf.ols(formula, data=model_data)
    naive = model.fit()
    clustered = model.fit(cov_type="cluster", cov_kwds={"groups": model_data[cluster]})
    return naive, clustered, model_data


def factorial_contrast_table(naive, clustered) -> pd.DataFrame:
    names = list(clustered.params.index)
    weights = _estimand_weights(names)
    rows = []
    labels = dict(CONTRASTS)
    for key, label in CONTRASTS:
        naive_row = linear_combination(naive, weights[key])
        cluster_row = linear_combination(clustered, weights[key])
        rows.append(
            {
                "contrast": key,
                "contrast_label": label,
                "estimate": cluster_row["estimate"],
                "se_naive": naive_row["se"],
                "se_cluster": cluster_row["se"],
                "ci_low": cluster_row["ci_low"],
                "ci_high": cluster_row["ci_high"],
                "p_cluster": cluster_row["p"],
            }
        )
    return pd.DataFrame(rows)


def fit_log_age_model(trials: pd.DataFrame, outcome: str = "mv_cm_s") -> pd.DataFrame:
    model_data = trials.loc[~trials["exclude"], ["subject", "vision", "surface", "age_group", outcome]].dropna().copy()
    model_data["log_outcome"] = np.log(model_data[outcome])
    formula = AGE_FORMULA.format(outcome="log_outcome")
    clustered = smf.ols(formula, data=model_data).fit(
        cov_type="cluster",
        cov_kwds={"groups": model_data["subject"]},
    )
    names = list(clustered.params.index)
    weights = _estimand_weights(names)
    closed_old = _find_term(names, closed=True, foam=False, old=True)
    foam_old = _find_term(names, closed=False, foam=True, old=True)
    interaction_old = _find_term(names, closed=True, foam=True, old=True)
    age_weights = {
        "vision_on_firm_old_minus_young": {closed_old: 1.0},
        "surface_eyes_open_old_minus_young": {foam_old: 1.0},
        "interaction_old_minus_young": {interaction_old: 1.0},
    }
    rows = []
    labels = dict(CONTRASTS)
    for key, _label in CONTRASTS:
        row = linear_combination(clustered, weights[key])
        rows.append(
            {
                "term": key,
                "label": labels[key] + ", younger reference group, log scale",
                "log_estimate": row["estimate"],
                "se_cluster": row["se"],
                "ci_low": row["ci_low"],
                "ci_high": row["ci_high"],
                "ratio": float(np.exp(row["estimate"])),
                "ratio_ci_low": float(np.exp(row["ci_low"])),
                "ratio_ci_high": float(np.exp(row["ci_high"])),
            }
        )
    age_labels = {
        "vision_on_firm_old_minus_young": "Age difference in the firm eyes-closed effect, log scale",
        "surface_eyes_open_old_minus_young": "Age difference in the eyes-open foam effect, log scale",
        "interaction_old_minus_young": "Age difference in the interaction, log scale",
    }
    for key, weight in age_weights.items():
        row = linear_combination(clustered, weight)
        rows.append(
            {
                "term": key,
                "label": age_labels[key],
                "log_estimate": row["estimate"],
                "se_cluster": row["se"],
                "ci_low": row["ci_low"],
                "ci_high": row["ci_high"],
                "ratio": float(np.exp(row["estimate"])),
                "ratio_ci_low": float(np.exp(row["ci_low"])),
                "ratio_ci_high": float(np.exp(row["ci_high"])),
            }
        )
    return pd.DataFrame(rows)


def repetition_coefficient(trials: pd.DataFrame, outcome: str = "mv_cm_s") -> dict[str, float]:
    model_data = trials.loc[~trials["exclude"], ["subject", "vision", "surface", "rep_index", outcome]].dropna().copy()
    formula = CONDITION_FORMULA.format(outcome=outcome) + " + rep_index"
    clustered = smf.ols(formula, data=model_data).fit(
        cov_type="cluster",
        cov_kwds={"groups": model_data["subject"]},
    )
    row = linear_combination(clustered, {"rep_index": 1.0})
    row["n_trials"] = int(len(model_data))
    row["n_subjects"] = int(model_data["subject"].nunique())
    return row


def random_intercept_icc(trials: pd.DataFrame, outcome: str = "mv_cm_s") -> dict[str, float] | None:
    model_data = trials.loc[~trials["exclude"], ["subject", "vision", "surface", outcome]].dropna().copy()
    formula = CONDITION_FORMULA.format(outcome=outcome)
    try:
        fitted = smf.mixedlm(formula, model_data, groups=model_data["subject"]).fit(
            method="lbfgs",
            reml=True,
            maxiter=200,
        )
    except Exception:
        return None
    between = float(np.asarray(fitted.cov_re).reshape(-1)[0])
    within = float(fitted.scale)
    if between + within <= 0:
        return None
    return {
        "between_subject_variance": between,
        "residual_variance": within,
        "icc": between / (between + within),
        "converged": bool(fitted.converged),
    }
