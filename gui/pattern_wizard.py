import logging
import tkinter as tk
from tkinter import ttk, messagebox
import re

logger = logging.getLogger(__name__)

from core.regex_highlighter import apply_highlighting
from gui.tooltip import ToolTip

from core.regex.regex_builder import build_draft_regex_from_examples
from utils.json_utils import save_user_pattern, save_per_log_pattern


SNIPPETS = [
    ("Одно слово (любые символы, кроме пробелов)", r"\S+"),
    ("Одно слово только из букв", r"[a-zA-Z]+"),
    ("Одно слово только из цифр", r"\d+"),
    ("Слово из букв и цифр", r"[a-zA-Z0-9]+"),
    ("Слово из любых символов", r"[^ \t\n\r\f\v]+"),
    ("Строка до конца строки", r".*"),
    ("Строка до конца строки (нежадно)", r".*?"),
    ("Одно число фиксированной длины (3)", r"\d{3}"),
    ("Одно число, минимум N цифр", r"\d{2,}"),
    ("Символы до двоеточия", r"[^:]+"),
    ("Фрагмент в квадратных скобках", r"\[[^\]]+\]"),
    ("Фрагмент в круглых скобках", r"\([^)]+\)"),
    ("Линия с тегом", r"[a-zA-Z0-9._-]+:")
]



class PatternWizardDialog(tk.Toplevel):
    def __init__(self, parent, selected_lines, context_lines, cef_fields, source_file, log_name, categories=None, fragment_context=None):

        super().__init__(parent)
        self.title("Создание нового паттерна")
        # Минимальный размер окна, но пользователь может растягивать его
        self.minsize(800, 600)

        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Сохранить", command=self._save, accelerator="Ctrl+S")
        menu_bar.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menu_bar)
        self.bind_all("<Control-s>", lambda e: self._save())

        self.selected_lines = selected_lines

        self.fragment_context = fragment_context or []
        
        self.context_lines = context_lines
        self.cef_fields = cef_fields
        self.cef_category_map = {
            f.get("key"): f.get("category") for f in self.cef_fields
            if f.get("key") and f.get("category")
        }
        cef_categories = {
            f.get("category") for f in self.cef_fields if f.get("category")
        }

        self.MULTI_CATEGORY = "Multiple"
        self.categories = sorted(
            set(categories or []) | cef_categories | {self.MULTI_CATEGORY}
        )

        self.source_file = source_file
        self.log_name = log_name

        self.page_size = 20
        self.current_page = 0
        self.regex_history = []

        self.page_label_var = tk.StringVar()
        self.show_mode = tk.StringVar(value="matches")
        self.total_pages = 1

        # Vars
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.regex_var = tk.StringVar()
        self.case_insensitive = tk.BooleanVar()
        self.digit_mode_values = {
            "Стандартный": "standard",
            "Фиксированная длина": "always_fixed_length",
            "Всегда \\d+": "always_plus",
            "С выставлением минимальной длины": "min_length",
            "Фикс. или мин.": "fixed_and_min",
        }
        self.digit_mode_display_var = tk.StringVar(value="Фиксированная длина")
        self.digit_mode_var = tk.StringVar(value="always_fixed_length")
        self.digit_min_length_var = tk.IntVar(value=1)
        self.merge_text_tokens_var = tk.BooleanVar(value=True)
        self.prefer_alternatives_var = tk.BooleanVar(value=True)
        self.merge_by_prefix_var = tk.BooleanVar(value=True)
        self.max_enum_options_var = tk.IntVar(value=10)
        self.window_left_var = tk.StringVar()
        self.window_right_var = tk.StringVar()
        self.selected_field_vars = {}
        self.show_advanced = tk.BooleanVar(value=False)

        self._build_ui()
        total_pages = (len(self.context_lines) - 1) // self.page_size + 1
        self.total_pages = total_pages
        self.page_label_var.set(f"Страница {self.current_page + 1} из {total_pages}")
        self._generate_regex()

    def _build_ui(self):
        # Верхние поля
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=5)

        ttk.Label(top_frame, text="Имя:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.name_var, width=20).pack(side="left", padx=5)

        ttk.Label(top_frame, text="Категория:").pack(side="left")

        self.category_label = ttk.Label(top_frame, textvariable=self.category_var, width=20)
        self.category_label.pack(side="left", padx=5)


        param_frame = ttk.Frame(self)
        param_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(param_frame)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)

        toggle_adv = ttk.Checkbutton(
            left_frame,
            text="Показать дополнительные параметры",
            variable=self.show_advanced,
            command=self._toggle_advanced,
        )
        toggle_adv.pack(anchor="w")

        self.advanced_frame = ttk.Frame(left_frame)

        ci = ttk.Checkbutton(self.advanced_frame, text="Игнорировать регистр", variable=self.case_insensitive)
        ci.pack(anchor="w", pady=2)

        row = ttk.Frame(self.advanced_frame)
        row.pack(anchor="w")
        ttk.Label(row, text="Режим чисел:").pack(side="left")
        dm = ttk.Combobox(row, textvariable=self.digit_mode_display_var, values=list(self.digit_mode_values.keys()), width=22, state="readonly")
        dm.pack(side="left", padx=2)
        self.digit_mode_display_var.trace_add("write", lambda *_: self._on_digit_mode_change())

        row = ttk.Frame(self.advanced_frame)
        row.pack(anchor="w")
        ttk.Label(row, text="Мин. длина числа:").pack(side="left")
        ml = ttk.Spinbox(row, from_=1, to=10, textvariable=self.digit_min_length_var, width=5)
        ml.pack(side="left", padx=2)

        mt = ttk.Checkbutton(self.advanced_frame, text="Объединять текст", variable=self.merge_text_tokens_var)
        mt.pack(anchor="w", pady=2)
        pa = ttk.Checkbutton(self.advanced_frame, text="Использовать |", variable=self.prefer_alternatives_var)
        pa.pack(anchor="w", pady=2)
        bp = ttk.Checkbutton(self.advanced_frame, text="Префикс. слияние", variable=self.merge_by_prefix_var)
        bp.pack(anchor="w", pady=2)

        row = ttk.Frame(self.advanced_frame)
        row.pack(anchor="w")
        ttk.Label(row, text="Макс. вариантов:").pack(side="left")
        mx = ttk.Spinbox(row, from_=1, to=20, textvariable=self.max_enum_options_var, width=5)
        mx.pack(side="left", padx=2)

        row = ttk.Frame(self.advanced_frame)
        row.pack(anchor="w")
        ttk.Label(row, text="Окно слева:").pack(side="left")
        wl = ttk.Entry(row, textvariable=self.window_left_var, width=8)
        wl.pack(side="left", padx=2)
        ttk.Label(row, text="Окно справа:").pack(side="left")
        wr = ttk.Entry(row, textvariable=self.window_right_var, width=8)
        wr.pack(side="left", padx=2)

        right_frame = ttk.Frame(param_frame)
        right_frame.pack(side="left", fill="both", expand=True)

        # Tooltips
        self._add_tip(ci, "Регулярное выражение будет нечувствительно к регистру")
        self._add_tip(dm, "Как обрабатывать числа в строках")
        self._add_tip(ml, "Минимальная длина числа при генерации")
        self._add_tip(mt, "Объединять разные слова в один блок")
        self._add_tip(pa, "Предпочитать варианты через |")
        self._add_tip(bp, "Объединять по общему префиксу")
        self._add_tip(mx, "Максимальное число вариантов в перечислении")
        self._add_tip(wl, "Слева от совпадения")
        self._add_tip(wr, "Справа от совпадения")

        # Скрыть блок с параметрами по умолчанию
        self._toggle_advanced()

        # Регулярное выражение
        regex_frame = ttk.LabelFrame(right_frame, text="Сгенерированное регулярное выражение")
        regex_frame.pack(fill="x", padx=5, pady=5)
        self.regex_entry = tk.Text(regex_frame, height=2)
        self.regex_entry.pack(fill="x")

        self.SNIPPET_DEFAULT = "Вставить шаблон..."
        self.snippet_var = tk.StringVar(value=self.SNIPPET_DEFAULT)
        self.snippet_map = {label: regex for label, regex in SNIPPETS}
        snippet_combo = ttk.Combobox(
            regex_frame,
            textvariable=self.snippet_var,
            values=list(self.snippet_map.keys()),
            state="readonly",
            width=35,
        )
        snippet_combo.pack(anchor="w", pady=2)
        snippet_combo.bind("<<ComboboxSelected>>", self._on_snippet_selected)

        undo_btn = ttk.Button(regex_frame, text="← Предыдущая", command=self._undo_regex)
        undo_btn.pack(side="right", padx=5)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Обновить", command=self._generate_regex).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Применить", command=self._apply_regex).pack(side="left", padx=2)

        # Примеры
        example_frame = ttk.LabelFrame(right_frame, text="Примеры")
        example_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.example_list = tk.Listbox(example_frame, height=4)
        self.example_list.pack(side="left", fill="both", expand=True)

        for s in self.selected_lines:
            self.example_list.insert(tk.END, s)

        btns = ttk.Frame(example_frame)
        btns.pack(side="left", fill="y", padx=5)
        ttk.Button(btns, text="Удалить", command=self._remove_example).pack(pady=2)
        ttk.Button(btns, text="Добавить выделение", command=self._add_selection).pack(pady=2)

        # Список совпадений
        self.match_frame = ttk.LabelFrame(self, text="Совпадения")
        self.match_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.match_text = tk.Text(self.match_frame, height=10)
        self.match_text.pack(fill="both", expand=True)

        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill="x", pady=5)
        ttk.Radiobutton(mode_frame, text="Совпадения", variable=self.show_mode, value="matches", command=self._on_mode_change).pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Отсутствие", variable=self.show_mode, value="absent", command=self._on_mode_change).pack(side="left", padx=5)
        ttk.Radiobutton(mode_frame, text="Конфликты", variable=self.show_mode, value="conflicts", command=self._on_mode_change).pack(side="left", padx=5)

        nav = ttk.Frame(self)
        nav.pack(fill="x")
        ttk.Button(nav, text="←", command=self.prev_page).pack(side="left")
        ttk.Label(nav, textvariable=self.page_label_var).pack(side="left", padx=5)
        ttk.Button(nav, text="→", command=self.next_page).pack(side="left")

        # CEF-поля
        field_frame = ttk.LabelFrame(left_frame, text="CEF-поля")
        field_frame.pack(fill="both", expand=True, pady=5)

        search_frame = ttk.Frame(field_frame)
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Поиск:").pack(side="left")
        self.cef_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.cef_search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.cef_search_var.trace_add("write", lambda *_: self._filter_cef_fields())

        list_container = ttk.Frame(field_frame)
        list_container.pack(fill="both", expand=True)
        canvas = tk.Canvas(list_container, height=80)
        scroll = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.cef_field_inner = ttk.Frame(canvas)
        self.cef_field_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.cef_field_inner, anchor="nw")

        self._filter_cef_fields()
        self._auto_select_category()

        # Кнопка сохранения
        ttk.Button(self, text="Сохранить", command=self._save).pack(pady=10)

    def _generate_regex(self):
        try:
            logger.info("[Wizard] Генерация регулярного выражения...")

            # Поддержка генерации даже при одной строке
            lines = self.selected_lines
            if len(lines) == 1:
                lines = lines * 2  # искусственно дублируем

            draft = build_draft_regex_from_examples(
                lines,
                digit_mode=self.digit_mode_var.get(),
                digit_min_length=self.digit_min_length_var.get(),
                case_insensitive=self.case_insensitive.get(),
                window_left=self.window_left_var.get() or None,
                window_right=self.window_right_var.get() or None,
                merge_text_tokens=self.merge_text_tokens_var.get(),
                max_enum_options=self.max_enum_options_var.get(),
                prefer_alternatives=self.prefer_alternatives_var.get(),
                merge_by_common_prefix=self.merge_by_prefix_var.get(),
            )
            logger.info("[Wizard] Получено: %s", draft)

            self._push_history(draft)
            self.regex_var.set(draft)
            self.regex_entry.delete("1.0", tk.END)
            self.regex_entry.insert(tk.END, draft)
            self._apply_regex()

        except Exception as e:
            logger.error("[Wizard Error] %s", e)
            messagebox.showerror("Ошибка генерации", str(e))

    def _apply_regex(self):
        pattern = self.regex_entry.get("1.0", tk.END).strip()
        if not pattern:
            return

        try:
            flags = re.IGNORECASE if self.case_insensitive.get() else 0
            regex = re.compile(pattern, flags)
        except re.error as e:
            messagebox.showerror("Ошибка компиляции", str(e))
            return

        self._push_history(pattern)

        self.match_text.config(state="normal")
        self.match_text.delete("1.0", tk.END)

        lines_info = []
        mode = self.show_mode.get()
        for idx, line in enumerate(self.context_lines, start=1):
            found = list(regex.finditer(line))
            if mode == "matches" and found:
                lines_info.append((idx, line, found))
            elif mode == "absent" and not found:
                lines_info.append((idx, line, found))
            elif mode == "conflicts" and len(found) >= 2:
                lines_info.append((idx, line, found))

        total_pages = (len(lines_info) - 1) // self.page_size + 1 if lines_info else 1
        self.total_pages = total_pages
        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        start = self.current_page * self.page_size
        end = min(start + self.page_size, len(lines_info))
        page_lines = lines_info[start:end]

        for _, line, _ in page_lines:
            self.match_text.insert(tk.END, line + "\n")

        matches_by_line = {}
        for idx, (_, _, matches) in enumerate(page_lines, start=1):
            if matches:
                matches_by_line[idx] = [
                    {
                        "start": m.start(),
                        "end": m.end(),
                        "category": "preview",
                        "name": "preview",
                        "regex": pattern,
                        "priority": 1,
                    }
                    for m in matches
                ]

        apply_highlighting(self.match_text, matches_by_line, {"preview"}, {"preview": "yellow"})

        self.page_label_var.set(f"Страница {self.current_page + 1} из {total_pages}")

        self.match_text.config(state="disabled")

    def _save(self):
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        regex = self.regex_entry.get("1.0", tk.END).strip()
        fields = [f for f, v in self.selected_field_vars.items() if v.get()]

        if not name or not category or not regex:
            messagebox.showwarning(
                "Незаполненные поля",
                "Имя, категория и регулярное выражение обязательны."
            )
            return

        if not fields:
            messagebox.showwarning(
                "Незаполненные поля",
                "Необходимо выбрать хотя бы одно CEF-поле."
            )
            return

        pattern_data = {
            "name": name,
            "regex": regex,
            "category": category,
            "fields": fields,
            "enabled": True,
            "priority": 1000
        }

        save_user_pattern(pattern_data)
        save_per_log_pattern(self.source_file, name, pattern_data, log_name=self.log_name)

        messagebox.showinfo("Готово", f"Паттерн '{name}' сохранён.")
        self.destroy()

    def _add_tip(self, widget, text):
        tip = ToolTip(widget)
        widget.bind("<Enter>", lambda e: tip.schedule(text, e.x_root, e.y_root))
        widget.bind("<Leave>", lambda e: tip.unschedule())

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._apply_regex()

    def next_page(self):
        if self.current_page + 1 < self.total_pages:
            self.current_page += 1
            self._apply_regex()

    def _on_mode_change(self):
        self.current_page = 0
        self._apply_regex()

    def _push_history(self, regex):
        if not self.regex_history or self.regex_history[-1] != regex:
            self.regex_history.append(regex)

    def _undo_regex(self):
        if len(self.regex_history) < 2:
            return
        self.regex_history.pop()
        prev = self.regex_history[-1]
        self.regex_entry.delete("1.0", tk.END)
        self.regex_entry.insert(tk.END, prev)
        self._apply_regex()

    def _on_snippet_selected(self, *_):
        label = self.snippet_var.get()
        regex = self.snippet_map.get(label)
        if not regex:
            return
        try:
            index = self.regex_entry.index(tk.INSERT)
        except Exception:
            index = tk.END
        self.regex_entry.insert(index, regex)
        self.snippet_var.set(self.SNIPPET_DEFAULT)

    def _add_selection(self):
        try:
            start = self.match_text.index(tk.SEL_FIRST)
            end = self.match_text.index(tk.SEL_LAST)
        except tk.TclError:
            return

        start_line = int(start.split(".")[0])
        end_line = int(end.split(".")[0])
        if start_line != end_line:
            messagebox.showwarning("Выделение", "Выберите часть одной строки")
            return

        fragment = self.match_text.get(start, end)
        full_line = self.match_text.get(f"{start_line}.0", f"{start_line}.end")
        self.selected_lines.append(fragment)
        self.fragment_context.append(full_line)
        self.example_list.insert(tk.END, fragment)
        self._generate_regex()

    def _remove_example(self):
        sel = list(self.example_list.curselection())
        if not sel:
            return
        for idx in reversed(sel):
            self.example_list.delete(idx)
            del self.selected_lines[idx]
            del self.fragment_context[idx]
        self._generate_regex()

    def _on_digit_mode_change(self, *_):
        disp = self.digit_mode_display_var.get()
        self.digit_mode_var.set(self.digit_mode_values.get(disp, "standard"))

    def _toggle_advanced(self):
        if self.show_advanced.get():
            self.advanced_frame.pack(fill="x", pady=5)
        else:
            self.advanced_frame.forget()

    def _filter_cef_fields(self):
        query = self.cef_search_var.get().lower()
        for widget in self.cef_field_inner.winfo_children():
            widget.destroy()
        for field in self.cef_fields:
            key = field.get("key", "")
            name = field.get("name", "")
            example = field.get("example", "")
            if query in (key + name).lower():
                var = self.selected_field_vars.get(key)
                if not var:
                    var = tk.BooleanVar()
                    self.selected_field_vars[key] = var
                    var.trace_add("write", lambda *_: self._auto_select_category())
                chk = ttk.Checkbutton(
                    self.cef_field_inner,
                    text=key,
                    variable=var
                )
                chk.pack(anchor="w")
                tip = f"{name}\nПример: {example}"
                self._add_tip(chk, tip)

    def _auto_select_category(self):
        selected_keys = [k for k, v in self.selected_field_vars.items() if v.get()]
        categories = {
            self.cef_category_map.get(k)
            for k in selected_keys
            if self.cef_category_map.get(k)
        }
        if len(categories) == 1:
            cat = next(iter(categories))

        elif len(categories) > 1:
            cat = self.MULTI_CATEGORY
        else:
            cat = ""

        if cat and cat not in self.categories:
            self.categories.append(cat)
            self.categories.sort()

        self.category_var.set(cat)

