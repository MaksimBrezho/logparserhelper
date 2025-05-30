import json
import os

PATTERNS_FILE = os.path.join("data", "patterns.json")


def load_patterns():
    """Загружает шаблоны регулярных выражений из JSON-файла."""
    if not os.path.exists(PATTERNS_FILE):
        return {"date_patterns": []}

    try:
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка при чтении {PATTERNS_FILE}: {e}")
        return {"date_patterns": []}


def save_patterns(patterns: dict):
    """Сохраняет шаблоны регулярных выражений в JSON-файл."""
    try:
        with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
            json.dump(patterns, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Ошибка при записи в {PATTERNS_FILE}: {e}")
