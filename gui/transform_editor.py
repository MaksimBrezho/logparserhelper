import tkinter as tk
from tkinter import ttk

from utils.transform_logic import apply_transform


class TransformEditorDialog(tk.Toplevel):
    """Dialog for selecting a basic or advanced value transformation."""

    TRANSFORMS = [
        ("none", "as is"),
        ("lower", "lower case"),
        ("upper", "UPPER CASE"),
        ("capitalize", "Capitalized"),
        ("sentence", "Sentence case"),
    ]

    def __init__(self, parent, cef_field: str, current: object = "none", *, regex: str = "", examples: list[str] | None = None):
        super().__init__(parent)
        self.result = None
        self.title(f"Transform Editor for CEF Field: {cef_field}")
        self.minsize(300, 360)
        self.examples = examples or []
        self.regex = regex
        self.tokens = []
        self.token_order = []
        if regex:
            ttk.Label(self, text="Regex:").pack(anchor="w", padx=10, pady=(5, 0))
            regex_box = tk.Text(self, height=1, width=40)
            regex_box.insert("1.0", regex)
            regex_box.config(state="disabled")
            regex_box.pack(fill="x", padx=10)

        if self.examples:
            ttk.Label(self, text="Examples:").pack(anchor="w", padx=10, pady=(5, 0))
            self.example_box = tk.Text(self, height=min(5, len(self.examples)), width=40)
            self.example_box.pack(fill="x", padx=10)
            self.example_box.config(state="disabled")

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
        self.var.trace_add("write", lambda *_: self._update_example_box())

        ttk.Label(self, text="Value map (key=value per line):").pack(anchor="w", padx=10, pady=(10, 5))
        self.map_text = tk.Text(self, height=4, width=40)
        self.map_text.pack(fill="x", padx=10)
        if mapping_text:
            self.map_text.insert("1.0", mapping_text)
        self.map_text.bind("<KeyRelease>", lambda e: self._update_example_box())
        apply_btn = ttk.Button(self, text="Apply", command=self._update_example_box)
        apply_btn.pack(anchor="e", padx=10, pady=(0, 5))

        rep_frame = ttk.Frame(self)
        rep_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(rep_frame, text="Replace if pattern matches:").grid(row=0, column=0, sticky="w")
        self.replace_pattern_var = tk.StringVar(value=replace_pat)
        self.replace_with_var = tk.StringVar(value=replace_with)
        ttk.Entry(rep_frame, textvariable=self.replace_pattern_var).grid(row=1, column=0, sticky="ew")
        ttk.Entry(rep_frame, textvariable=self.replace_with_var).grid(row=1, column=1, sticky="ew")
        self.replace_pattern_var.trace_add("write", lambda *_: self._update_example_box())
        self.replace_with_var.trace_add("write", lambda *_: self._update_example_box())
        rep_frame.grid_columnconfigure(0, weight=1)
        rep_frame.grid_columnconfigure(1, weight=1)

        if self.regex:
            self._init_token_editor()

        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="left", padx=5)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=5)
        # initial examples rendering
        self._update_example_box()

    # ------------------------------------------------------------------
    def _init_token_editor(self):
        import re

        pat = re.compile(self.regex)
        value = None
        for ex in self.examples:
            m = pat.search(ex)
            if m:
                value = ex
                break
        if value is None:
            return

        tokens = []
        pos = m.start()
        for i in range(1, (m.lastindex or 0) + 1):
            literal = value[pos:m.start(i)]
            if literal:
                tokens.append(literal)
            tokens.append(m.group(i))
            pos = m.end(i)
        tail = value[pos:m.end()]
        if tail:
            tokens.append(tail)

        self.tokens = tokens
        self.token_order = list(range(len(tokens)))

        frame = ttk.LabelFrame(self, text="Reorder tokens (drag to move, Del to remove)")
        frame.pack(fill="x", padx=10, pady=(5, 0))
        self.token_list = tk.Listbox(frame, selectmode="browse", height=min(5, len(tokens)))
        self._refresh_token_list()
        self.token_list.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.token_list.yview)
        sb.pack(side="right", fill="y")
        self.token_list.config(yscrollcommand=sb.set)
        self.token_list.bind("<Button-1>", self._on_drag_start)
        self.token_list.bind("<B1-Motion>", self._on_drag_motion)
        self.token_list.bind("<ButtonRelease-1>", self._on_drag_stop)
        self.token_list.bind("<Delete>", lambda e: self._delete_token())

    def _refresh_token_list(self):
        if not hasattr(self, "token_list"):
            return
        self.token_list.delete(0, tk.END)
        for idx in self.token_order:
            self.token_list.insert(tk.END, self.tokens[idx])

    def _on_drag_start(self, event):
        self._drag_index = self.token_list.nearest(event.y)
        self.token_list.selection_clear(0, tk.END)
        self.token_list.selection_set(self._drag_index)

    def _on_drag_motion(self, event):
        idx = self.token_list.nearest(event.y)
        if idx != getattr(self, "_drag_index", None):
            tok = self.token_order.pop(self._drag_index)
            self.token_order.insert(idx, tok)
            self._drag_index = idx
            self._refresh_token_list()

    def _on_drag_stop(self, event):
        self._drag_index = None
        self._update_example_box()

    def _delete_token(self):
        sel = self.token_list.curselection()
        if not sel:
            return
        idx = sel[0]
        self.token_order.pop(idx)
        self._refresh_token_list()
        self._update_example_box()
    @staticmethod
    def _parse_mapping(text: str) -> dict:
        mapping = {}
        for line in text.strip().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                mapping[k.strip()] = v.strip()
        return mapping
    def _get_spec(self) -> object:
        """Return the transformation spec from current UI values."""
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
        if self.token_order:
            default = list(range(len(self.tokens)))
            if self.token_order != default:
                result["token_order"] = self.token_order
                result["regex"] = self.regex

        if list(result.keys()) == ["format"]:
            return result["format"]
        return result

    def _update_example_box(self):
        if not hasattr(self, "example_box"):
            return
        spec = self._get_spec()
        self.example_box.config(state="normal")
        self.example_box.delete("1.0", "end")
        for ex in self.examples:
            transformed = apply_transform(ex, spec)
            self.example_box.insert("end", f"{ex} -> {transformed}\n")
        self.example_box.config(state="disabled")

    def _on_save(self):
        result = self._get_spec()
        self.result = result
        self.destroy()
