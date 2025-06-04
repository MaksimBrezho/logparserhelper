import re
import os
import sys

# Ensure the core package is importable when running tests directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.regex.regex_builder import build_draft_regex_from_examples


def test_regex_modes_digit_standard():
    logs = ['code=12', 'code=345']
    regex = build_draft_regex_from_examples(logs, digit_mode="standard")
    print(f"[standard] Regex: {regex}")
    assert re.fullmatch(regex, "code=12")
    assert re.fullmatch(regex, "code=345")
    assert not re.fullmatch(regex, "code=abc")


def test_regex_modes_digit_fixed_length():
    logs = ['2015-07-29 17:41:44,747',
            '2015-07-29 17:41:44,7476']
    regex = build_draft_regex_from_examples(logs, digit_mode="fixed_and_min", )
    print(f"[fixed length] Regex: {regex}")
    assert re.fullmatch(regex, "2015-07-29 17:41:44,123")
    assert not re.fullmatch(regex, "2015/07/29 17:41:44,747")


def test_regex_modes_digit_plus():
    logs = ['val=1', 'val=999']
    regex = build_draft_regex_from_examples(logs, digit_mode="always_plus")
    print(f"[plus] Regex: {regex}")
    assert re.fullmatch(regex, "val=1234567890")
    assert not re.fullmatch(regex, "val=abc")


def test_regex_modes_digit_min_length():
    logs = ['id=2', 'id=33', 'id=555']
    regex = build_draft_regex_from_examples(logs, digit_mode="min_length", digit_min_length=1)
    print(f"[min length] Regex: {regex}")
    assert re.fullmatch(regex, "id=33")
    assert not re.fullmatch(regex, "id=66666")


def test_regex_modes_case_insensitive():
    logs = ['type=ERROR', 'type=INFO']
    regex = build_draft_regex_from_examples(logs, case_insensitive=True)
    print(f"[case insensitive] Regex: {regex}")
    assert re.fullmatch(regex, "type=ERROR")
    assert re.fullmatch(regex, "type=info")
    assert not re.fullmatch(regex, "type=warn")


def test_regex_window_lookaround():
    logs = ['val=1', 'val=22']
    regex = build_draft_regex_from_examples(
        logs,
        window_left='start ',
        window_right=' end'
    )
    assert regex.startswith('(?<=') and '(?=' in regex
    match = re.search(regex, 'prefix start val=1 end suffix')
    print(match)
    assert match
