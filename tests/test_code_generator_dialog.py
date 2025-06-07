from gui.code_generator_dialog import CodeGeneratorDialog
from utils import json_utils


def test_find_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "error 42"]
    assert dlg._find_example(r"user=\w+") == "user=john"
    assert dlg._find_example(r"error") == "error"


def test_find_examples():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "user=jane", "something else"]
    result = dlg._find_examples(r"user=(\w+)")
    assert result == ["user=john", "user=jane"]

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


def test_dialog_init_no_duplicate(monkeypatch):
    patterns = [{"name": "deviceVendor", "regex": "foo"}]

    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["deviceVendor"])

    monkeypatch.setattr(CodeGeneratorDialog, "_build_ui", lambda self: None)
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = patterns
    dlg.logs = []
    dlg.mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    CodeGeneratorDialog._build_ui(dlg)

    dv = [m for m in dlg.mappings if m["cef"] == "deviceVendor"]
    assert len(dv) == 1


def test_initial_mappings_from_fields(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)

    patterns = [
        {"name": "Date L", "regex": "foo", "fields": ["start"]},
        {"name": "Time Range", "regex": "bar", "fields": ["start", "end"]},
    ]

    dlg.per_log_patterns = patterns
    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["start", "end"])

    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    start = [m["pattern"] for m in mappings if m["cef"] == "start"]
    end = [m["pattern"] for m in mappings if m["cef"] == "end"]

    assert start.count("Date L") == 1
    assert start.count("Time Range") == 1
    assert end == ["Time Range"]


def test_get_transformed_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john"]
    result = CodeGeneratorDialog._get_transformed_example(dlg, r"user=\w+", "upper")
    assert result == "USER=JOHN"


def test_get_transformed_example_constant():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = []
    result = CodeGeneratorDialog._get_transformed_example(dlg, "", "lower", value="ACME")
    assert result == "acme"


def test_initial_mappings_time_transform(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)

    patterns = [
        {"name": "TimePat", "regex": "foo", "fields": ["rt"]},
    ]

    dlg.per_log_patterns = patterns
    monkeypatch.setattr(CodeGeneratorDialog, "_collect_patterns", lambda self: patterns)
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["rt"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "rt", "category": "Time"}])

    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    tran = [m["transform"] for m in mappings if m["cef"] == "rt"]
    assert tran == ["time"]


def test_dialog_merges_new_patterns(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = [{"name": "NewPat", "regex": "n", "fields": ["deviceVendor"]}]
    dlg.logs = []
    dlg.log_key = "app"

    config = {
        "header": {},
        "mappings": [{"cef": "deviceVendor", "pattern": "OldPat", "transform": "none", "value": ""}],
    }
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "deviceVendor"}])

    initial = CodeGeneratorDialog._build_initial_mappings(dlg)
    merged = CodeGeneratorDialog._merge_mappings(dlg, config["mappings"], initial)

    names = {m.get("pattern") for m in merged if m.get("cef") == "deviceVendor"}
    assert names == {"OldPat", "NewPat"}


def test_initial_mappings_signature_id_incremental(monkeypatch):
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.per_log_patterns = []
    monkeypatch.setattr(json_utils, "load_cef_field_keys", lambda: ["signatureID"])
    monkeypatch.setattr(json_utils, "load_cef_fields", lambda: [{"key": "signatureID"}])
    mappings = CodeGeneratorDialog._build_initial_mappings(dlg)
    sig = [m for m in mappings if m["cef"] == "signatureID"][0]
    assert sig.get("rule") == "incremental"


def test_gather_mappings_handles_rule():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.mappings = [{"cef": "signatureID", "rule": "incremental", "transform": "none"}]
    result = CodeGeneratorDialog._gather_mappings(dlg)
    assert result == [{"cef": "signatureID", "rule": "incremental", "transform": "none"}]

