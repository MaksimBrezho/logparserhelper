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
