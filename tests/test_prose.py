"""Documentation stays free of em dashes, en dashes, and unicode minus signs."""

import re
from pathlib import Path

from hbedb_sway.punctuation import LONG_DASHES, assert_plain_prose, strip_code_fences

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md",
    ROOT / "DATA_LICENSE.md",
    ROOT / "LICENSE",
    ROOT / "RESULTS.md",
]


def test_helper_rejects_long_dashes():
    try:
        assert_plain_prose("A long dash \u2014 is not allowed.")
    except ValueError:
        return
    raise AssertionError("An em dash was accepted.")


def test_project_documents_use_plain_punctuation():
    for path in DOCUMENTS:
        if not path.exists():
            continue
        text = strip_code_fences(path.read_text(encoding="utf-8"))
        for character in LONG_DASHES:
            assert character not in text, f"{path.name} contains a long dash"
        prose_lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("|") and set(stripped) <= set("|-: "):
                continue
            prose_lines.append(line)
        outside_identifiers = re.sub(r"`[^`]+`", "", "\n".join(prose_lines))
        assert "--" not in outside_identifiers, f"{path.name} contains a double hyphen outside code"
