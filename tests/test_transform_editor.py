import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.transform_editor import TransformEditorDialog


def test_parse_mapping():
    text = "info=1\nerror=8\n"
    result = TransformEditorDialog._parse_mapping(text)
    assert result == {'info': '1', 'error': '8'}
