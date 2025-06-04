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
