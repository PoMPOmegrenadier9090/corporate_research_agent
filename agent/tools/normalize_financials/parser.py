"""
Shared helpers for normalizing financial value strings.
"""

from __future__ import annotations

import re

_EMPTY_MARKERS = {
    "",
    "-",
    "--",
    "―",
    "－",
    "—",
    "赤字",
    "N/A",
    "n/a",
}

_UNIT_MULTIPLIERS = {
    "兆円": 1_000_000_000_000.0,
    "億円": 100_000_000.0,
    "万円": 10_000.0,
    "千円": 1_000.0,
    "百万円": 1_000_000.0,
    "百万": 1_000_000.0,
    "円": 1.0,
    "兆": 1_000_000_000_000.0,
    "億": 100_000_000.0,
    "万": 10_000.0,
    "千": 1_000.0,
    "百": 100.0,
}

_UNIT_PATTERN = "|".join(sorted((re.escape(unit) for unit in _UNIT_MULTIPLIERS), key=len, reverse=True))
_AMOUNT_PATTERN = re.compile(rf"([\d,.]+)\s*({_UNIT_PATTERN})")


def parse_financial_value(text: str | None):
    """Normalize a raw financial string into a base numeric value.

    Amounts are converted into yen.
    Percentages are converted into decimal ratios.
    Unknown or empty values return ``None``.
    """

    if text is None:
        return None

    text = str(text)
    text = (
        text.replace("\u2009", "")
        .replace("\u2003", "")
        .replace("\u3000", "")
        .replace("−", "-")
        .replace("－", "-")
        .strip()
    )

    if text in _EMPTY_MARKERS:
        return None

    is_negative = False
    if text.startswith("-") or text.startswith("▲"):
        is_negative = True
        text = text[1:].strip()

    if not text or text in _EMPTY_MARKERS:
        return None

    if "％" in text or "%" in text:
        try:
            val = float(text.replace("％", "").replace("%", "").replace(",", "").strip()) / 100.0
            return -val if is_negative else val
        except ValueError:
            return None

    if any(unit in text for unit in _UNIT_MULTIPLIERS):
        total = 0.0
        matched = False
        for match in _AMOUNT_PATTERN.finditer(text):
            num_str, unit = match.groups()
            try:
                num = float(num_str.replace(",", ""))
            except ValueError:
                continue
            matched = True
            total += num * _UNIT_MULTIPLIERS[unit]

        if matched:
            return -total if is_negative else total

    try:
        val = float(text.replace(",", ""))
        return -val if is_negative else val
    except ValueError:
        return None