import re
import tkinter as tk
from typing import List, Dict
from utils.color_utils import get_shaded_color, adjust_lightness


def compute_optimal_matches(line: str, patterns: List[Dict]) -> List[Dict]:
    """Return list of pattern matches following priority rules."""

    builtin = []
    user = []
    per_log = []
    for pat in patterns:
        src = pat.get("source")
        if src in {"per_log", "log"}:
            per_log.append(pat)
        elif src == "user":
            user.append(pat)
        else:
            builtin.append(pat)

    def _collect(pats):
        collected = []
        for pat in pats:
            regex = pat.get("regex") or pat.get("pattern")
            try:
                compiled = re.compile(regex)
            except re.error:
                continue
            for m in compiled.finditer(line):
                collected.append({
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
        return collected

    def _wis(items):
        if not items:
            return []
        items.sort(key=lambda m: m["end"])
        n = len(items)
        dp = [0] * n
        prev = [-1] * n

        def find_last_non_conflicting(i):
            for j in range(i - 1, -1, -1):
                if items[j]["end"] <= items[i]["start"]:
                    return j
            return -1

        for i in range(n):
            incl = items[i]["priority"]
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

        result = []
        i = n - 1
        while i >= 0:
            if prev[i] == -2:
                i -= 1
            else:
                result.append(items[i])
                i = prev[i]
        return list(reversed(result))

    per_log_matches = _collect(per_log)

    intervals = [(m["start"], m["end"]) for m in per_log_matches]

    def _overlaps_any(start: int, end: int) -> bool:
        for s, e in intervals:
            if start < e and end > s:
                return True
        return False

    others_raw = []
    for pat in builtin + user:
        regex = pat.get("regex") or pat.get("pattern")
        try:
            compiled = re.compile(regex)
        except re.error:
            continue
        for m in compiled.finditer(line):
            if _overlaps_any(m.start(), m.end()):
                continue
            priority = pat.get("priority", 1)
            if pat.get("source") == "user":
                priority += 1000
            others_raw.append({
                "start": m.start(),
                "end": m.end(),
                "length": m.end() - m.start(),
                "match": m.group(),
                "category": pat.get("category", "Unknown"),
                "name": pat.get("name", "Unnamed"),
                "source": pat.get("source", "unknown"),
                "regex": regex,
                "priority": priority,
            })

    main_matches = _wis(others_raw)
    all_matches = main_matches + per_log_matches
    all_matches.sort(key=lambda m: m["start"])

    for i in range(len(all_matches)):
        for j in range(i + 1, len(all_matches)):
            if all_matches[i]["end"] > all_matches[j]["start"] and all_matches[j]["end"] > all_matches[i]["start"]:
                all_matches[i]["overlap"] = True
                all_matches[j]["overlap"] = True

    return all_matches


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
            hover = adjust_lightness(shaded, 1.3)

            tag = f"{lineno}_{m['start']}_{m['end']}_{m['name']}"
            if tag not in text_widget.tag_names():
                text_widget.tag_config(tag, background=shaded, underline=m.get('overlap', False))
                text_widget.tag_bind(tag, "<Enter>", lambda e, t=tag, c=hover: text_widget.tag_config(t, background=c))
                text_widget.tag_bind(tag, "<Leave>", lambda e, t=tag, c=shaded: text_widget.tag_config(t, background=c))

            start_idx = f"{lineno}.{m['start']}"
            end_idx = f"{lineno}.{m['end']}"
            text_widget.tag_add(tag, start_idx, end_idx)
