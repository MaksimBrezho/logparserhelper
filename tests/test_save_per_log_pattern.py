import json
import os
import sys
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import json_utils


def test_save_per_log_pattern(monkeypatch, tmp_path):
    temp_file = tmp_path / "per_log.json"
    monkeypatch.setattr(json_utils, "PER_LOG_PATTERNS_PATH", str(temp_file))

    json_utils.save_per_log_pattern("/var/log/app.log", "p1", {"regex": "a"}, log_name="app")
    assert temp_file.exists()
    with open(temp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "app" in data
    assert data["app"]["file"] == "/var/log/app.log"
    assert "p1" in data["app"]["patterns"]

    json_utils.save_per_log_pattern("/var/log/other.log", "p2", {"regex": "b"})
    with open(temp_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "other.log" in data
    assert data["other.log"]["file"] == "/var/log/other.log"
    assert "p2" in data["other.log"]["patterns"]


def test_get_log_name_for_file(monkeypatch, tmp_path):
    temp_file = tmp_path / "per_log.json"
    monkeypatch.setattr(json_utils, "PER_LOG_PATTERNS_PATH", str(temp_file))

    json_utils.save_per_log_pattern("/logs/app.log", "p1", {"regex": "a"}, log_name="app")
    json_utils.save_per_log_pattern("/logs/other.log", "p2", {"regex": "b"})

    assert json_utils.get_log_name_for_file("/logs/app.log") == "app"
    assert json_utils.get_log_name_for_file("/logs/other.log") == "other.log"
    assert json_utils.get_log_name_for_file("/logs/missing.log") is None
