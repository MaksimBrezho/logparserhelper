import json
import logging
import os

logger = logging.getLogger(__name__)

# Папка для пользовательских файлов
USER_DATA_DIR = os.path.join("data", "user")

USER_PATTERNS_PATH = os.path.join(USER_DATA_DIR, "patterns_user.json")
BUILTIN_PATTERNS_PATH = os.path.join("data", "patterns_builtin.json")
LOG_KEY_MAP_PATH = os.path.join("data", "log_key_map.json")
BUILTIN_PATTERN_KEYS_PATH = os.path.join("data", "builtin_pattern_keys.json")
CEF_FIELDS_PATH = os.path.join("data", "cef_fields.json")

def load_builtin_pattern_keys():
    try:
        with open(BUILTIN_PATTERN_KEYS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_all_patterns():
    """Загружает объединённые пользовательские и встроенные шаблоны."""

    builtin_keys = load_builtin_pattern_keys()

    def _read(path, is_builtin=False):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data = data.get("patterns", []) if isinstance(data, dict) else data
                for p in data:
                    if "regex" not in p and "pattern" in p:
                        p["regex"] = p.pop("pattern")
                    p["source"] = "builtin" if is_builtin else "user"
                    if is_builtin:
                        p["log_keys"] = builtin_keys.get(p.get("name"), [])
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    return _read(USER_PATTERNS_PATH) + _read(BUILTIN_PATTERNS_PATH, is_builtin=True)


def save_user_patterns(patterns):
    """Сохраняет пользовательские шаблоны."""
    to_save = {"patterns": patterns}
    try:
        os.makedirs(os.path.dirname(USER_PATTERNS_PATH), exist_ok=True)
        with open(USER_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=4, ensure_ascii=False)
    except IOError as e:
        logger.error("[Ошибка сохранения] %s", e)

def save_user_pattern(new_pattern):
    patterns = load_all_patterns()
    user_patterns = [p for p in patterns if p.get("source") != "builtin"]

    # Удалить старый паттерн с тем же именем
    user_patterns = [p for p in user_patterns if p.get("name") != new_pattern.get("name")]
    user_patterns.append(new_pattern)

    save_user_patterns(user_patterns)


def load_log_key_map():
    try:
        with open(LOG_KEY_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_log_key_mapping(source_file, keys, log_name=None):
    """Сохраняет сопоставление между лог-файлом и ключами."""

    log_key = log_name if log_name else os.path.basename(source_file)
    data = load_log_key_map()
    data[log_key] = {"file": source_file, "keys": list(keys)}

    try:
        os.makedirs(os.path.dirname(LOG_KEY_MAP_PATH), exist_ok=True)
        with open(LOG_KEY_MAP_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("[Ошибка сохранения сопоставления лог-ключей] %s", e)


def get_log_keys_for_file(source_file):
    """Возвращает список ключей, связанных с файлом лога."""

    data = load_log_key_map()
    base = os.path.basename(source_file)
    for name, entry in data.items():
        if entry.get("file") == source_file or name == base:
            return entry.get("keys", [])
    return []


def get_log_name_for_file(source_file):
    """Совместимая обёртка, возвращающая имя (ключ) для файла."""

    data = load_log_key_map()
    for name, entry in data.items():
        if entry.get("file") == source_file:
            return name
    return None


def save_per_log_pattern(*args, **kwargs):
    """Устаревшая совместимая функция."""
    logger.warning("save_per_log_pattern is deprecated")


def load_cef_fields():
    """Возвращает список словарей с описанием CEF-полей."""
    try:
        with open(CEF_FIELDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("fields", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_cef_field_keys():
    """Возвращает список ключей CEF-полей."""
    return [fld.get("key") for fld in load_cef_fields() if "key" in fld]
