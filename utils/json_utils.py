import json
import os

USER_PATTERNS_PATH = os.path.join("data", "patterns_user.json")
BUILTIN_PATTERNS_PATH = os.path.join("data", "patterns_builtin.json")
PER_LOG_PATTERNS_PATH = os.path.join("data", "per_log_patterns.json")

def load_all_patterns():
    """Загружает объединённые пользовательские и встроенные шаблоны."""
    patterns = []

    def _read(path, is_builtin=False):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data = data.get("patterns", []) if isinstance(data, dict) else data
                for p in data:
                    if "regex" not in p and "pattern" in p:
                        p["regex"] = p.pop("pattern")
                    p["source"] = "builtin" if is_builtin else "user"
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    return _read(USER_PATTERNS_PATH) + _read(BUILTIN_PATTERNS_PATH, is_builtin=True)


def save_user_patterns(patterns):
    """Сохраняет пользовательские шаблоны."""
    to_save = {"patterns": patterns}
    try:
        with open(USER_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"[Ошибка сохранения] {e}")

def save_user_pattern(new_pattern):
    patterns = load_all_patterns()
    user_patterns = [p for p in patterns if p.get("source") != "builtin"]

    # Удалить старый паттерн с тем же именем
    user_patterns = [p for p in user_patterns if p.get("name") != new_pattern.get("name")]
    user_patterns.append(new_pattern)

    save_user_patterns(user_patterns)

def save_per_log_pattern(source_file, pattern_name, pattern_data):
    try:
        if os.path.exists(PER_LOG_PATTERNS_PATH):
            with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        else:
            all_data = {}

        entry = all_data.get(source_file, {"patterns": {}})
        entry["patterns"][pattern_name] = {
            "regex": pattern_data["regex"],
            "fields": pattern_data.get("fields", [])
        }
        all_data[source_file] = entry

        with open(PER_LOG_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[Ошибка сохранения пер-лог паттерна] {e}")