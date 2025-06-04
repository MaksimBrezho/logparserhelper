import re
import tkinter as tk
from typing import List, Dict, Tuple
from utils.color_utils import get_shaded_color


def compute_optimal_matches(line: str, patterns: List[Dict]) -> List[Dict]:
    """Find optimal non-overlapping matches.

    User patterns from the current log (marked with ``source='log'``) may
    overlap with each other, but they must not intersect with built-in or
    global user patterns. Built-in and global patterns remain mutually
    exclusive based on their priority.
    """

    all_matches = []
    for pat in patterns:
        regex = pat.get("regex") or pat.get("pattern")
        try:
            compiled = re.compile(regex)
        except re.error:
            continue
        for m in compiled.finditer(line):
            all_matches.append({
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

    # per-log паттерны могут перекрываться только между собой
    log_allowed = [m for m in all_matches if m.get("source") == "log"]
    base_matches = [m for m in all_matches if m.get("source") != "log"]

    base_matches.sort(key=lambda m: m["end"])
    n = len(base_matches)
    dp = [0] * n
    prev = [-1] * n

    def find_last_non_conflicting(i: int) -> int:
        for j in range(i - 1, -1, -1):
            if base_matches[j]["end"] <= base_matches[i]["start"]:
                return j
        return -1

    for i in range(n):
        incl = base_matches[i]["priority"]
        j = find_last_non_conflicting(i)
        if j != -1:
            incl += dp[j]
        excl = dp[i - 1] if i > 0 else 0
        if incl > excl:
            dp[i] = incl
            prev[i] = j
        else:
            dp[i] = excl
            prev[i] = -2  # skip this match

    result = []
    i = n - 1
    while i >= 0:
        if prev[i] == -2:
            i -= 1
        else:
            result.append(base_matches[i])
            i = prev[i]
    result = list(reversed(result))

    # добавляем лог‑специфичные совпадения, если они не пересекаются с базовыми
    filtered_logs = []
    for m in log_allowed:
        if all(m["end"] <= b["start"] or m["start"] >= b["end"] for b in result):
            filtered_logs.append(m)

    result.extend(filtered_logs)
    result.sort(key=lambda m: (m["start"], m["end"]))
    return result


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

    tag_order: Dict[str, int] = {}
    order_counter = 0

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
        active_matches = [m for m in matches if m["name"] in active_names]

        for m in active_matches:
            key = (m["category"], m["regex"])
            idx = pattern_index_map.get(key, 0)
            base_color = color_map.get(m["category"], "black")
            shaded = get_shaded_color(base_color, idx, total)

            tag = f"{m['category']}_{m['regex']}"
            if tag not in text_widget.tag_names():
                text_widget.tag_config(tag, background=shaded)
                text_widget.tag_lower(tag)
                tag_order[tag] = order_counter
                order_counter += 1

            start_idx = f"{lineno}.{m['start']}"
            end_idx = f"{lineno}.{m['end']}"
            text_widget.tag_add(tag, start_idx, end_idx)

        # выделим области перекрытия
        ranges: List[Tuple[int, int]] = [(m["start"], m["end"]) for m in active_matches]
        overlaps: List[Tuple[int, int]] = []
        points = []
        for s, e in ranges:
            points.append((s, 1))
            points.append((e, -1))
        points.sort()
        count = 0
        overlap_start = None
        for pos, delta in points:
            prev = count
            count += delta
            if prev < 2 and count >= 2:
                overlap_start = pos
            elif prev >= 2 and count < 2 and overlap_start is not None:
                overlaps.append((overlap_start, pos))
                overlap_start = None

        if "overlap" not in text_widget.tag_names():
            text_widget.tag_config("overlap", underline=True)

        for s, e in overlaps:
            text_widget.tag_add("overlap", f"{lineno}.{s}", f"{lineno}.{e}")

    for tag in sorted(tag_order, key=tag_order.get):
        text_widget.tag_raise(tag)

    if "overlap" in text_widget.tag_names():
        text_widget.tag_raise("overlap")

    return tag_order
