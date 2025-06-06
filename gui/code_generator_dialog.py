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


        self.mappings = self._build_initial_mappings()
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
        for label, default in fields:
            var = tk.StringVar(value=default)
            self.header_vars[label] = var

        ttk.Label(header, text="CEF Version:").grid(row=0, column=0, sticky="w", pady=2, padx=2)
        entry = ttk.Entry(header, textvariable=self.header_vars["CEF Version"], state="disabled")
        entry.grid(row=0, column=1, sticky="ew", pady=2, padx=2)
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

        self._refresh_mapping_list()

    def _build_initial_mappings(self):
        # Only consider patterns that are present for this log file
        patterns = list(self.per_log_patterns)
        cef_keys = set(json_utils.load_cef_field_keys())

        by_field = {}
        for p in patterns:
            name = p.get("name")
            fields = p.get("fields", [])

            for fld in fields:
                if fld in cef_keys:
                    by_field.setdefault(fld, []).append(name)

            if name in cef_keys:
                by_field.setdefault(name, []).append(name)

        mappings: list[dict] = []
        for field in self.MANDATORY_FIELDS:
            names = by_field.get(field, [])
            if not names:
                mappings.append({"cef": field, "pattern": "", "value": "", "transform": "none"})
            else:
                for n in names:
                    mappings.append({"cef": field, "pattern": n, "value": "", "transform": "none"})

        for field, names in by_field.items():
            if field in self.MANDATORY_FIELDS:
                continue
            for n in names:
                mappings.append({"cef": field, "pattern": n, "value": "", "transform": "none"})

        return mappings

    # ------------------------------------------------------------------
    # helpers
    def _collect_patterns(self) -> list:
        patterns = {p["name"]: p for p in json_utils.load_all_patterns()}
        for p in self.per_log_patterns:
            patterns[p.get("name")] = p

        result = []
        for name, pat in patterns.items():
            entry = {
                "name": name,
                "regex": pat.get("regex", pat.get("pattern", "")),
            }
            if "fields" in pat:
                entry["fields"] = pat["fields"]
            result.append(entry)
        return result

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
        self.mappings.append({"cef": field, "pattern": "", "value": "", "transform": "none"})
        self._refresh_mapping_list()

    def _on_pattern_changed(self, idx, var):
        self.mappings[idx]["pattern"] = var.get()
        if var.get():
            self.mappings[idx]["value"] = ""
        self._refresh_mapping_list()

    def _on_value_changed(self, idx, var):
        self.mappings[idx]["value"] = var.get()

    def _on_edit_transform(self, idx):
        m = self.mappings[idx]
        dlg = TransformEditorDialog(self, m["cef"], current=m["transform"])
        dlg.grab_set()
        self.wait_window(dlg)
        if dlg.result is not None:
            m["transform"] = dlg.result
            self._refresh_mapping_list()

    def _gather_mappings(self):
        result = []
        for m in self.mappings:
            if m.get("pattern"):
                result.append({"cef": m["cef"], "pattern": m["pattern"], "group": 0, "transform": m["transform"]})
            elif m.get("value"):
                result.append({"cef": m["cef"], "value": m["value"], "transform": m["transform"]})
        return result


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

        counts = {}
        for m in self.mappings:
            counts[m["cef"]] = counts.get(m["cef"], 0) + 1
        used = {}

        for idx, m in enumerate(self.mappings, start=1):
            regex = pattern_map.get(m.get("pattern"), {}).get("regex", "")
            example = self._find_example(regex) if regex else ""

            label = m["cef"]
            if counts.get(label, 0) > 1:
                used[label] = used.get(label, 0) + 1
                label = f"{label} {used[label]}"
            ttk.Label(self.mapping_list, text=label).grid(row=idx, column=0, sticky="w", padx=2)
            if m.get("pattern"):
                var = tk.StringVar(value=m["pattern"])
                combo = ttk.Combobox(self.mapping_list, values=all_names, textvariable=var, state="readonly")
                combo.grid(row=idx, column=1, sticky="ew", padx=2)
                combo.bind("<<ComboboxSelected>>", lambda e, i=idx-1, v=var: self._on_pattern_changed(i, v))
            else:
                var = tk.StringVar(value=m.get("value", ""))
                entry = ttk.Entry(self.mapping_list, textvariable=var)
                entry.grid(row=idx, column=1, sticky="ew", padx=2)
                entry.bind("<KeyRelease>", lambda e, i=idx-1, v=var: self._on_value_changed(i, v))
            ttk.Label(self.mapping_list, text=regex).grid(row=idx, column=2, sticky="w", padx=2)
            btn_text = m["transform"] if isinstance(m.get("transform"), str) else "custom"
            ttk.Button(self.mapping_list, text=btn_text, command=lambda i=idx-1: self._on_edit_transform(i)).grid(row=idx, column=3, sticky="w", padx=2)
            ttk.Label(self.mapping_list, text=example).grid(row=idx, column=4, sticky="w", padx=2)

        self.mapping_list.grid_columnconfigure(1, weight=1)


