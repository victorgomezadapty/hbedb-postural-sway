"""Download HBEDB v1.0.0 for local analysis.

The files stay in the destination directory. This project does not commit them.
The HTTPS base is the public PhysioNet open bucket documented on the dataset
page (s3://physionet-open/hbedb/1.0.0/). The same objects are linked from
https://physionet.org/files/hbedb/1.0.0/.
"""

from __future__ import annotations

import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from hbedb_sway.constants import DATASET_FILES, DATASET_S3_HTTPS, LICENSE_NAME, LICENSE_URI

DAT_BYTES = 192_000


def record_names(records_file: Path) -> list[str]:
    names = [line.strip() for line in records_file.read_text(encoding="utf-8").splitlines()]
    return [name for name in names if name]


def _ready(path: Path, expected_size: int | None) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    if expected_size is None:
        return True
    return path.stat().st_size == expected_size


def _download_one(url: str, dest: Path, expected_size: int | None, retries: int = 5) -> str:
    if _ready(dest, expected_size):
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    temporary = dest.with_name(dest.name + ".part")
    last_error = "unknown error"
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "hbedb-private-research"})
            with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 256)
            if temporary.stat().st_size <= 0:
                raise OSError(f"Empty download for {dest.name}")
            if expected_size is not None and temporary.stat().st_size != expected_size:
                raise OSError(f"{dest.name} has {temporary.stat().st_size} bytes, expected {expected_size}")
            temporary.replace(dest)
            return "ok"
        except Exception as exc:
            last_error = str(exc)
            if temporary.exists():
                temporary.unlink()
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Failed to download {dest.name}: {last_error}")


def download_hbedb(dest: Path, workers: int = 16, base_url: str = DATASET_S3_HTTPS) -> dict[str, int]:
    """Download recordings, headers, BDSinfo.txt, and RECORDS."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    print(
        "Downloading the Human Balance Evaluation Database, version 1.0.0.\n"
        f"Source page: {DATASET_FILES}\n"
        f"File host used here: {base_url}\n"
        f"License stated on the PhysioNet record: {LICENSE_NAME} ({LICENSE_URI}).\n"
        "Raw files are written only under the destination directory and are not committed."
    )
    records_path = dest / "RECORDS"
    info_path = dest / "BDSinfo.txt"
    _download_one(base_url + "RECORDS", records_path, None)
    _download_one(base_url + "BDSinfo.txt", info_path, None)
    names = record_names(records_path)
    jobs: list[tuple[str, Path, int | None]] = []
    for name in names:
        jobs.append((base_url + name + ".dat", dest / f"{name}.dat", DAT_BYTES))
        jobs.append((base_url + name + ".hea", dest / f"{name}.hea", None))

    counts = {"ok": 0, "skip": 0}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for status in pool.map(lambda job: _download_one(*job), jobs):
            counts[status] = counts.get(status, 0) + 1
    dat_count = len(list(dest.glob("BDS*.dat")))
    hea_count = len(list(dest.glob("BDS*.hea")))
    if dat_count != len(names) or hea_count != len(names):
        raise RuntimeError(
            f"Download incomplete: {dat_count} data files and {hea_count} headers for {len(names)} records."
        )
    print(f"Records: {len(names)}. Newly downloaded: {counts.get('ok', 0)}. Already present: {counts.get('skip', 0)}.")
    return {"records": len(names), **counts}
