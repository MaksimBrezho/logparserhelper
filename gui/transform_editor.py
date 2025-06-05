import tkinter as tk
from tkinter import ttk


class TransformEditorDialog(tk.Toplevel):
    """Simple placeholder dialog for editing transformations."""

    def __init__(self, parent, cef_field: str):
        super().__init__(parent)
        self.title(f"Transform Editor for CEF Field: {cef_field}")
        self.minsize(300, 200)

        ttk.Label(self, text=f"Transform editor for {cef_field}").pack(padx=10, pady=10)
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)
