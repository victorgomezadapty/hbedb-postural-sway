#!/usr/bin/env python3
"""Run the subject-level HBEDB analysis and write tables, figures, and RESULTS.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hbedb_sway.pipeline import run_analysis  # noqa: E402


def main() -> None:
    run_analysis(ROOT / "data" / "raw", ROOT / "outputs", results_path=ROOT / "RESULTS.md")


if __name__ == "__main__":
    main()
