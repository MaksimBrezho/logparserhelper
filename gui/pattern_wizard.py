import tkinter as tk
from tkinter import ttk, messagebox
import re

from core.regex.regex_builder import build_draft_regex_from_examples
from utils.json_utils import save_user_pattern, save_per_log_pattern


class PatternWizardDialog(tk.Toplevel):
    def __init__(self, parent, selected_lines, context_lines, cef_fields, source_file):
        super().__init__(parent)
        self.title("Создание нового паттерна")
        self.geometry("800x600")

        self.selected_lines = selected_lines
        self.context_lines = context_lines
        self.cef_fields = cef_fields
        self.source_file = source_file

        # Vars
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.regex_var = tk.StringVar()
        self.case_insensitive = tk.BooleanVar()
        self.digit_mode_var = tk.StringVar(value="standard")
        self.digit_min_length_var = tk.IntVar(value=1)
        self.selected_field_vars = {}
        self.match_check_vars = []

        self._build_ui()
        self._generate_regex()

    def _build_ui(self):
        # Верхние поля
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=5)

        ttk.Label(top_frame, text="Имя:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.name_var, width=20).pack(side="left", padx=5)

        ttk.Label(top_frame, text="Категория:").pack(side="left")
        ttk.Entry(top_frame, textvariable=self.category_var, width=20).pack(side="left", padx=5)

        # Флаги и параметры
        flag_frame = ttk.Frame(self)
        flag_frame.pack(fill="x", pady=5)

        ttk.Checkbutton(flag_frame, text="Case Insensitive", variable=self.case_insensitive).pack(side="left", padx=5)

        ttk.Label(flag_frame, text="Digit Mode:").pack(side="left")
        ttk.Combobox(flag_frame, textvariable=self.digit_mode_var, values=[
            "standard", "always_fixed_length", "always_plus", "min_length", "fixed_and_min"
        ], width=20, state="readonly").pack(side="left", padx=5)

        ttk.Label(flag_frame, text="Min Digit Len:").pack(side="left")
        ttk.Spinbox(flag_frame, from_=1, to=10, textvariable=self.digit_min_length_var, width=5).pack(side="left", padx=5)

        # Регулярка
        regex_frame = ttk.LabelFrame(self, text="Сгенерированная регулярка")
        regex_frame.pack(fill="x", padx=5, pady=5)
        self.regex_entry = tk.Text(regex_frame, height=2)
        self.regex_entry.pack(fill="x")

        # Кнопка генерации
        ttk.Button(self, text="Обновить регулярку", command=self._generate_regex).pack(pady=5)

        # Кнопка применения
        ttk.Button(self, text="Применить к строкам", command=self._apply_regex).pack(pady=5)

        # Список совпадений
        self.match_frame = ttk.LabelFrame(self, text="Совпадения")
        self.match_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.match_listbox = tk.Listbox(self.match_frame)
        self.match_listbox.pack(fill="both", expand=True)

        # CEF-поля
        field_frame = ttk.LabelFrame(self, text="CEF-поля")
        field_frame.pack(fill="x", padx=5, pady=5)
        for field in self.cef_fields:
            var = tk.BooleanVar()
            self.selected_field_vars[field] = var
            ttk.Checkbutton(field_frame, text=field, variable=var).pack(side="left")

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
                case_insensitive=self.case_insensitive.get()
            )
            print("[Wizard] Получено:", draft)

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

        self.match_listbox.delete(0, tk.END)
        self.match_check_vars.clear()

        for line in self.selected_lines:
            match = regex.search(line)
            if match:
                self.match_listbox.insert(tk.END, line)

    def _save(self):
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        regex = self.regex_entry.get("1.0", tk.END).strip()
        fields = [f for f, v in self.selected_field_vars.items() if v.get()]

        if not name or not category or not regex:
            messagebox.showwarning("Незаполненные поля", "Имя, категория и регулярка обязательны.")
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
        save_per_log_pattern(self.source_file, name, pattern_data)

        messagebox.showinfo("Готово", f"Паттерн '{name}' сохранён.")
        self.destroy()
