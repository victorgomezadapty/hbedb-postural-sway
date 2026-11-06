"""Reject em dashes, en dashes, and unicode minus signs in prose."""

from __future__ import annotations

import re

LONG_DASHES = ("\u2014", "\u2013", "\u2212")


def strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def assert_plain_prose(text: str, *, allow_double_hyphen: bool = False) -> None:
    """Raise if prose uses a long dash or, unless allowed, a double hyphen.

    Markdown table rules are three hyphens inside a table row. Those rules are
    removed before the double-hyphen check so a separator is not mistaken for
    prose punctuation.
    """
    for character in LONG_DASHES:
        if character in text:
            raise ValueError("Prose contains an em dash, en dash, or unicode minus.")
    if allow_double_hyphen:
        return
    without_table_rules = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and set(stripped) <= set("|-: "):
            continue
        without_table_rules.append(line)
    if "--" in "\n".join(without_table_rules):
        raise ValueError("Prose contains a double hyphen.")
