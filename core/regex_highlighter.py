import re
import tkinter as tk
from utils.color_utils import generate_distinct_colors

def highlight_dates_in_text(text_widget, patterns):
    """
    Подсвечивает все фрагменты текста, соответствующие шаблонам даты,
    разными цветами по шаблонам.
    """
    text_widget.tag_delete(*text_widget.tag_names())
    content = text_widget.get("1.0", tk.END)

    date_patterns = patterns.get("date_patterns", [])
    colors = generate_distinct_colors(len(date_patterns))

    for i, pat in enumerate(date_patterns):
        tag_name = f"date_{i}"
        pattern_text = pat["pattern"]
        regex_obj = re.compile(pattern_text)
        text_widget.tag_config(tag_name, foreground=colors[i])

        for match in regex_obj.finditer(content):
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.end()} chars"
            text_widget.tag_add(tag_name, start_idx, end_idx)
