import re
import tkinter as tk
from typing import List, Dict
from utils.color_utils import get_shaded_color


def compute_optimal_matches(line: str, patterns: List[Dict]) -> List[Dict]:
    """Return optimal non-overlapping matches for the given line.

    Parameters
    ----------
    line : str
        Line to analyse.
    patterns : list[dict]
        Patterns loaded from ``json_utils``. Three classes are supported:

        ``builtin``
            Patterns shipped with the application.
        ``user``
            Patterns created by the user and applied globally.
        ``log``
            Patterns tied to a specific log file.

    Notes
    -----
    All matches produced by ``log`` patterns are kept. Matches from ``builtin``
    and ``user`` patterns that intersect these log-specific matches are
    discarded. The weighted selection algorithm is then applied only to the
    remaining matches to avoid overlaps and maximise the sum of their
    ``priority`` values.
    """

    log_matches: List[Dict] = []
    other_matches: List[Dict] = []

    for pat in patterns:
        regex = pat.get("regex") or pat.get("pattern")
        try:
            compiled = re.compile(regex)
        except re.error:
            continue
        for m in compiled.finditer(line):
            entry = {
                "start": m.start(),
                "end": m.end(),
                "length": m.end() - m.start(),
                "match": m.group(),
                "category": pat.get("category", "Unknown"),
                "name": pat.get("name", "Unnamed"),
                "source": pat.get("source", "unknown"),
                "regex": regex,
                "priority": pat.get("priority", 1),
            }
            if entry["source"] == "log":
                log_matches.append(entry)
            else:
                other_matches.append(entry)

    def _overlap(a: Dict, b: Dict) -> bool:
        return not (a["end"] <= b["start"] or a["start"] >= b["end"])

    filtered_other = [
        m for m in other_matches
        if not any(_overlap(m, lm) for lm in log_matches)
    ]

    filtered_other.sort(key=lambda m: m["end"])
    n = len(filtered_other)
    dp = [0] * n
    prev = [-1] * n

    def find_last_non_conflicting(i: int) -> int:
        for j in range(i - 1, -1, -1):
            if filtered_other[j]["end"] <= filtered_other[i]["start"]:
                return j
        return -1

    for i in range(n):
        incl = filtered_other[i]["priority"]
        j = find_last_non_conflicting(i)
        if j != -1:
            incl += dp[j]
        excl = dp[i - 1] if i > 0 else 0
        if incl > excl:
            dp[i] = incl
            prev[i] = j
        else:
            dp[i] = excl
            prev[i] = -2  # special marker: skip this match

    result: List[Dict] = []
    i = n - 1
    while i >= 0:
        if prev[i] == -2:
            i -= 1
        else:
            result.append(filtered_other[i])
            i = prev[i]

    result.extend(log_matches)
    return sorted(result, key=lambda m: m["start"])


def find_matches_in_line(line: str, patterns: List[Dict]) -> List[Dict]:
    """Convenience wrapper around :func:`compute_optimal_matches`."""
    return compute_optimal_matches(line, patterns)


def apply_highlighting(
    text_widget,
    matches_by_line: Dict[int, List[Dict]],
    active_names: set,
    color_map: Dict[str, str]
):
    for tag in text_widget.tag_names():
        text_widget.tag_remove(tag, "1.0", tk.END)
        try:
            text_widget.tag_delete(tag)
        except tk.TclError:
            pass

    pattern_keys = []
    seen = set()
    for matches in matches_by_line.values():
        for m in matches:
            key = (m["category"], m["regex"])
            if key not in seen:
                pattern_keys.append(key)
                seen.add(key)

    pattern_index_map = {key: i for i, key in enumerate(pattern_keys)}
    total = len(pattern_keys) or 1

    for lineno, matches in matches_by_line.items():
        for m in matches:
            if m["name"] not in active_names:
                continue

            key = (m["category"], m["regex"])
            idx = pattern_index_map.get(key, 0)
            base_color = color_map.get(m["category"], "black")
            shaded = get_shaded_color(base_color, idx, total)

            tag = f"{m['category']}_{m['regex']}"
            if tag not in text_widget.tag_names():
                text_widget.tag_config(tag, background=shaded)

            start_idx = f"{lineno}.{m['start']}"
            end_idx = f"{lineno}.{m['end']}"
            text_widget.tag_add(tag, start_idx, end_idx)
