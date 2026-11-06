#!/usr/bin/env python3
"""Download HBEDB v1.0.0 into data/raw. Does not commit the files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hbedb_sway.download import download_hbedb  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Download HBEDB v1.0.0 for local analysis.")
    parser.add_argument("--dest", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args()
    download_hbedb(args.dest, workers=args.workers)


if __name__ == "__main__":
    main()
