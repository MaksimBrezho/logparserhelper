from typing import List
from .tokenizer import tokenize
from .generalizer import generalize_token
from .enum_generator import EnumRegexGenerator
import re

def build_regex_from_examples(lines: List[str]) -> str:
    token_columns = []
    sep_columns = []

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
        if all(re.fullmatch(r'[A-Z]+', t) for t in column):
            pattern = EnumRegexGenerator(column).generate()
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

    return ''.join(result)
