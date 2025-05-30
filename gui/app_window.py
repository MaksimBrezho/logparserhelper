import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from gui.regex_editor import RegexEditor
import os

from core.regex_highlighter import highlight_dates_in_text
from utils.json_utils import load_patterns

class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.patterns = load_patterns()
        self.create_widgets()

    def create_widgets(self):
        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(side="top", fill="x", padx=10, pady=5)

        load_btn = tk.Button(btn_frame, text="Загрузить лог", command=self.load_log)
        load_btn.pack(side="left", padx=5)

        edit_btn = tk.Button(btn_frame, text="Редактировать шаблоны", command=self.edit_patterns)
        edit_btn.pack(side="left", padx=5)

        # Текстовое поле с логами
        self.text_area = scrolledtext.ScrolledText(self, wrap="none", font=("Courier", 10))
        self.text_area.pack(fill="both", expand=True, padx=10, pady=5)

    def load_log(self):
        filepath = filedialog.askopenfilename(title="Выберите лог-файл", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                log_content = f.read()

            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", log_content)
            highlight_dates_in_text(self.text_area, self.patterns)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")

    def edit_patterns(self):
        def on_close():
            if self.text_area.winfo_exists():  # Проверка на существование виджета
                self.patterns = load_patterns()
                content = self.text_area.get("1.0", tk.END)
                highlight_dates_in_text(self.text_area, self.patterns)

        RegexEditor(self.master, on_close_callback=on_close)
