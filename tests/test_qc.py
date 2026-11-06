"""Quality screens use physical bounds, not a vision or surface effect."""

from hbedb_sway.qc import quality_flags, reconstruct_cop_cm
import numpy as np


def _base(**overrides):
    metrics = {
        "readable": True,
        "checksum_ok": True,
        "initial_ok": True,
        "n_samples": 6000,
        "fs_hz": 100.0,
        "missing_channel": False,
        "subject_id_mismatch": False,
        "finite": True,
        "body_mass_ok": True,
        "fz_ratio": 1.0,
        "fz_min_n": 400.0,
        "cop_recon_cm": 0.0001,
        "max_step_cm": 0.05,
        "mv_cm_s": 1.0,
        "range_ap_cm": 2.0,
        "range_ml_cm": 1.5,
    }
    metrics.update(overrides)
    return metrics


def test_clean_trial_is_kept():
    assert quality_flags(_base()) == []


def test_force_and_step_boundaries():
    assert "fz_ratio" in quality_flags(_base(fz_ratio=0.749))
    assert "fz_ratio" not in quality_flags(_base(fz_ratio=0.75))
    assert "fz_ratio" in quality_flags(_base(fz_ratio=1.251))
    assert "fz_dropout" in quality_flags(_base(fz_min_n=49.9))
    assert "step_artifact" in quality_flags(_base(max_step_cm=2.01))
    assert "step_artifact" not in quality_flags(_base(max_step_cm=2.0))
    assert "speed_out_of_range" in quality_flags(_base(mv_cm_s=20.01))
    assert "range_too_large" in quality_flags(_base(range_ap_cm=25.01))
    assert quality_flags(_base(readable=False)) == ["unreadable"]
    assert "nonfinite_signal" in quality_flags(_base(finite=False))


def test_reconstruction_uses_the_source_formulas():
    force_z = np.array([500.0, 500.0])
    moment_x = np.array([5.0, -2.5])
    moment_y = np.array([-10.0, 1.0])
    cop_x, cop_y = reconstruct_cop_cm(force_z, moment_x, moment_y)
    assert np.allclose(cop_x, -moment_y / force_z * 100.0)
    assert np.allclose(cop_y, moment_x / force_z * 100.0)
    assert abs(cop_x[0] - 2.0) < 1e-12
    assert abs(cop_y[0] - 1.0) < 1e-12
