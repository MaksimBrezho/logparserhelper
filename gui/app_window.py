import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from utils.json_utils import load_all_patterns
from core.regex_highlighter import find_matches_in_line, apply_highlighting
from gui.pattern_panel import PatternPanel
from utils.color_utils import generate_distinct_colors
from gui.tooltip import ToolTip
from gui.pattern_wizard import PatternWizardDialog
import re


class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.logs = []
        self.page_size = 40
        self.current_page = 0
        self.patterns = []
        self.tooltip = ToolTip(self)
        self.pattern_panel = None
        self.match_cache = {}  # lineno -> list of matches

        self._setup_widgets()
        self._load_patterns()

    def _setup_widgets(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = tk.Frame(self)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.text_area = tk.Text(frame, wrap=tk.NONE)
        self.text_area.grid(row=0, column=0, sticky="nsew")

        y_scroll = tk.Scrollbar(frame, orient="vertical", command=self.text_area.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.text_area.config(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(frame, orient="horizontal", command=self.text_area.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.text_area.config(xscrollcommand=x_scroll.set)

        self.pattern_panel = PatternPanel(
            master=frame,
            patterns=[],
            on_toggle_callback=self.render_page,
            width=200
        )
        self.pattern_panel.grid(row=0, column=2, sticky="ns", padx=5)
        self.pattern_panel.grid_propagate(False)

        ctrl = tk.Frame(self)
        ctrl.grid(row=1, column=0, sticky="w", padx=5, pady=5)

        tk.Button(ctrl, text="Загрузить лог", command=self.load_log_file).pack(side="left", padx=5)
        tk.Button(ctrl, text="← Назад", command=self.prev_page).pack(side="left", padx=5)
        tk.Button(ctrl, text="Вперёд →", command=self.next_page).pack(side="left", padx=5)

        tk.Label(ctrl, text="Строк на странице:").pack(side="left", padx=(20, 5))

        self.spinbox = tk.Spinbox(ctrl, from_=1, to=1000, width=5, command=self.update_page_size)
        self.spinbox.pack(side="left")
        self.spinbox.delete(0, tk.END)
        self.spinbox.insert(0, str(self.page_size))

        self.status_label = tk.Label(ctrl, text="Стр. 0 из 0")
        self.status_label.pack(side="left", padx=15)
        tk.Button(ctrl, text="Создать паттерн", command=self.open_pattern_wizard).pack(side="left", padx=5)
        self.text_area.bind("<Motion>", self.on_hover)
        self.text_area.bind("<Leave>", lambda e: self.tooltip.hidetip())

    def _load_patterns(self):
        self.patterns = load_all_patterns()

    def load_log_file(self):
        path = filedialog.askopenfilename(filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            self.logs = [line.rstrip() for line in f.readlines()]
        self.current_page = 0
        self._cache_matches()
        self.render_page()

    def _cache_matches(self):
        self.match_cache = {}
        active_patterns = [p for p in self.patterns if p.get("enabled", True)]

        for i, line in enumerate(self.logs, start=1):
            self.match_cache[i] = find_matches_in_line(line, active_patterns)

    def render_page(self):
        self.text_area.delete(1.0, tk.END)

        start = self.current_page * self.page_size
        end = start + self.page_size
        visible_lines = self.logs[start:end]

        for line in visible_lines:
            self.text_area.insert(tk.END, line + "\n")

        # Собираем все паттерны, у которых были совпадения
        matched_names = set()
        for matches in self.match_cache.values():
            for m in matches:
                matched_names.add(m["name"])

        # visible_patterns = все найденные паттерны
        visible_patterns = [p for p in self.patterns if p["name"] in matched_names]

        # active_patterns = включённые пользователем
        active_patterns = [p for p in visible_patterns if p.get("enabled", True)]
        active_names = set(p["name"] for p in active_patterns)

        # Формируем color_map по всем категориям
        categories = sorted(set(p["category"] for p in visible_patterns))
        color_map = {cat: color for cat, color in zip(categories, generate_distinct_colors(len(categories)))}

        # Собираем matches для текущей страницы, но с относительной нумерацией
        matches_to_show = {
            rel_lineno: self.match_cache.get(abs_lineno, [])
            for rel_lineno, abs_lineno in enumerate(range(start + 1, end + 1), start=1)
        }

        # Построим индекс оттенков: (category, regex) -> index
        pattern_keys = []
        seen = set()
        for matches in self.match_cache.values():
            for m in matches:
                key = (m["category"], m["regex"])
                if key not in seen:
                    pattern_keys.append(key)
                    seen.add(key)

        pattern_index_map = {key: i for i, key in enumerate(pattern_keys)}

        # Проверка на пересекающиеся паттерны
        def has_overlap(matches: list[dict]) -> bool:
            intervals = sorted((m["start"], m["end"]) for m in matches)
            for i in range(1, len(intervals)):
                if intervals[i][0] < intervals[i - 1][1]:
                    return True
            return False

        for line_num, matches in matches_to_show.items():
            if has_overlap(matches):
                print(f"[WARNING] Overlapping patterns on line {line_num}:")
                for m in matches:
                    print(f"  - {m['start']}..{m['end']} → {m['name']} ({m['regex']})")

        # Подсветка текста
        apply_highlighting(self.text_area, matches_to_show, active_names, color_map)

        # Обновление панели справа
        self.pattern_panel.patterns = visible_patterns
        self.pattern_panel.refresh(color_map=color_map, pattern_index_map=pattern_index_map)

        self._update_status()

    def update_page_size(self):
        try:
            self.page_size = max(1, int(self.spinbox.get()))
            self.current_page = 0
            self.render_page()
        except ValueError:
            pass

    def _update_status(self):
        total_pages = (len(self.logs) - 1) // self.page_size + 1 if self.logs else 0
        self.status_label.config(text=f"Стр. {self.current_page + 1} из {total_pages}")

    def next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.logs):
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def on_hover(self, event):
        try:
            index = self.text_area.index(f"@{event.x},{event.y}")
            tags = self.text_area.tag_names(index)
            if tags:
                tag = tags[0]
                category, *_ = tag.split("_", 1)
                self.tooltip.schedule(f"Категория: {category}", event.x_root, event.y_root)
            else:
                self.tooltip.unschedule()
        except Exception:
            self.tooltip.unschedule()

    def open_pattern_wizard(self):
        selections = self.get_selected_lines()
        if not selections:
            messagebox.showwarning("Нет выделения", "Пожалуйста, выделите строки для генерации паттерна.")
            return

        # Получаем CEF-поля и путь к лог-файлу
        cef_fields = getattr(self.pattern_panel, "cef_fields", [])
        source_file = getattr(self, "source_path", "example.log")

        try:
            selected_lines = [s for s, _ in selections]
            context_lines = [c for _, c in selections]
            PatternWizardDialog(
                parent=self,
                selected_lines=selected_lines,
                context_lines=context_lines,
                cef_fields=cef_fields,
                source_file=source_file
            )
        except Exception as e:
            print(f"[Ошибка PatternWizard] {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть мастер: {e}")

    def get_selected_lines(self):
        """Return selected fragments along with their full line context."""
        try:
            start = self.text_area.index(tk.SEL_FIRST)
            end = self.text_area.index(tk.SEL_LAST)
        except tk.TclError:
            return []

        start_line = int(start.split('.')[0])
        end_line = int(end.split('.')[0])

        selections = []
        for line_no in range(start_line, end_line + 1):
            line_start = f"{line_no}.0"
            line_end = f"{line_no}.end"
            full_line = self.text_area.get(line_start, line_end)

            sel_start = start if line_no == start_line else line_start
            sel_end = end if line_no == end_line else line_end
            fragment = self.text_area.get(sel_start, sel_end)
            if fragment.strip():
                selections.append((fragment, full_line))

        return selections
