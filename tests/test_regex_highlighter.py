import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.regex_highlighter import compute_optimal_matches


def test_log_specific_overrides_builtin():
    line = "foobar"
    patterns = [
        {"regex": "foo", "source": "builtin", "name": "b"},
        {"regex": "foobar", "source": "log", "name": "l"},
    ]
    matches = compute_optimal_matches(line, patterns)
    assert len(matches) == 1
    assert matches[0]["match"] == "foobar"
    assert matches[0]["source"] == "log"

def test_keyed_patterns_overlap():
    line = "Notification time out: 5"
    patterns = [
        {"name": "A", "regex": "Notification time out", "source": "user", "log_keys": ["x"], "priority": 1000},
        {"name": "B", "regex": "Notification time out: \d+", "source": "builtin", "log_keys": ["x"], "priority": 100},
        {"name": "C", "regex": "Notification", "source": "user", "priority": 1000},
    ]
    matches = compute_optimal_matches(line, patterns, log_keys=["x"])
    names = {m["name"] for m in matches}
    assert names == {"A", "B"}

def test_nonmatching_keys_blocked():
    line = "Notification time out: 5"
    patterns = [
        {"name": "A", "regex": "Notification time out", "source": "user", "log_keys": ["x"], "priority": 1000},
        {"name": "C", "regex": "Notification", "source": "user", "priority": 1000},
    ]
    matches = compute_optimal_matches(line, patterns, log_keys=["z"])
    assert len(matches) == 1
    assert matches[0]["name"] == "A"



def test_per_log_blocks_other_sources():
    line = "alpha beta gamma"
    patterns = [
        {"name": "log_pat", "regex": "alpha beta", "source": "log"},
        {"name": "user_pat", "regex": "beta", "source": "user", "priority": 1000},
        {"name": "builtin_pat", "regex": "alpha", "source": "builtin", "priority": 100},
    ]
    matches = compute_optimal_matches(line, patterns)
    assert len(matches) == 1
    assert matches[0]["name"] == "log_pat"


