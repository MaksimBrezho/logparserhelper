import os
import tkinter as tk
from tkinter import ttk, messagebox

from gui.transform_editor import TransformEditorDialog
from utils import json_utils, code_generator


class CodeGeneratorDialog(tk.Toplevel):
    """Dialog for configuring and generating CEF converter code."""

    MANDATORY_FIELDS = [
        "deviceVendor",
        "deviceProduct",
        "deviceVersion",
        "signatureID",
        "name",
        "severity",
    ]

    def __init__(self, parent, per_log_patterns=None, logs=None):
        super().__init__(parent)
        self.title("CEF Code Generator Dialog")
        self.minsize(700, 500)
        self.per_log_patterns = per_log_patterns or []
        self.logs = logs or []
        self.mappings = []

        self._build_ui()

    def _build_ui(self):
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

        self.mapping_frame = ttk.LabelFrame(self, text="Fields Auto-Mapped from Regex Patterns")
        self.mapping_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.mapping_list = ttk.Frame(self.mapping_frame)
        self.mapping_list.pack(fill="both", expand=True)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text="+ Add Field", command=self._on_add_field).pack(side="left", padx=5)
        ttk.Button(btns, text="Preview Code ▸", command=self._on_preview).pack(side="right", padx=5)
        ttk.Button(btns, text="Generate Python", command=self._on_generate).pack(side="right", padx=5)

        for key in self.MANDATORY_FIELDS:
            self.mappings.append({"cef": key, "pattern": "", "transform": "none"})

        self._refresh_mapping_list()

    # ------------------------------------------------------------------
    # helpers
    def _collect_patterns(self) -> list:
        patterns = {p["name"]: p for p in json_utils.load_all_patterns()}
        for p in self.per_log_patterns:
            patterns[p.get("name")] = p
        return [
            {"name": name, "regex": pat.get("regex", pat.get("pattern", ""))}
            for name, pat in patterns.items()
        ]

    def _find_example(self, regex: str) -> str:
        import re

        try:
            pat = re.compile(regex)
        except re.error:
            return ""
        for line in self.logs:
            m = pat.search(line)
            if m:
                return m.group(0)
        return ""

    def _choose_cef_field(self):
        keys = json_utils.load_cef_field_keys()
        if not keys:
            messagebox.showerror("Error", "No CEF fields available")
            return None
        dlg = tk.Toplevel(self)
        dlg.title("Choose CEF Field")
        var = tk.StringVar(value=keys[0])
        combo = ttk.Combobox(dlg, values=keys, textvariable=var, state="readonly")
        combo.pack(padx=10, pady=10)
        result = {"val": None}

        def ok():
            result["val"] = var.get()
            dlg.destroy()

        ttk.Button(dlg, text="OK", command=ok).pack(pady=5)
        dlg.grab_set()
        self.wait_window(dlg)
        return result["val"]

    def _on_add_field(self):
        field = self._choose_cef_field()
        if not field:
            return
        self.mappings.append({"cef": field, "pattern": "", "transform": "none"})
        self._refresh_mapping_list()

    def _on_pattern_changed(self, idx, var):
        self.mappings[idx]["pattern"] = var.get()
        self._refresh_mapping_list()

    def _on_edit_transform(self, idx):
        m = self.mappings[idx]
        dlg = TransformEditorDialog(self, m["cef"], current=m["transform"])
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.result is not None:
            m["transform"] = dlg.result
            self._refresh_mapping_list()

    def _gather_mappings(self):
        return [
            {"cef": m["cef"], "pattern": m["pattern"], "group": 0, "transform": m["transform"]}
            for m in self.mappings
            if m["pattern"]
        ]

    # ------------------------------------------------------------------
    def _on_preview(self):
        import tempfile, pathlib

        header = {k: v.get() for k, v in self.header_vars.items()}
        mappings = self._gather_mappings()
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
        mappings = self._gather_mappings()
        patterns = self._collect_patterns()
        out_dir = os.path.join(os.getcwd(), "generated_cef")
        try:
            code_generator.generate_files(header, mappings, patterns, out_dir)
            messagebox.showinfo("Success", f"Files written to {out_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ------------------------------------------------------------------
    def _refresh_mapping_list(self):
        for child in self.mapping_list.winfo_children():
            child.destroy()

        headers = ["CEF Field", "Pattern", "Regex", "Transform", "Example"]
        for col, text in enumerate(headers):
            ttk.Label(self.mapping_list, text=text, font=("Segoe UI", 9, "bold")).grid(row=0, column=col, sticky="w", padx=2)

        pattern_map = {p["name"]: p for p in self._collect_patterns()}
        all_names = list(pattern_map.keys())

        for idx, m in enumerate(self.mappings, start=1):
            regex = pattern_map.get(m["pattern"], {}).get("regex", "")
            example = self._find_example(regex)
            ttk.Label(self.mapping_list, text=m["cef"]).grid(row=idx, column=0, sticky="w", padx=2)
            var = tk.StringVar(value=m["pattern"])
            combo = ttk.Combobox(self.mapping_list, values=all_names, textvariable=var, state="readonly")
            combo.grid(row=idx, column=1, sticky="ew", padx=2)
            combo.bind("<<ComboboxSelected>>", lambda e, i=idx-1, v=var: self._on_pattern_changed(i, v))
            ttk.Label(self.mapping_list, text=regex).grid(row=idx, column=2, sticky="w", padx=2)
            ttk.Button(self.mapping_list, text=m["transform"], command=lambda i=idx-1: self._on_edit_transform(i)).grid(row=idx, column=3, sticky="w", padx=2)
            ttk.Label(self.mapping_list, text=example).grid(row=idx, column=4, sticky="w", padx=2)

        self.mapping_list.grid_columnconfigure(1, weight=1)

