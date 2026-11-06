"""Center-of-pressure summaries for one quiet-stance trial.

Resultant mean velocity is the COP path length divided by the elapsed time
between the first and last sample. It is a speed. The posturography literature
still calls it mean velocity, and that name is kept here.

The area is the 95% prediction ellipse of the COP cloud. It is not the
confidence ellipse of the mean COP, which would shrink as the trial lengthens.
The finite-sample critical value follows the usual F form (Prieto and
colleagues, 1996; Duarte, 2015).
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def _as_series(values: np.ndarray) -> np.ndarray:
    series = np.asarray(values, dtype=float)
    if series.ndim != 1 or series.size < 3:
        raise ValueError("A COP series needs at least three samples.")
    if not np.isfinite(series).all():
        raise ValueError("COP series contains a non-finite value.")
    return series


def resultant_mean_velocity(cop_x: np.ndarray, cop_y: np.ndarray, fs_hz: float) -> float:
    """Path length divided by elapsed time, in the distance unit of the inputs per second."""
    x = _as_series(cop_x)
    y = _as_series(cop_y)
    if x.size != y.size:
        raise ValueError("COP axes must have the same length.")
    if fs_hz <= 0:
        raise ValueError("Sampling frequency must be positive.")
    step = np.hypot(np.diff(x), np.diff(y))
    elapsed = (x.size - 1) / float(fs_hz)
    return float(step.sum() / elapsed)


def axis_mean_velocity(cop: np.ndarray, fs_hz: float) -> float:
    """Mean absolute step on one axis, divided by elapsed time."""
    x = _as_series(cop)
    if fs_hz <= 0:
        raise ValueError("Sampling frequency must be positive.")
    elapsed = (x.size - 1) / float(fs_hz)
    return float(np.abs(np.diff(x)).sum() / elapsed)


def ellipse_area_95(cop_x: np.ndarray, cop_y: np.ndarray) -> float:
    """Area of the 95% prediction ellipse, in the squared unit of the inputs.

    For unbiased covariance S and sample size n, the ellipse constant is
    c = 2 * (n - 1) / (n - 2) * F(0.95; 2, n - 2), and the area is
    pi * c * sqrt(det S).
    """
    x = _as_series(cop_x)
    y = _as_series(cop_y)
    if x.size != y.size:
        raise ValueError("COP axes must have the same length.")
    n = int(x.size)
    covariance = np.cov(x, y, ddof=1)
    determinant = float(np.linalg.det(covariance))
    if determinant < 0:
        if determinant > -1e-8:
            determinant = 0.0
        else:
            raise ValueError("Covariance determinant is negative.")
    f_critical = float(stats.f.ppf(0.95, 2, n - 2))
    constant = 2.0 * (n - 1) / (n - 2) * f_critical
    return float(np.pi * constant * np.sqrt(determinant))


def cop_step_and_range(cop_x: np.ndarray, cop_y: np.ndarray) -> dict[str, float]:
    x = _as_series(cop_x)
    y = _as_series(cop_y)
    if x.size != y.size:
        raise ValueError("COP axes must have the same length.")
    step = np.hypot(np.diff(x), np.diff(y))
    return {
        "max_step_cm": float(step.max()),
        "range_ap_cm": float(x.max() - x.min()),
        "range_ml_cm": float(y.max() - y.min()),
    }


def trial_cop_metrics(cop_x: np.ndarray, cop_y: np.ndarray, fs_hz: float) -> dict[str, float]:
    metrics = {
        "mv_cm_s": resultant_mean_velocity(cop_x, cop_y, fs_hz),
        "mv_ap_cm_s": axis_mean_velocity(cop_x, fs_hz),
        "mv_ml_cm_s": axis_mean_velocity(cop_y, fs_hz),
        "ellipse_cm2": ellipse_area_95(cop_x, cop_y),
    }
    metrics.update(cop_step_and_range(cop_x, cop_y))
    return metrics
