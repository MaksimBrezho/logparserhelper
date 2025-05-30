import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict
from gui.regex_editor import RegexEditor
from core.regex_highlighter import highlight_dates_in_text, tag_to_label
from utils.json_utils import load_patterns

class AppWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        self.patterns = load_patterns()
        self.log_lines = []
        self.current_page = 0
        self.lines_per_page = 5
        self.check_vars = defaultdict(list)
        self.tooltip = None

        self.matched_patterns = set()

        self.create_widgets()

    def create_widgets(self):
        btn_frame = tk.Frame(self)
        btn_frame.pack(side="top", fill="x", padx=10, pady=5)

        load_btn = tk.Button(btn_frame, text="Загрузить лог", command=self.load_log)
        load_btn.pack(side="left", padx=5)

        edit_btn = tk.Button(btn_frame, text="Редактировать шаблоны", command=self.edit_patterns)
        edit_btn.pack(side="left", padx=5)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill="both", expand=True)

        log_frame = tk.Frame(paned)
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True)

        self.text_area = tk.Text(text_frame, wrap="none", font=("Courier", 10))
        self.text_area.pack(side="left", fill="both", expand=True)

        y_scroll = tk.Scrollbar(text_frame, orient="vertical", command=self.text_area.yview)
        y_scroll.pack(side="right", fill="y")
        self.text_area.configure(yscrollcommand=y_scroll.set)

        x_scroll = tk.Scrollbar(log_frame, orient="horizontal", command=self.text_area.xview)
        x_scroll.pack(side="bottom", fill="x")
        self.text_area.configure(xscrollcommand=x_scroll.set)

        paned.add(log_frame, stretch="always")

        self.control_frame = tk.Frame(paned, width=250)
        paned.add(self.control_frame)

        nav_frame = tk.Frame(self)
        nav_frame.pack(side="bottom", fill="x", pady=5)

        self.prev_btn = tk.Button(nav_frame, text="← Назад", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=10)

        self.next_btn = tk.Button(nav_frame, text="Вперед →", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)

        self.page_label = tk.Label(nav_frame, text="")
        self.page_label.pack(side="left", padx=10)

        tk.Label(nav_frame, text="Строк на странице:").pack(side="left", padx=(20, 5))
        self.page_size_spin = tk.Spinbox(nav_frame, from_=1, to=100, width=5, command=self.on_page_size_change)
        self.page_size_spin.delete(0, tk.END)
        self.page_size_spin.insert(0, str(self.lines_per_page))
        self.page_size_spin.pack(side="left")

        self.text_area.bind("<Motion>", self.on_mouse_move)
        self.text_area.bind("<Leave>", self.hide_tooltip)

    def load_log(self):
        filepath = filedialog.askopenfilename(title="Выберите лог-файл", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self.log_lines = f.readlines()

            for pat in self.patterns.get("date_patterns", []):
                pat["enabled"] = True
                pat["_matched"] = False

            self.current_page = 0
            self.update_log_view()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")

    def build_highlight_controls(self):
        for widget in self.control_frame.winfo_children():
            widget.destroy()

        self.check_vars.clear()
        categories = defaultdict(list)

        for i, pat in enumerate(self.patterns.get("date_patterns", [])):
            # Отображаем только те, что хотя бы раз сработали
            if not pat.get("_matched", False):
                continue
            category = pat.get("category", "Дата")
            categories[category].append((i, pat))

        for group, items in categories.items():
            label = tk.Label(self.control_frame, text=group, font=("Arial", 10, "bold"))
            label.pack(anchor="w", padx=10, pady=(10, 0))
            for i, pat in items:
                var = self.check_vars.get(i, tk.BooleanVar(value=pat.get("enabled", True)))
                chk = tk.Checkbutton(
                    self.control_frame,
                    text=pat["name"],
                    variable=var,
                    command=self.apply_highlighting,
                    anchor="w",
                    justify="left"
                )
                chk.pack(fill="x", padx=20, pady=2)
                self.check_vars[i] = var

    def update_log_view(self):
        self.text_area.delete("1.0", tk.END)

        start = self.current_page * self.lines_per_page
        end = start + self.lines_per_page
        visible_lines = self.log_lines[start:end]

        self.text_area.insert("1.0", "".join(visible_lines))
        self.text_area.update_idletasks()
        self.apply_highlighting()
        self.update_nav_buttons()

    def apply_highlighting(self):
        # Обновляем включённость шаблонов из чекбоксов
        for i, pat in enumerate(self.patterns.get("date_patterns", [])):
            if i in self.check_vars:
                pat["enabled"] = self.check_vars[i].get()

        # Подсветка
        matched_indexes = highlight_dates_in_text(self.text_area, self.patterns)

        # Обновляем флаг "_matched": сохраняем True, если хотя бы раз сработал
        for i, pat in enumerate(self.patterns.get("date_patterns", [])):
            pat["_matched"] = pat.get("_matched", False) or (i in matched_indexes)

        self.build_highlight_controls()

    def update_nav_buttons(self):
        self.prev_btn.config(state="normal" if self.current_page > 0 else "disabled")

        max_page = len(self.log_lines) // self.lines_per_page
        if self.current_page >= max_page or not self.log_lines[self.current_page * self.lines_per_page:]:
            self.next_btn.config(state="disabled")
        else:
            self.next_btn.config(state="normal")

        total_pages = max_page + (1 if len(self.log_lines) % self.lines_per_page else 0)
        self.page_label.config(text=f"Стр. {self.current_page + 1} из {max(1, total_pages)}")

    def on_page_size_change(self):
        try:
            new_size = int(self.page_size_spin.get())
            if new_size > 0:
                self.lines_per_page = new_size
                self.current_page = 0
                self.update_log_view()
        except ValueError:
            pass

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_log_view()

    def next_page(self):
        max_page = len(self.log_lines) // self.lines_per_page
        if self.current_page < max_page:
            self.current_page += 1
            self.update_log_view()

    def edit_patterns(self):
        def on_close():
            self.patterns = load_patterns()
            for pat in self.patterns.get("date_patterns", []):
                pat["enabled"] = True
                pat["_matched"] = False
            self.update_log_view()

        RegexEditor(self.master, on_close_callback=on_close)

    def on_mouse_move(self, event):
        index = self.text_area.index(f"@{event.x},{event.y}")
        tags = self.text_area.tag_names(index)

        for tag in tags:
            if tag in tag_to_label:
                self.show_tooltip(event.x_root, event.y_root, tag_to_label[tag])
                return
        self.hide_tooltip()

    def show_tooltip(self, x, y, text):
        if self.tooltip:
            self.tooltip.destroy()

        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x+15}+{y+10}")

        label = tk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, font=("Arial", 9))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
