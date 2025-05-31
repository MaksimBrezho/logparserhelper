from core.regex_builder import build_regex_from_examples

def main():
    test_cases = {
        "Case 1 — Стандартный лог": [
            "2025-05-31 15:20:44,123 ERROR",
            "2024-12-01 08:01:05,231 ERROR",
            "2023-03-17 12:00:01,004 INFO"
        ],
        "Case 2 — Коды и уровни": [
            "2023-03-17 01:02:03 DEBUG",
            "2023-03-17 01:02:03 INFO",
            "2023-03-17 01:02:03 WARNING",
            "2023-03-17 01:02:03 ERROR"
        ],
        "Case 3 — IP-адреса": [
            "192.168.0.1 connected",
            "10.0.0.255 disconnected",
            "172.16.0.5 error"
        ],
        "Case 4 — UUID-like идентификаторы": [
            "User ID: 550e8400-e29b-41d4-a716-446655440000",
            "Session: 6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "Token: 123e4567-e89b-12d3-a456-426614174000"
        ],
        "Case 5 — Смешанный формат": [
            "100",
            "50000",
            "2"
        ],
    }

    for title, examples in test_cases.items():
        print(f"\n{title}:")
        regex = build_regex_from_examples(examples)
        print(regex)

if __name__ == "__main__":
    main()
