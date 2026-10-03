"""Small, conservative guard for LLM prose containing business numbers."""
from __future__ import annotations

import re

_DEVANAGARI = str.maketrans("०१२३४५६७८९", "0123456789")


def numbers(text: object) -> set[str]:
    """Return normalised decimal tokens found in text (currency/comma agnostic)."""
    found = re.findall(r"(?<![\w.])\d+(?:,\d{3})*(?:\.\d+)?", str(text).translate(_DEVANAGARI))
    result = set()
    for value in found:
        value = value.replace(",", "")
        try:
            value = ("%.10f" % float(value)).rstrip("0").rstrip(".")
        except ValueError:
            pass
        result.add(value)
    return result


def is_grounded(output: str, *sources: object) -> bool:
    allowed: set[str] = set()
    for source in sources:
        allowed |= numbers(source)
    return numbers(output) <= allowed
