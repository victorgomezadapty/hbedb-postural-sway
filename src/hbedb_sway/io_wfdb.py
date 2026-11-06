"""Minimal reader for the HBEDB WFDB format-32 recordings.

The PhysioNet files store eight multiplexed little-endian int32 channels in
one .dat file. Physical values are (digital - baseline) / gain, which is the
WFDB conversion. Channel checksums use the signed 16-bit sum of samples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

_SIGNAL_LINE = re.compile(
    r"^(?P<file>\S+)\s+"
    r"(?P<fmt>\d+)\s+"
    r"(?P<gain>[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"(?:\((?P<baseline>[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\))?/"
    r"(?P<units>\S+)\s+"
    r"\S+\s+\S+\s+"
    r"(?P<initial>[+-]?\d+)\s+"
    r"(?P<checksum>[+-]?\d+)\s+"
    r"\S+\s+"
    r"(?P<name>\S+)\s*$"
)

_HEADER_FIELDS = ("subject", "age", "gender", "height", "weight")


@dataclass
class Recording:
    name: str
    fs_hz: float
    n_samples: int
    physical: dict[str, np.ndarray]
    checksum_ok: bool
    initial_ok: bool
    header_subject: str | None
    header_age: float | None
    header_gender: str | None
    header_height: float | None
    header_weight: float | None


def signed_checksum(samples: np.ndarray) -> int:
    total = int(np.asarray(samples, dtype=np.int64).sum())
    remainder = total % 65536
    if remainder >= 32768:
        remainder -= 65536
    return int(remainder)


def _parse_header(text: str) -> tuple[str, float, int, list[dict[str, object]], dict[str, str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("Empty WFDB header.")
    parts = lines[0].split()
    if len(parts) < 4:
        raise ValueError(f"Unreadable WFDB header line: {lines[0]}")
    name = parts[0]
    n_signals = int(parts[1])
    fs_hz = float(parts[2])
    n_samples = int(parts[3])
    signals: list[dict[str, object]] = []
    header_fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.startswith("#"):
            key, _, value = line[1:].partition(":")
            key = key.strip().lower()
            if key in _HEADER_FIELDS:
                header_fields[key] = value.strip()
            continue
        match = _SIGNAL_LINE.match(line)
        if match is None:
            raise ValueError(f"Unreadable WFDB signal line: {line}")
        signals.append(
            {
                "fmt": int(match.group("fmt")),
                "gain": float(match.group("gain")),
                "baseline": float(match.group("baseline") or 0.0),
                "initial": int(match.group("initial")),
                "checksum": int(match.group("checksum")),
                "name": str(match.group("name")),
            }
        )
    if len(signals) != n_signals:
        raise ValueError(
            f"{name}: header declares {n_signals} signals but {len(signals)} were parsed."
        )
    return name, fs_hz, n_samples, signals, header_fields


def _optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def read_recording(path: Path) -> Recording:
    """Read one HBEDB record from its header path or from the record stem."""
    path = Path(path)
    header_path = path if path.suffix == ".hea" else path.with_suffix(".hea")
    data_path = header_path.with_suffix(".dat")
    name, fs_hz, n_samples, signals, fields = _parse_header(header_path.read_text(encoding="utf-8"))
    if any(int(signal["fmt"]) != 32 for signal in signals):
        raise ValueError(f"{name}: only format 32 is implemented.")
    n_signals = len(signals)
    digital = np.fromfile(data_path, dtype="<i4")
    expected = n_signals * n_samples
    if digital.size != expected:
        raise ValueError(f"{name}: expected {expected} samples, found {digital.size}.")
    digital = digital.reshape(n_samples, n_signals)
    baselines = np.array([signal["baseline"] for signal in signals], dtype=float)
    gains = np.array([signal["gain"] for signal in signals], dtype=float)
    if np.any(gains == 0):
        raise ValueError(f"{name}: a channel gain is zero.")
    physical_matrix = (digital.astype(np.float64) - baselines) / gains
    checksum_ok = True
    initial_ok = True
    physical: dict[str, np.ndarray] = {}
    for index, signal in enumerate(signals):
        if signed_checksum(digital[:, index]) != int(signal["checksum"]):
            checksum_ok = False
        if int(digital[0, index]) != int(signal["initial"]):
            initial_ok = False
        physical[str(signal["name"])] = physical_matrix[:, index]
    return Recording(
        name=name,
        fs_hz=fs_hz,
        n_samples=n_samples,
        physical=physical,
        checksum_ok=checksum_ok,
        initial_ok=initial_ok,
        header_subject=fields.get("subject"),
        header_age=_optional_float(fields.get("age")),
        header_gender=fields.get("gender"),
        header_height=_optional_float(fields.get("height")),
        header_weight=_optional_float(fields.get("weight")),
    )
