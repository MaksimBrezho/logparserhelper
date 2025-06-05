"""Simple transformation helpers for CEF field values."""

from typing import Any


def apply_transform(value: str, transform: str) -> str:
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


