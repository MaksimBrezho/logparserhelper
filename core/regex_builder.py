from typing import List
from .tokenizer import tokenize
from .generalizer import generalize_token
from .enum_generator import EnumRegexGenerator
import re

def build_regex_from_examples(lines: List[str], ignore_case=False) -> str:
    token_columns = []
    sep_columns = []
    case_insensitive = ignore_case  # по умолчанию — False, включим при необходимости

    for line in lines:
        pairs = tokenize(line.strip())
        tokens = [t for t, kind in pairs if kind == 'token']
        seps = [t for t, kind in pairs if kind == 'sep']

        if not token_columns:
            token_columns = [[] for _ in tokens]
            sep_columns = [[] for _ in seps]

        for i, token in enumerate(tokens):
            token_columns[i].append(token)

        for i, sep in enumerate(seps):
            sep_columns[i].append(sep)

    token_patterns = []
    for column in token_columns:
        unique_values = list(set(column))
        if all(re.fullmatch(r'[A-Z]+', t) for t in unique_values) and len(unique_values) > 1:
            pattern = EnumRegexGenerator(unique_values).generate()
            case_insensitive = True  # поскольку используем слова в верхнем регистре
        else:
            pattern = generalize_token(column[0])
        token_patterns.append(pattern)

    sep_patterns = [re.escape(seps[0]) for seps in sep_columns]

    # Сборка финального шаблона
    result = []
    for i in range(len(token_patterns)):
        result.append(token_patterns[i])
        if i < len(sep_patterns):
            result.append(sep_patterns[i])

    final_pattern = ''.join(result)
    if case_insensitive:
        final_pattern = f"(?i){final_pattern}"
    return final_pattern
