import pytest
from core.tokenizer.tree_tokenizer import build_token_tree  # путь может отличаться в зависимости от структуры проекта

@pytest.mark.parametrize("input_str, expected", [
    ("abc def", [("abc", "token"), (" ", "sep"), ("def", "token")]),
    ("192.168.0.1", [("192", "token"), (".", "sep"), ("168", "token"), (".", "sep"), ("0", "token"), (".", "sep"), ("1", "token")]),
    ("key=value", [("key", "token"), ("=", "sep"), ("value", "token")]),
    ("ERROR: something bad happened", [
        ("ERROR", "token"), (": ", "sep"), ("something", "token"), (" ", "sep"), ("bad", "token"), (" ", "sep"), ("happened", "token")
    ]),
    ("", []),
    ("   ", [("   ", "sep")]),
    ("abc123", [("abc123", "token")]),
    ("abc!123", [("abc", "token"), ("!", "sep"), ("123", "token")]),
    ("a_b-c", [("a", "token"), ("_", "sep"), ("b", "token"), ("-", "sep"), ("c", "token")]),
])
def test_tokenize(input_str, expected):
    result = build_token_tree(input_str)
    assert result == expected, f"Failed for input: {input_str}"
