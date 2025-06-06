import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.transform_logic import apply_transform


def test_apply_transform_modes():
    assert apply_transform('TeSt', 'lower') == 'test'
    assert apply_transform('TeSt', 'upper') == 'TEST'
    assert apply_transform('john', 'capitalize') == 'John'
    assert apply_transform('hello WORLD', 'sentence') == 'Hello world'
    assert apply_transform('Same', 'none') == 'Same'


def test_apply_transform_dict_map():
    spec = {
        'format': 'upper',
        'value_map': {'info': '1', 'error': '8'},
    }
    assert apply_transform('info', spec) == '1'
    assert apply_transform('error', spec) == '8'


def test_apply_transform_dict_replace():
    spec = {
        'format': 'none',
        'replace_pattern': r'foo',
        'replace_with': 'BAR'
    }
    assert apply_transform('foo', spec) == 'BAR'
    assert apply_transform('baz', spec) == 'baz'
