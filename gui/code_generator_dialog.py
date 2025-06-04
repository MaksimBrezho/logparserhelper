import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

from utils.json_utils import (
    load_per_log_keys,
    load_per_log_patterns_for,
    load_cef_field_keys,
)


class FieldMappingDialog(tk.Toplevel):
    """Dialog to add a CEF field mapping."""

    def __init__(self, parent, cef_fields, pattern_names):
        super().__init__(parent)
        self.title("Add Field Mapping")
        self.result = None

        self.cef_var = tk.StringVar()
        self.pattern_var = tk.StringVar()

        ttk.Label(self, text="CEF Field:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(self, textvariable=self.cef_var, values=cef_fields, state="readonly", width=25).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(self, text="Pattern:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(self, textvariable=self.pattern_var, values=pattern_names, state="readonly", width=25).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(self, text="OK", command=self._on_ok).grid(row=2, column=0, columnspan=2, pady=5)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _on_ok(self):
        if self.cef_var.get() and self.pattern_var.get():
            self.result = (self.cef_var.get(), self.pattern_var.get())
        self.destroy()


class CodeGeneratorDialog(tk.Toplevel):
    """Window for generating Python code that converts logs to CEF."""

    def __init__(self, parent, default_key=None):
        super().__init__(parent)
        self.title("CEF Code Generator")
        self.minsize(700, 500)

        self.per_log_keys = load_per_log_keys()
        init_key = default_key if default_key in self.per_log_keys else (self.per_log_keys[0] if self.per_log_keys else "")
        self.key_var = tk.StringVar(value=init_key)

        # Header values
        self.version_var = tk.StringVar(value="0.1")
        self.vendor_var = tk.StringVar(value="ACME")
        self.product_var = tk.StringVar(value="LogParserPro")
        self.dev_version_var = tk.StringVar(value="1.0.0")
        self.event_id_var = tk.StringVar(value="42")
        self.event_name_var = tk.StringVar(value="Event")
        self.severity_var = tk.StringVar(value="5")

        self.cef_fields = load_cef_field_keys()
        self.pattern_names = []
        self.field_mappings = []  # list of (cef_field, pattern_name)

        self._build_ui()
        self._update_pattern_names()

    def _build_ui(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", padx=10, pady=5)

        ttk.Label(frm, text="Source Pattern Key:").grid(row=0, column=0, sticky="w")
        key_box = ttk.Combobox(frm, textvariable=self.key_var, values=self.per_log_keys, state="readonly", width=30)
        key_box.grid(row=0, column=1, sticky="w", padx=5)
        self.key_var.trace_add("write", lambda *_: self._update_pattern_names())

        row = 1
        for label, var in [
            ("CEF Version:", self.version_var),
            ("Device Vendor:", self.vendor_var),
            ("Device Product:", self.product_var),
            ("Device Version:", self.dev_version_var),
            ("Event Class ID:", self.event_id_var),
            ("Event Name:", self.event_name_var),
            ("Severity (int):", self.severity_var),
        ]:
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Entry(frm, textvariable=var, width=32).grid(row=row, column=1, sticky="w", padx=5)
            row += 1

        mapping_frame = ttk.LabelFrame(self, text="Field Mappings")
        mapping_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("cef_field", "pattern")
        self.tree = ttk.Treeview(mapping_frame, columns=columns, show="headings")
        self.tree.heading("cef_field", text="CEF Field")
        self.tree.heading("pattern", text="Pattern")
        self.tree.pack(fill="both", expand=True, side="left")

        scroll = ttk.Scrollbar(mapping_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)
        ttk.Button(btns, text="+ Add Field", command=self._add_field).pack(side="left", padx=5)
        ttk.Button(btns, text="Preview Code", command=self._preview_code).pack(side="left", padx=5)
        ttk.Button(btns, text="Generate Python", command=self._generate_code).pack(side="right", padx=5)

    def _update_pattern_names(self):
        key = self.key_var.get()
        self.pattern_names = list(load_per_log_patterns_for(key).keys()) if key else []

    def _add_field(self):
        dlg = FieldMappingDialog(self, self.cef_fields, self.pattern_names)
        self.wait_window(dlg)
        if getattr(dlg, "result", None):
            cef_key, pattern_name = dlg.result
            self.field_mappings.append((cef_key, pattern_name))
            self.tree.insert("", "end", values=(cef_key, pattern_name))

    def _preview_code(self):
        code = self._generate_code_str()
        win = tk.Toplevel(self)
        win.title("Generated Code")
        txt = scrolledtext.ScrolledText(win, width=80, height=25)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", code)
        txt.config(state="disabled")

    def _generate_code(self):
        code = self._generate_code_str()
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python", "*.py")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            messagebox.showinfo("Success", "File saved")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _generate_code_str(self) -> str:
        header = f"CEF:{self.version_var.get()}|{self.vendor_var.get()}|{self.product_var.get()}|{self.dev_version_var.get()}|{self.event_id_var.get()}|{self.event_name_var.get()}|{self.severity_var.get()}|"
        mapping_lines = [f"{cef}={{values.get('{pat}', '')}}" for cef, pat in self.field_mappings]
        body = " ".join(mapping_lines)
        code = [
            "class LogToCEFConverter:",
            "    def convert_line(self, line):",
            "        values = {}  # TODO: extract values using patterns",
            f"        return '{header} ' + '{body}'",
            "",
            "def main():",
            "    import sys",
            "    conv = LogToCEFConverter()",
            "    for ln in sys.stdin:",
            "        print(conv.convert_line(ln.strip()))",
            "",
            "if __name__ == '__main__':",
            "    main()",
        ]
        return "\n".join(code)
