import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from utils.json_utils import load_patterns, save_patterns

class RegexEditor(tk.Toplevel):
    def __init__(self, master=None, on_close_callback=None):
        super().__init__(master)
        self.title("Редактор шаблонов дат")
        self.geometry("600x400")
        self.on_close_callback = on_close_callback

        self.patterns = load_patterns().get("date_patterns", [])
        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("pattern",), show="headings")
        self.tree.heading("pattern", text="Регулярное выражение")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_tree()

        # Кнопки
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        add_btn = tk.Button(btn_frame, text="Добавить", command=self.add_pattern)
        add_btn.pack(side="left", padx=5)

        edit_btn = tk.Button(btn_frame, text="Редактировать", command=self.edit_selected)
        edit_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(btn_frame, text="Удалить", command=self.delete_selected)
        delete_btn.pack(side="left", padx=5)

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        for pat in self.patterns:
            self.tree.insert("", "end", values=(pat["pattern"],))

    def add_pattern(self):
        name = simpledialog.askstring("Название шаблона", "Введите название шаблона:")
        if not name:
            return
        pattern = simpledialog.askstring("Регулярное выражение", "Введите шаблон регулярного выражения:")
        if not pattern:
            return

        self.patterns.append({"name": name, "pattern": pattern})
        save_patterns({"date_patterns": self.patterns})
        self.update_tree()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор отсутствует", "Сначала выберите шаблон.")
            return
        idx = self.tree.index(selected[0])
        current = self.patterns[idx]

        new_name = simpledialog.askstring("Название шаблона", "Измените название шаблона:", initialvalue=current["name"])
        if not new_name:
            return
        new_pattern = simpledialog.askstring("Регулярное выражение", "Измените шаблон:", initialvalue=current["pattern"])
        if not new_pattern:
            return

        self.patterns[idx] = {"name": new_name, "pattern": new_pattern}
        save_patterns({"date_patterns": self.patterns})
        self.update_tree()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор отсутствует", "Сначала выберите шаблон.")
            return
        idx = self.tree.index(selected[0])

        confirm = messagebox.askyesno("Подтверждение", "Удалить выбранный шаблон?")
        if confirm:
            del self.patterns[idx]
            save_patterns({"date_patterns": self.patterns})
            self.update_tree()

    def destroy(self):
        if self.on_close_callback:
            self.on_close_callback()
        super().destroy()
