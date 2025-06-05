import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.code_generator_dialog import CodeGeneratorDialog
from utils import json_utils


def test_find_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "error 42"]
    assert dlg._find_example(r"user=\w+") == "user=john"
    assert dlg._find_example(r"error") == "error"


def test_initial_mappings_duplicate(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = [
        {"name": "deviceVendor", "regex": "foo"},
        {"name": "deviceVendor", "regex": "bar"},
    ]
    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: dlg.per_log_patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["deviceVendor"])
    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    dv = [m for m in mappings if m["cef"] == "deviceVendor"]
    assert len(dv) == 2
