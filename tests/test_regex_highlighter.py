import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.regex_highlighter import compute_optimal_matches
from utils.text_utils import compute_char_coverage


def test_compute_optimal_matches_priorities():
    line = "abcde"
    patterns = [
        {"name": "p1", "regex": "abcde", "source": "builtin", "priority": 1},
        {"name": "p2", "regex": "abc", "source": "builtin", "priority": 2},
        {"name": "p3", "regex": "de", "source": "builtin", "priority": 2},
    ]
    result = compute_optimal_matches(line, patterns)
    names = [m["name"] for m in result]
    assert names == ["p2", "p3"]


def test_compute_optimal_matches_user_overlap():
    line = "abc"
    patterns = [
        {"name": "u1", "regex": "ab", "source": "user", "priority": 1},
        {"name": "u2", "regex": "bc", "source": "user", "priority": 1},
    ]
    result = compute_optimal_matches(line, patterns)
    names = {m["name"] for m in result}
    assert names == {"u1", "u2"}


def test_compute_optimal_matches_user_vs_builtin():
    line = "abcd"
    patterns = [
        {"name": "base", "regex": "ab", "source": "builtin", "priority": 1},
        {"name": "u1", "regex": "abc", "source": "user", "priority": 2},
        {"name": "u2", "regex": "cd", "source": "user", "priority": 3},
    ]
    result = compute_optimal_matches(line, patterns)
    names = {m["name"] for m in result}
    assert names == {"base", "u2"}


def test_compute_char_coverage_overlaps():
    logs = ["abcde"]
    matches = {
        1: [
            {"name": "p1", "start": 0, "end": 3, "match": "abc"},
            {"name": "p2", "start": 2, "end": 5, "match": "cde"},
        ]
    }
    cov = compute_char_coverage(logs, matches, {"p1", "p2"})
    assert cov == 100.0
