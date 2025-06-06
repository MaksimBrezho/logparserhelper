import sys
import os
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.transform_editor import TransformEditorDialog


def test_parse_mapping():
    text = "info=1\nerror=8\n"
    result = TransformEditorDialog._parse_mapping(text)
    assert result == {"info": "1", "error": "8"}


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, v):
        self.value = v


class DummyText:
    def __init__(self, text):
        self.text = text

    def get(self, start, end):
        return self.text


def test_get_spec():
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.var = DummyVar("upper")
    dlg.map_text = DummyText("info=1\nerror=8\n")
    dlg.replace_pattern_var = DummyVar("foo")
    dlg.replace_with_var = DummyVar("BAR")
    dlg.token_order = []
    dlg.tokens = []
    dlg.regex = ""

    spec = TransformEditorDialog._get_spec(dlg)
    assert spec == {
        "format": "upper",
        "value_map": {"info": "1", "error": "8"},
        "replace_pattern": "foo",
        "replace_with": "BAR",
    }


def test_get_spec_token_order():
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.var = DummyVar("lower")
    dlg.map_text = DummyText("")
    dlg.replace_pattern_var = DummyVar("")
    dlg.replace_with_var = DummyVar("")
    dlg.token_order = [1, 0]
    dlg.tokens = ["a", "b"]
    dlg.regex = r"(\w+) (\w+)"

    spec = TransformEditorDialog._get_spec(dlg)
    assert spec == {"format": "lower", "token_order": [1, 0], "regex": r"(\w+) (\w+)"}


def test_init_token_editor_sets_tokens(monkeypatch):
    dlg = TransformEditorDialog.__new__(TransformEditorDialog)
    dlg.regex = r"user=(\w+)"
    dlg.examples = ["user=jane"]

    # Avoid actual tkinter widgets
    class DummyWidget:
        def __init__(self, *a, **k):
            pass

        def pack(self, *a, **k):
            pass

        def bind(self, *a, **k):
            pass

        def config(self, *a, **k):
            pass

        def yview(self, *a, **k):
            pass

        def set(self, *a, **k):
            pass

    monkeypatch.setattr(ttk, "Label", DummyWidget)
    monkeypatch.setattr(ttk, "Frame", DummyWidget)
    monkeypatch.setattr(ttk, "LabelFrame", DummyWidget)
    monkeypatch.setattr(TransformEditorDialog, "_refresh_token_list", lambda self: None)

    TransformEditorDialog._init_token_editor(dlg)

    assert dlg.tokens == ["user=", "jane"]
    assert dlg.token_order == [0, 1]
