
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from gui.transform_editor import TransformEditorDialog



from utils import json_utils, code_generator


class CodeGeneratorDialog(tk.Toplevel):
    """Dialog for configuring and generating CEF converter code."""

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
        self.pattern_var = tk.StringVar(value=pattern_names[0] if pattern_names else "")
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


        # sample initial rows
        self.tree.insert("", "end", values=("time", "ISODate", "none", ""))
        self.tree.insert("", "end", values=("user", "UserName", "none", ""))
        self.tree.insert("", "end", values=("msg", "Message", "none", ""))
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text="+ Add Field", command=self._on_add_field).pack(side="left", padx=5)
        ttk.Button(btns, text="Preview Code ▸", command=self._on_preview).pack(side="right", padx=5)
        ttk.Button(btns, text="Generate Python", command=self._on_generate).pack(side="right", padx=5)

    def _collect_patterns(self) -> list:
        patterns = {p["name"]: p for p in json_utils.load_all_patterns()}
        for p in self.per_log_patterns:
            patterns[p.get("name")] = p
        return [
            {"name": name, "regex": pat.get("regex", pat.get("pattern", ""))}
            for name, pat in patterns.items()
        ]

    def _row_to_mapping(self, item):
        values = self.tree.item(item, "values")
        return {
            "cef": values[0],
            "pattern": values[1],
            "group": 0,
            "transform": values[2] or "none",
        }

    def _on_add_field(self):
        cef_field = simpledialog.askstring("CEF Field", "Enter CEF field key")
        if not cef_field:
            return
        pattern = simpledialog.askstring("Source Pattern", "Enter pattern name")
        if not pattern:
            return
        self.tree.insert("", "end", values=(cef_field, pattern, "none", ""))

    def _on_preview(self):
        # generate code into a temporary directory and show the converter code
        import tempfile, pathlib

        header = {k: v.get() for k, v in self.header_vars.items()}
        mappings = [self._row_to_mapping(item) for item in self.tree.get_children()]
        patterns = self._collect_patterns()

        tmp_dir = tempfile.mkdtemp()
        paths = code_generator.generate_files(header, mappings, patterns, tmp_dir)
        converter_path = pathlib.Path(paths[0])
        try:
            with open(converter_path, "r", encoding="utf-8") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror("Error", str(e))
            return

        preview = tk.Toplevel(self)
        preview.title("Generated cef_converter.py")
        text = tk.Text(preview, wrap="none")
        text.insert("1.0", data)
        text.pack(fill="both", expand=True)

    def _on_generate(self):
        header = {k: v.get() for k, v in self.header_vars.items()}
        mappings = [self._row_to_mapping(item) for item in self.tree.get_children()]
        patterns = self._collect_patterns()
        out_dir = os.path.join(os.getcwd(), "generated_cef")
        try:
            code_generator.generate_files(header, mappings, patterns, out_dir)
            messagebox.showinfo("Success", f"Files written to {out_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def _on_edit(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        cef_field, pattern, transform = values[:3]
        dlg = TransformEditorDialog(self, cef_field, current=transform)
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.result is not None:
            self.tree.item(item, values=(cef_field, pattern, dlg.result, values[3]))
