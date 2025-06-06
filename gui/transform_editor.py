import tkinter as tk
from tkinter import ttk


class TransformEditorDialog(tk.Toplevel):
    """Dialog for selecting a basic or advanced value transformation."""

    TRANSFORMS = [
        ("none", "as is"),
        ("lower", "lower case"),
        ("upper", "UPPER CASE"),
        ("capitalize", "Capitalized"),
        ("sentence", "Sentence case"),
    ]

    def __init__(self, parent, cef_field: str, current: object = "none"):
        super().__init__(parent)
        self.result = None
        self.title(f"Transform Editor for CEF Field: {cef_field}")
        self.minsize(300, 320)

        if isinstance(current, dict):
            fmt = current.get("format", "none")
            mapping_text = "\n".join(f"{k}={v}" for k, v in current.get("value_map", {}).items())
            replace_pat = current.get("replace_pattern", "")
            replace_with = current.get("replace_with", "")
        else:
            fmt = str(current)
            mapping_text = ""
            replace_pat = ""
            replace_with = ""

        ttk.Label(self, text="Formatting:").pack(anchor="w", padx=10, pady=(10, 5))
        self.var = tk.StringVar(value=fmt)
        for value, label in self.TRANSFORMS:
            ttk.Radiobutton(self, text=label, variable=self.var, value=value).pack(anchor="w", padx=20)

        ttk.Label(self, text="Value map (key=value per line):").pack(anchor="w", padx=10, pady=(10, 5))
        self.map_text = tk.Text(self, height=4, width=40)
        self.map_text.pack(fill="x", padx=10)
        if mapping_text:
            self.map_text.insert("1.0", mapping_text)

        rep_frame = ttk.Frame(self)
        rep_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(rep_frame, text="Replace if pattern matches:").grid(row=0, column=0, sticky="w")
        self.replace_pattern_var = tk.StringVar(value=replace_pat)
        self.replace_with_var = tk.StringVar(value=replace_with)
        ttk.Entry(rep_frame, textvariable=self.replace_pattern_var).grid(row=1, column=0, sticky="ew")
        ttk.Entry(rep_frame, textvariable=self.replace_with_var).grid(row=1, column=1, sticky="ew")
        rep_frame.grid_columnconfigure(0, weight=1)
        rep_frame.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    @staticmethod
    def _parse_mapping(text: str) -> dict:
        mapping = {}
        for line in text.strip().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                mapping[k.strip()] = v.strip()
        return mapping

    def _on_save(self):
        fmt = self.var.get()
        mapping = self._parse_mapping(self.map_text.get("1.0", "end"))
        replace_pat = self.replace_pattern_var.get().strip()
        replace_with = self.replace_with_var.get()

        result = {"format": fmt}
        if mapping:
            result["value_map"] = mapping
        if replace_pat:
            result["replace_pattern"] = replace_pat
            result["replace_with"] = replace_with

        if list(result.keys()) == ["format"]:
            self.result = result["format"]
        else:
            self.result = result
        self.destroy()
