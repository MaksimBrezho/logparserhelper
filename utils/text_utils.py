import re
from typing import List, Dict


def common_prefix(words):
    if not words:
        return ''
    prefix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(prefix), len(w))
        while i < max_i and prefix[i] == w[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def common_suffix(words):
    if not words:
        return ''
    suffix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(suffix), len(w))
        while i < max_i and suffix[-1 - i] == w[-1 - i]:
            i += 1
        suffix = suffix[len(suffix)-i:]
        if not suffix:
            break
    return suffix


def count_significant_chars(text: str) -> int:
    """Return the length of text excluding any whitespace characters."""
    return len("".join(ch for ch in text if not ch.isspace()))


def compute_char_coverage(
    logs: List[str], matches_by_line: Dict[int, List[Dict]], active_names: set
) -> float:
    """Calculate coverage by number of significant characters.

    Parameters
    ----------
    logs : List[str]
        Source log lines.
    matches_by_line : Dict[int, List[Dict]]
        Mapping of line number to list of match dictionaries.
    active_names : set
        Names of patterns that should be counted in coverage.

    Returns
    -------
    float
        Coverage percentage from 0 to 100.
    """
    total = sum(count_significant_chars(line) for line in logs)
    if total == 0:
        return 0.0

    covered = 0
    for lineno, matches in matches_by_line.items():
        ranges = []
        for m in matches:
            if m.get("name") not in active_names:
                continue
            start = m.get("start")
            end = m.get("end")
            if start is None or end is None:
                start = 0
                end = len(m.get("match", ""))
            ranges.append((start, end))

        if not ranges:
            continue

        ranges.sort()
        merged = [list(ranges[0])]
        for start, end in ranges[1:]:
            last = merged[-1]
            if start <= last[1]:
                last[1] = max(last[1], end)
            else:
                merged.append([start, end])

        line_text = logs[lineno - 1] if 0 < lineno <= len(logs) else ""
        for start, end in merged:
            segment = line_text[start:end]
            covered += count_significant_chars(segment)

    return covered / total * 100
