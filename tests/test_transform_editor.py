import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.transform_editor import TransformEditorDialog


def test_parse_mapping():
    text = "info=1\nerror=8\n"
    result = TransformEditorDialog._parse_mapping(text)
    assert result == {'info': '1', 'error': '8'}


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
    dlg.var = DummyVar('upper')
    dlg.map_text = DummyText('info=1\nerror=8\n')
    dlg.replace_pattern_var = DummyVar('foo')
    dlg.replace_with_var = DummyVar('BAR')

    spec = TransformEditorDialog._get_spec(dlg)
    assert spec == {
        'format': 'upper',
        'value_map': {'info': '1', 'error': '8'},
        'replace_pattern': 'foo',
        'replace_with': 'BAR',
    }
