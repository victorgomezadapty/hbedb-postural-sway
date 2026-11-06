"""Pre-specified trial quality screens.

A trial is excluded when a screen fails. Screens look for broken files,
unphysiological vertical force, COP that disagrees with the force and moment
channels, and single-sample jumps that a 10 Hz filtered quiet-stance signal
does not produce. They do not use the vision or surface coefficient.
"""

from __future__ import annotations

import numpy as np

from hbedb_sway.constants import (
    COP_RECON_MAX_CM,
    FS_HZ,
    FZ_MIN_N,
    FZ_RATIO_MAX,
    FZ_RATIO_MIN,
    GRAVITY_MPS2,
    MAX_STEP_CM,
    N_SAMPLES,
    RANGE_MAX_CM,
    SPEED_MAX_CM_S,
    SPEED_MIN_CM_S,
)
from hbedb_sway.metrics import trial_cop_metrics

REASON_LABELS = {
    "checksum_mismatch": "WFDB checksum or initial-value mismatch",
    "bad_length": "Recording length was not 6,000 samples",
    "bad_sampling_rate": "Sampling rate was not 100 Hz",
    "nonfinite_signal": "Force or COP channel was not finite",
    "missing_channel": "A required channel was missing",
    "subject_id_mismatch": "Header subject id did not match BDSinfo",
    "bad_body_mass": "Body mass was missing or not positive",
    "fz_ratio": "Mean vertical force was outside 75% to 125% of body weight",
    "fz_dropout": "A sample of vertical force fell below 50 N",
    "cop_reconstruction": "Stored COP disagreed with moments and vertical force",
    "step_artifact": "A sample-to-sample COP step exceeded 2 cm",
    "speed_out_of_range": "Resultant mean velocity was outside 0.05 to 20 cm/s",
    "range_too_large": "COP range exceeded 25 cm on one axis",
    "unreadable": "Recording could not be read",
}


def reconstruct_cop_cm(force_z: np.ndarray, moment_x: np.ndarray, moment_y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Santos and Duarte formulas, converted from meters to centimeters.

    COPx = -My / Fz and COPy = Mx / Fz when moments are in N*m and force is in N.
    """
    force = np.asarray(force_z, dtype=float)
    cop_x = -np.asarray(moment_y, dtype=float) / force * 100.0
    cop_y = np.asarray(moment_x, dtype=float) / force * 100.0
    return cop_x, cop_y


def quality_flags(metrics: dict[str, object]) -> list[str]:
    """Return exclusion reasons. An empty list means the trial is kept."""
    flags: list[str] = []
    if not bool(metrics.get("readable", False)):
        return ["unreadable"]
    if not bool(metrics.get("checksum_ok", False)) or not bool(metrics.get("initial_ok", False)):
        flags.append("checksum_mismatch")
    if int(metrics["n_samples"]) != N_SAMPLES:
        flags.append("bad_length")
    if abs(float(metrics["fs_hz"]) - FS_HZ) > 1e-6:
        flags.append("bad_sampling_rate")
    if bool(metrics.get("missing_channel", False)):
        flags.append("missing_channel")
    if bool(metrics.get("subject_id_mismatch", False)):
        flags.append("subject_id_mismatch")
    if not bool(metrics.get("finite", False)):
        flags.append("nonfinite_signal")
        return flags
    if not bool(metrics.get("body_mass_ok", False)):
        flags.append("bad_body_mass")
        return flags
    fz_ratio = float(metrics["fz_ratio"])
    if fz_ratio < FZ_RATIO_MIN or fz_ratio > FZ_RATIO_MAX:
        flags.append("fz_ratio")
    if float(metrics["fz_min_n"]) < FZ_MIN_N:
        flags.append("fz_dropout")
    if float(metrics["cop_recon_cm"]) > COP_RECON_MAX_CM:
        flags.append("cop_reconstruction")
    if float(metrics["max_step_cm"]) > MAX_STEP_CM:
        flags.append("step_artifact")
    speed = float(metrics["mv_cm_s"])
    if speed < SPEED_MIN_CM_S or speed > SPEED_MAX_CM_S:
        flags.append("speed_out_of_range")
    if float(metrics["range_ap_cm"]) > RANGE_MAX_CM or float(metrics["range_ml_cm"]) > RANGE_MAX_CM:
        flags.append("range_too_large")
    return flags


def metrics_from_physical(
    physical: dict[str, np.ndarray],
    *,
    fs_hz: float,
    n_samples: int,
    weight_kg: float,
    checksum_ok: bool,
    initial_ok: bool,
    subject_id_mismatch: bool,
) -> dict[str, object]:
    required = ("Fz", "Mx", "My", "COPx", "COPy")
    missing = any(name not in physical for name in required)
    base: dict[str, object] = {
        "readable": True,
        "checksum_ok": checksum_ok,
        "initial_ok": initial_ok,
        "n_samples": n_samples,
        "fs_hz": fs_hz,
        "missing_channel": missing,
        "subject_id_mismatch": subject_id_mismatch,
        "finite": False,
        "body_mass_ok": bool(np.isfinite(weight_kg) and weight_kg > 0),
        "fz_mean_n": np.nan,
        "fz_min_n": np.nan,
        "fz_ratio": np.nan,
        "cop_recon_cm": np.nan,
        "mv_cm_s": np.nan,
        "mv_ap_cm_s": np.nan,
        "mv_ml_cm_s": np.nan,
        "ellipse_cm2": np.nan,
        "max_step_cm": np.nan,
        "range_ap_cm": np.nan,
        "range_ml_cm": np.nan,
    }
    if missing:
        return base
    force_z = np.asarray(physical["Fz"], dtype=float)
    moment_x = np.asarray(physical["Mx"], dtype=float)
    moment_y = np.asarray(physical["My"], dtype=float)
    cop_x = np.asarray(physical["COPx"], dtype=float)
    cop_y = np.asarray(physical["COPy"], dtype=float)
    finite = bool(
        np.isfinite(force_z).all()
        and np.isfinite(moment_x).all()
        and np.isfinite(moment_y).all()
        and np.isfinite(cop_x).all()
        and np.isfinite(cop_y).all()
    )
    base["finite"] = finite
    if not finite:
        return base
    expected_weight = float(weight_kg) * GRAVITY_MPS2 if base["body_mass_ok"] else np.nan
    fz_mean = float(np.mean(np.abs(force_z)))
    base["fz_mean_n"] = fz_mean
    base["fz_min_n"] = float(np.min(np.abs(force_z)))
    base["fz_ratio"] = float(fz_mean / expected_weight) if expected_weight and expected_weight > 0 else np.nan
    if np.any(np.abs(force_z) < 1.0):
        base["cop_recon_cm"] = np.inf
    else:
        hat_x, hat_y = reconstruct_cop_cm(force_z, moment_x, moment_y)
        recon = max(
            float(np.median(np.abs(cop_x - hat_x))),
            float(np.median(np.abs(cop_y - hat_y))),
        )
        base["cop_recon_cm"] = recon
    try:
        base.update(trial_cop_metrics(cop_x, cop_y, fs_hz))
    except ValueError:
        base["finite"] = False
    return base
