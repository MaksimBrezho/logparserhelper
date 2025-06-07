import tkinter as tk
from tkinter import ttk

from utils.i18n import translate as _
from utils.window_utils import set_window_icon


class CoverageAnalysisDialog(tk.Toplevel):
    """Dialog showing log coverage statistics."""

    def __init__(self, parent, coverage: float, field_stats: dict):
        super().__init__(parent)
        set_window_icon(self)
        self.title(_("Coverage Analysis"))
        self.minsize(360, 200)

        text = tk.Text(self, height=10, width=60)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("end", _("Coverage: {value}%").format(value=f"{coverage:.1f}") + "\n\n")
        for field, (percent, missing) in field_stats.items():
            line = f"{field}: {percent:.1f}%"
            if missing:
                nums = ", ".join(str(n) for n in missing)
                line += _(" (missing: {lines})").format(lines=nums)
            text.insert("end", line + "\n")
        text.config(state="disabled")

        btn = ttk.Button(self, text="OK", command=self.destroy)
        btn.pack(pady=(0, 10))
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.transient(parent)

