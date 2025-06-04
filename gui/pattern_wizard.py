import tkinter as tk
from tkinter import ttk, messagebox
import re

from core.regex_highlighter import apply_highlighting
from gui.tooltip import ToolTip

from core.regex.regex_builder import build_draft_regex_from_examples
from utils.json_utils import save_user_pattern, save_per_log_pattern


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
        self.categories = categories or []
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
        self.cef_field_var = tk.StringVar()
        self.digit_mode_var = tk.StringVar(value="standard")
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
        ttk.Combobox(top_frame, textvariable=self.category_var, values=self.categories, width=20, state="readonly").pack(side="left", padx=5)

        ttk.Label(top_frame, text="CEF-поле:").pack(side="left")
        ttk.Combobox(top_frame, textvariable=self.cef_field_var, values=self.cef_fields, width=15, state="readonly").pack(side="left", padx=5)

        # Флаги и параметры
        toggle_adv = ttk.Checkbutton(
            self,
            text="Показать дополнительные параметры",
            variable=self.show_advanced,
            command=self._toggle_advanced,
        )
        toggle_adv.pack(anchor="w", padx=5)

        self.advanced_frame = ttk.Frame(self)
        flag_frame = ttk.Frame(self.advanced_frame)
        flag_frame.pack(fill="x", pady=5)

        ci = ttk.Checkbutton(flag_frame, text="Игнорировать регистр", variable=self.case_insensitive)
        ci.pack(side="left", padx=5)

        ttk.Label(flag_frame, text="Режим чисел:").pack(side="left")
        dm = ttk.Combobox(flag_frame, textvariable=self.digit_mode_var, values=[
            "standard", "always_fixed_length", "always_plus", "min_length", "fixed_and_min"
        ], width=18, state="readonly")
        dm.pack(side="left", padx=5)

        ttk.Label(flag_frame, text="Мин. длина числа:").pack(side="left")
        ml = ttk.Spinbox(flag_frame, from_=1, to=10, textvariable=self.digit_min_length_var, width=5)
        ml.pack(side="left", padx=5)

        mt = ttk.Checkbutton(flag_frame, text="Объединять текст", variable=self.merge_text_tokens_var)
        mt.pack(side="left", padx=5)
        pa = ttk.Checkbutton(flag_frame, text="Использовать |", variable=self.prefer_alternatives_var)
        pa.pack(side="left", padx=5)
        bp = ttk.Checkbutton(flag_frame, text="Префикс. слияние", variable=self.merge_by_prefix_var)
        bp.pack(side="left", padx=5)
        ttk.Label(flag_frame, text="Макс. вариантов:").pack(side="left")
        mx = ttk.Spinbox(flag_frame, from_=1, to=20, textvariable=self.max_enum_options_var, width=5)
        mx.pack(side="left", padx=5)
        ttk.Label(flag_frame, text="Окно слева:").pack(side="left")
        wl = ttk.Entry(flag_frame, textvariable=self.window_left_var, width=8)
        wl.pack(side="left", padx=2)
        ttk.Label(flag_frame, text="Окно справа:").pack(side="left")
        wr = ttk.Entry(flag_frame, textvariable=self.window_right_var, width=8)
        wr.pack(side="left", padx=2)

        # Tooltips
        self._add_tip(ci, "Регулярка будет нечувствительна к регистру")
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

        # Регулярка
        regex_frame = ttk.LabelFrame(self, text="Сгенерированная регулярка")
        regex_frame.pack(fill="x", padx=5, pady=5)
        self.regex_entry = tk.Text(regex_frame, height=2)
        self.regex_entry.pack(fill="x")

        undo_btn = ttk.Button(regex_frame, text="← Предыдущая", command=self._undo_regex)
        undo_btn.pack(side="right", padx=5)

        # Примеры
        example_frame = ttk.LabelFrame(self, text="Примеры")
        example_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.example_list = tk.Listbox(example_frame, height=4)
        self.example_list.pack(side="left", fill="both", expand=True)

        for s in self.selected_lines:
            self.example_list.insert(tk.END, s)

        btns = ttk.Frame(example_frame)
        btns.pack(side="left", fill="y", padx=5)
        ttk.Button(btns, text="Удалить", command=self._remove_example).pack(pady=2)
        ttk.Button(btns, text="Добавить выделение", command=self._add_selection).pack(pady=2)

        # Кнопка генерации
        ttk.Button(self, text="Обновить регулярку", command=self._generate_regex).pack(pady=5)

        # Кнопка применения
        ttk.Button(self, text="Применить к строкам", command=self._apply_regex).pack(pady=5)

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
        field_frame = ttk.LabelFrame(self, text="CEF-поля")
        field_frame.pack(fill="both", expand=True, padx=5, pady=5)

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

        # Кнопка сохранения
        ttk.Button(self, text="Сохранить", command=self._save).pack(pady=10)

    def _generate_regex(self):
        try:
            print("[Wizard] Генерация регулярки...")

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
            print("[Wizard] Получено:", draft)

            self._push_history(draft)
            self.regex_var.set(draft)
            self.regex_entry.delete("1.0", tk.END)
            self.regex_entry.insert(tk.END, draft)
            self._apply_regex()

        except Exception as e:
            print(f"[Wizard Error] {e}")
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
        cef_field = self.cef_field_var.get().strip()

        if not name or not category or not regex:
            messagebox.showwarning("Незаполненные поля", "Имя, категория и регулярка обязательны.")
            return

        pattern_data = {
            "name": name,
            "regex": regex,
            "category": category,
            "fields": fields,
            "cef_field": cef_field,
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

    def _toggle_advanced(self):
        if self.show_advanced.get():
            self.advanced_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.advanced_frame.forget()

    def _filter_cef_fields(self):
        query = self.cef_search_var.get().lower()
        for widget in self.cef_field_inner.winfo_children():
            widget.destroy()
        for field in self.cef_fields:
            if query in field.lower():
                var = self.selected_field_vars.get(field)
                if not var:
                    var = tk.BooleanVar()
                    self.selected_field_vars[field] = var
                ttk.Checkbutton(
                    self.cef_field_inner,
                    text=field,
                    variable=var
                ).pack(anchor="w")
