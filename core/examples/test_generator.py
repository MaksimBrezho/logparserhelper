from core.regex_builder import build_regex_from_examples

examples = [
    "2025-05-31 15:20:44,123 ERROR",
    "2024-12-01 08:01:05,231 ERROR",
    "2023-03-17 12:00:01,004 ERROR"
]

regex = build_regex_from_examples(examples)
print("Сгенерированное регулярное выражение:")
print(regex)
