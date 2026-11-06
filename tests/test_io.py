"""WFDB round trip and one real HBEDB record when the local download is present."""

from pathlib import Path

import numpy as np
import pytest

from hbedb_sway.io_wfdb import read_recording, signed_checksum
from hbedb_sway.metrics import resultant_mean_velocity
from hbedb_sway.qc import metrics_from_physical, quality_flags

ROOT = Path(__file__).resolve().parents[1]
REAL_RECORD = ROOT / "data" / "raw" / "BDS00001"


def _write_triangle(directory: Path, name: str, step: float, n: int = 6000, fs: float = 100.0) -> None:
    increments = np.where((np.arange(n - 1) // 50) % 2 == 0, step, -step)
    cop_y = np.cumsum(np.concatenate([[0.0], increments]))
    force_z = np.full(n, 700.0)
    physical = np.column_stack(
        [
            np.zeros(n),
            np.zeros(n),
            force_z,
            cop_y / 100.0 * 700.0,
            np.zeros(n),
            np.zeros(n),
            np.zeros(n),
            cop_y,
        ]
    )
    gain = 100000.0
    digital = np.rint(physical * gain).astype("<i4")
    digital.tofile(directory / f"{name}.dat")
    names = ["Fx", "Fy", "Fz", "Mx", "My", "Mz", "COPx", "COPy"]
    units = ["N", "N", "N", "Nm", "Nm", "Nm", "cm", "cm"]
    lines = [f"{name} 8 {fs:.0f} {n}", "#Subject:7", "#Age:30.0", "#Gender:F", "#Height:170.0", "#Weight:71.38"]
    # Insert signal lines before comments by rebuilding in header order.
    signal_lines = []
    for index, channel in enumerate(names):
        checksum = signed_checksum(digital[:, index])
        initial = int(digital[0, index])
        signal_lines.append(
            f"{name}.dat 32 {gain:.1f}(0)/{units[index]} 0 0 {initial} {checksum} 0 {channel}"
        )
    text = "\n".join([lines[0], *signal_lines, *lines[1:]]) + "\n"
    (directory / f"{name}.hea").write_text(text, encoding="utf-8")


def test_round_trip_preserves_velocity_checksum_and_cop(tmp_path):
    _write_triangle(tmp_path, "SYN0001", step=0.01)
    recording = read_recording(tmp_path / "SYN0001")
    assert recording.checksum_ok
    assert recording.initial_ok
    assert recording.header_subject == "7"
    speed = resultant_mean_velocity(recording.physical["COPx"], recording.physical["COPy"], recording.fs_hz)
    assert abs(speed - 1.0) < 1e-4
    metrics = metrics_from_physical(
        recording.physical,
        fs_hz=recording.fs_hz,
        n_samples=recording.n_samples,
        weight_kg=700.0 / 9.80665,
        checksum_ok=True,
        initial_ok=True,
        subject_id_mismatch=False,
    )
    assert quality_flags(metrics) == []
    assert metrics["cop_recon_cm"] < 1e-3


@pytest.mark.skipif(not REAL_RECORD.with_suffix(".dat").exists(), reason="HBEDB files are not downloaded")
def test_first_public_record_matches_the_source_cop_formula():
    recording = read_recording(REAL_RECORD)
    assert recording.n_samples == 6000
    assert recording.fs_hz == 100.0
    assert recording.checksum_ok
    assert recording.initial_ok
    metrics = metrics_from_physical(
        recording.physical,
        fs_hz=recording.fs_hz,
        n_samples=recording.n_samples,
        weight_kg=54.2,
        checksum_ok=True,
        initial_ok=True,
        subject_id_mismatch=False,
    )
    assert metrics["cop_recon_cm"] < 1e-4
    assert 0.2 < metrics["mv_cm_s"] < 2.0
    assert 0.9 < metrics["fz_ratio"] < 1.1
