import json
import logging
import os

logger = logging.getLogger(__name__)

# Папка для пользовательских файлов
USER_DATA_DIR = os.path.join("data", "user")

USER_PATTERNS_PATH = os.path.join(USER_DATA_DIR, "patterns_user.json")
BUILTIN_PATTERNS_PATH = os.path.join("data", "patterns_builtin.json")
PER_LOG_PATTERNS_PATH = os.path.join(USER_DATA_DIR, "per_log_patterns.json")
CEF_FIELDS_PATH = os.path.join("data", "cef_fields.json")

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


def get_log_name_for_file(source_file):
    """Return previously used log_name for the given log file path.

    Parameters
    ----------
    source_file : str
        Absolute path of the log file.

    Returns
    -------
    str | None
        The log_name if the log file was already stored, otherwise ``None``.
    """
    try:
        if not os.path.exists(PER_LOG_PATTERNS_PATH):
            return None
        with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        for log_name, entry in all_data.items():
            if entry.get("file") == source_file:
                return log_name
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None

def save_per_log_pattern(source_file, pattern_name, pattern_data, log_name=None):
    """Сохраняет паттерн, привязанный к конкретному логу.

    Parameters
    ----------
    source_file : str
        Полный путь к файлу лога.
    pattern_name : str
        Имя сохраняемого паттерна.
    pattern_data : dict
        Данные паттерна.
    log_name : str | None
        Пользовательское имя для набора паттернов. Если не задано,
        используется имя файла лога.
    """
    try:
        log_key = log_name if log_name else os.path.basename(source_file)

        if os.path.exists(PER_LOG_PATTERNS_PATH):
            with open(PER_LOG_PATTERNS_PATH, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        else:
            all_data = {}

        entry = all_data.get(log_key, {"file": source_file, "patterns": {}})
        entry["file"] = source_file
        entry["patterns"][pattern_name] = {
            "regex": pattern_data["regex"],
            "fields": pattern_data.get("fields", []),
            "cef_field": pattern_data.get("cef_field"),
        }
        all_data[log_key] = entry

        os.makedirs(os.path.dirname(PER_LOG_PATTERNS_PATH), exist_ok=True)
        with open(PER_LOG_PATTERNS_PATH, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error("[Ошибка сохранения пер-лог паттерна] %s", e)


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
