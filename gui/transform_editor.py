import tkinter as tk
from tkinter import ttk


class TransformEditorDialog(tk.Toplevel):
    """Dialog for selecting a basic value transformation."""

    TRANSFORMS = [
        ("none", "as is"),
        ("lower", "lower case"),
        ("upper", "UPPER CASE"),
        ("capitalize", "Capitalized"),
        ("sentence", "Sentence case"),
    ]

    def __init__(self, parent, cef_field: str, current: str = "none"):
        super().__init__(parent)
        self.result = None
        self.title(f"Transform Editor for CEF Field: {cef_field}")
        self.minsize(300, 200)

        ttk.Label(self, text="Formatting:").pack(anchor="w", padx=10, pady=(10, 5))
        self.var = tk.StringVar(value=current)
        for value, label in self.TRANSFORMS:
            ttk.Radiobutton(self, text=label, variable=self.var, value=value).pack(anchor="w", padx=20)

        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=5)

    def _on_save(self):
        self.result = self.var.get()
        self.destroy()
