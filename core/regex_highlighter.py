import re
import tkinter as tk
from tkinter import END

from utils.color_utils import generate_distinct_colors

# глобальная таблица соответствий
tag_to_label = {}

def highlight_dates_in_text(text_widget, patterns):
    text_widget.tag_delete(*text_widget.tag_names())
    content = text_widget.get("1.0", tk.END)
    print(f"[DEBUG] content length: {len(content)}")
    date_patterns = patterns.get("date_patterns", [])
    colors = generate_distinct_colors(len(date_patterns))
    tag_to_label.clear()

    matched_indexes = set()

    for i, pat in enumerate(date_patterns):
        if not pat.get("enabled", True):
            continue

        tag_name = f"date_{i}"
        regex = re.compile(pat["pattern"])
        text_widget.tag_config(tag_name, background=colors[i])

        tag_to_label[tag_name] = pat["name"]

        for match in regex.finditer(content):
            start_idx = text_widget.index(f"1.0 + {match.start()}c")
            end_idx = text_widget.index(f"1.0 + {match.end()}c")
            text_widget.tag_add(tag_name, start_idx, end_idx)

            matched_indexes.add(i)

    return matched_indexes


def debug_highlight_dates_in_text(text_widget, patterns):
    """
    Отладочная версия функции подсветки: выводит подробности по каждому паттерну.
    """
    text_widget.tag_delete(*text_widget.tag_names())
    content = text_widget.get("1.0", END)
    print(f"[DEBUG] Текущая длина текста: {len(content)} символов")

    date_patterns = patterns.get("date_patterns", [])
    matched_indexes = set()

    for i, pat in enumerate(date_patterns):
        if not pat.get("enabled", True):
            continue

        pattern = pat["pattern"]
        try:
            regex = re.compile(pattern)
        except re.error as e:
            print(f"[ERROR] Некорректный паттерн '{pattern}': {e}")
            continue

        matches = list(regex.finditer(content))
        print(f"[DEBUG] Паттерн {i} ('{pat['name']}') дал {len(matches)} совпадений")

        for match in matches:
            print(f"    -> Совпадение: '{match.group()}' на позициях {match.start()} - {match.end()}")
            matched_indexes.add(i)

    return matched_indexes