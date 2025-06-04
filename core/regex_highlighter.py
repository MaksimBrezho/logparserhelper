import re
import tkinter as tk
from typing import List, Dict
from utils.color_utils import get_shaded_color


def compute_optimal_matches(line: str, patterns: List[Dict]) -> List[Dict]:
    matches = []
    for pat in patterns:
        regex = pat.get("regex") or pat.get("pattern")
        try:
            compiled = re.compile(regex)
        except re.error:
            continue
        for m in compiled.finditer(line):
            matches.append({
                "start": m.start(),
                "end": m.end(),
                "length": m.end() - m.start(),
                "match": m.group(),
                "category": pat.get("category", "Unknown"),
                "name": pat.get("name", "Unnamed"),
                "source": pat.get("source", "unknown"),
                "regex": regex,
                "priority": pat.get("priority", 1),
            })

    matches.sort(key=lambda m: m["end"])
    n = len(matches)
    dp = [0] * n
    prev = [-1] * n

    def find_last_non_conflicting(i):
        for j in range(i - 1, -1, -1):
            if matches[j]["end"] <= matches[i]["start"]:
                return j
        return -1

    for i in range(n):
        incl = matches[i]["priority"]
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

    # Восстановление
    result = []
    i = n - 1
    while i >= 0:
        if prev[i] == -2:
            i -= 1
        else:
            result.append(matches[i])
            i = prev[i]
    return list(reversed(result))


def find_matches_in_line(line: str, patterns: List[Dict]) -> List[Dict]:
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
