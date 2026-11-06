"""Known-signal checks for COP velocity and the prediction ellipse."""

import numpy as np
from scipy import stats

from hbedb_sway.metrics import axis_mean_velocity, ellipse_area_95, resultant_mean_velocity


def test_constant_step_velocity_is_exact():
    fs = 100.0
    step = 0.01
    n = 6000
    increments = np.where((np.arange(n - 1) // 50) % 2 == 0, step, -step)
    y = np.cumsum(np.concatenate([[0.0], increments]))
    x = np.zeros(n)
    assert abs(resultant_mean_velocity(x, y, fs) - step * fs) < 1e-12
    assert abs(axis_mean_velocity(y, fs) - step * fs) < 1e-12
    assert axis_mean_velocity(x, fs) == 0.0


def test_diagonal_velocity_is_the_hypotenuse():
    fs = 100.0
    n = 1000
    t = np.arange(n) / fs
    x = t * 3.0
    y = t * 4.0
    assert abs(resultant_mean_velocity(x, y, fs) - 5.0) < 1e-9


def test_prediction_ellipse_matches_the_finite_sample_formula():
    rng = np.random.default_rng(2648)
    n = 80_000
    x = rng.normal(0.0, 2.0, n)
    y = rng.normal(5.0, 3.0, n)
    area = ellipse_area_95(x, y)
    covariance = np.cov(x, y, ddof=1)
    constant = 2.0 * (n - 1) / (n - 2) * stats.f.ppf(0.95, 2, n - 2)
    expected = np.pi * constant * np.sqrt(np.linalg.det(covariance))
    assert abs(area - expected) / expected < 1e-10
    # Independent axes: the area should sit near pi * c * 2 * 3.
    rough = np.pi * constant * 6.0
    assert abs(area - rough) / rough < 0.02


def test_collinear_sway_has_zero_area():
    y = np.linspace(-1.0, 1.0, 500)
    x = np.zeros(500)
    assert ellipse_area_95(x, y) == 0.0
