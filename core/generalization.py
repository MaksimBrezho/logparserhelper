import re
from typing import List
from tokenization import TokenizedExample

def generalize_token(token: str) -> str:
    """Обобщает одиночный токен в регулярное выражение."""
    if re.fullmatch(r'\d+', token):
        return r'\d{' + str(len(token)) + '}'
    elif re.fullmatch(r'[A-Za-z]+', token):
        return r'[A-Za-z]{' + str(len(token)) + '}'
    elif re.fullmatch(r'[A-Za-z0-9]+', token):
        return r'\w{' + str(len(token)) + '}'
    else:
        return re.escape(token)  # для случаев, когда это смешанный токен

def generalize_separator(sep: str) -> str:
    """Обобщает разделитель (если нужно), иначе экранирует."""
    return re.escape(sep)

def generalize_examples(examples: List[str]) -> str:
    """Генерирует регулярное выражение на основе списка примеров."""
    tokenized = [TokenizedExample(e) for e in examples]

    if not tokenized:
        return ""

    # Проверим, что у всех одинаковое количество пар токен-разделитель
    length = len(tokenized[0].token_separator_pairs)
    if not all(len(ex.token_separator_pairs) == length for ex in tokenized):
        raise ValueError("Несогласованные структуры в примерах")

    result_parts = []
    for i in range(length):
        ith_tokens = [ex.token_separator_pairs[i][0] for ex in tokenized]
        ith_seps = [ex.token_separator_pairs[i][1] for ex in tokenized]

        token_part = generalize_token(ith_tokens[0])
        if all(t == ith_tokens[0] for t in ith_tokens):
            # одинаковые токены — можно сделать константой
            token_part = re.escape(ith_tokens[0])

        sep_part = generalize_separator(ith_seps[0])
        if not all(s == ith_seps[0] for s in ith_seps):
            # разнится — допустим любой из встречающихся
            unique = set(ith_seps)
            sep_part = f"(?:{'|'.join(map(re.escape, unique))})"

        result_parts.append(token_part + sep_part)

    return "".join(result_parts)
