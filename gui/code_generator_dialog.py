import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from gui.transform_editor import TransformEditorDialog


class CodeGeneratorDialog(tk.Toplevel):
    """Placeholder dialog for future code generation features."""

    def __init__(self, parent, per_log_patterns=None):
        super().__init__(parent)
        self.title("CEF Code Generator Dialog")
        self.minsize(600, 400)
        self.per_log_patterns = per_log_patterns or []

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)
        ttk.Label(top, text="Source Pattern Key:").grid(row=0, column=0, sticky="w")
        pattern_names = [p.get("name") for p in self.per_log_patterns]
        self.pattern_var = tk.StringVar()
        combo = ttk.Combobox(top, textvariable=self.pattern_var, values=pattern_names, state="readonly")
        combo.grid(row=0, column=1, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        header = ttk.LabelFrame(self, text="CEF Header")
        header.pack(fill="x", padx=10, pady=5)

        self.header_vars = {}
        fields = [
            ("CEF Version", "0"),
            ("Device Vendor", "ACME"),
            ("Device Product", "LogParserPro"),
            ("Device Version", "1.0.0"),
            ("Event Class ID", "42"),
            ("Event Name", "LoginAttempt"),
            ("Severity (int)", "5"),
        ]
        for i, (label, default) in enumerate(fields):
            ttk.Label(header, text=f"{label}:").grid(row=i, column=0, sticky="w", pady=2, padx=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(header, textvariable=var)
            if label == "CEF Version":
                entry.config(state="disabled")
            entry.grid(row=i, column=1, sticky="ew", pady=2, padx=2)
            self.header_vars[label] = var
        header.grid_columnconfigure(1, weight=1)

        fields_frame = ttk.LabelFrame(self, text="Fields Auto-Mapped from Regex Patterns")
        fields_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("cef_field", "source", "transform", "preview")
        self.tree = ttk.Treeview(fields_frame, columns=columns, show="headings", height=5)
        for col in columns:
            heading = "CEF Fields" if col == "cef_field" else col.title()
            self.tree.heading(col, text=heading)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_edit)

        self.tree.insert("", "end", values=("time", "ISODate", "[Edit]", "2024-06.."))
        self.tree.insert("", "end", values=("user", "UserName", "[Edit]", "max"))
        self.tree.insert("", "end", values=("msg", "Message", "[Edit]", "login fail"))

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text="+ Add Field", command=self._on_add_field).pack(side="left", padx=5)
        ttk.Button(btns, text="Preview Code ▸", command=self._on_preview).pack(side="right", padx=5)
        ttk.Button(btns, text="Generate Python", command=self._on_generate).pack(side="right", padx=5)

    def _on_add_field(self):
        messagebox.showinfo("Stub", "Add Field action")

    def _on_preview(self):
        messagebox.showinfo("Stub", "Preview Code action")

    def _on_generate(self):
        messagebox.showinfo("Stub", "Generate Python action")

    def _on_edit(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        cef_field = values[0]
        dlg = TransformEditorDialog(self, cef_field)
        dlg.grab_set()
