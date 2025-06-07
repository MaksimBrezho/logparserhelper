import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import re
from utils.json_utils import load_transformations, save_transformations

class LogGeneratorWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Генератор логов")
        self.geometry("800x400")

        self.transforms = load_transformations().get("transformations", [])
        self.create_widgets()

    def create_widgets(self):
        columns = ("enabled", "pattern", "example")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("enabled", text="Исп.")
        self.tree.heading("pattern", text="Регулярное выражение")
        self.tree.heading("example", text="Преобразованный пример")
        self.tree.column("enabled", width=50, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_tree()

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        edit_btn = tk.Button(btn_frame, text="Редактировать", command=self.edit_selected)
        edit_btn.pack(side="left", padx=5)

        toggle_btn = tk.Button(btn_frame, text="Вкл/выкл", command=self.toggle_selected)
        toggle_btn.pack(side="left", padx=5)

        save_btn = tk.Button(btn_frame, text="Сохранить", command=self.save_current)
        save_btn.pack(side="right", padx=5)

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        for tr in self.transforms:
            pattern_text = tr.get("pattern", "")
            sample = tr.get("sample", "")
            replacement = tr.get("replacement", "<DATE>")
            try:
                example = re.sub(pattern_text, replacement, sample)
            except re.error:
                example = sample
            enabled_marker = "✓" if tr.get("enabled", True) else ""
            self.tree.insert("", "end", values=(enabled_marker, pattern_text, example))

    def get_selected_index(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор отсутствует", "Сначала выберите элемент.")
            return None
        return self.tree.index(selected[0])

    def edit_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        current = self.transforms[idx]
        new_sample = simpledialog.askstring(
            "Пример строки", "Измените пример:", initialvalue=current.get("sample", "")
        )
        if new_sample is None:
            return
        new_replacement = simpledialog.askstring(
            "Строка замены", "Измените строку замены:", initialvalue=current.get("replacement", "<DATE>")
        )
        if new_replacement is None:
            return
        current["sample"] = new_sample
        current["replacement"] = new_replacement
        self.update_tree()

    def toggle_selected(self):
        idx = self.get_selected_index()
        if idx is None:
            return
        self.transforms[idx]["enabled"] = not self.transforms[idx].get("enabled", True)
        self.update_tree()

    def save_current(self):
        save_transformations({"transformations": self.transforms})
        messagebox.showinfo("Сохранено", "Трансформации сохранены")
