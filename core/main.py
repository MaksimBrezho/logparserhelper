from generalization import generalize_examples

if __name__ == "__main__":
    examples = [
        "2023-04-01 12:34:56 - INFO",
        "2024-05-02 13:45:10 - ERROR",
        "2025-06-03 14:55:20 - INFO"
    ]

    regex = generalize_examples(examples)
    print("Сгенерированная регулярка:")
    print(regex)
