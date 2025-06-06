"""Simple transformation helpers for CEF field values."""

from __future__ import annotations

import re
from typing import Any, Dict


def _apply_basic_transform(value: str, transform: str) -> str:
    """Apply a basic string transformation."""
    if value is None:
        value = ""
    if transform == "lower":
        return value.lower()
    if transform == "upper":
        return value.upper()
    if transform == "capitalize":
        return value.capitalize()
    if transform == "sentence":
        return value[:1].upper() + value[1:].lower() if value else value
    return value


def apply_transform(value: str, transform: Any) -> str:
    """Apply a basic or advanced transformation."""
    if isinstance(transform, dict):
        fmt = transform.get("format", "none")
        if transform.get("replace_pattern"):
            pat = re.compile(transform["replace_pattern"])
            if pat.fullmatch(value or ""):
                value = transform.get("replace_with", "")
        if transform.get("value_map"):
            mapping: Dict[str, str] = transform["value_map"]
            if value in mapping:
                value = mapping[value]
            else:
                for k, v in mapping.items():
                    if k in (value or ""):
                        value = (value or "").replace(k, v)
        return _apply_basic_transform(value, fmt)
    return _apply_basic_transform(value, str(transform))



