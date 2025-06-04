import re
from typing import List, Literal, Optional
from .enum_generator import EnumRegexGenerator
from .generalizer import generalize_token
from core.tokenizer.tree_tokenizer import build_token_tree, flatten_token_tree
from utils.text_utils import common_prefix, common_suffix

KEY_VALUE_SEPARATORS = {'=', ':', '->', '=>', '<-'}

DigitMode = Literal["standard", "always_fixed_length", "always_plus", "min_length", "fixed_and_min"]

def build_draft_regex_from_examples(
        lines: List[str], *,
        digit_mode: DigitMode = "standard",
        digit_min_length: int = 1,
        case_insensitive: bool = False,
        window_left: Optional[str] = None,
        window_right: Optional[str] = None,
        merge_text_tokens: bool = True,
        max_enum_options: int = 10,
        prefer_alternatives: bool = True,
        merge_by_common_prefix: bool = True,
) -> str:
    token_columns = []
    sep_columns = []

    for line in lines:
        tree = build_token_tree(line.strip())
        pairs = flatten_token_tree(tree)

        tokens = [val for val, kind in pairs if kind == 'token']
        seps = [val for val, kind in pairs if kind == 'sep']

        if not token_columns:
            token_columns = [[] for _ in tokens]
            sep_columns = [[] for _ in seps]

        for i, token in enumerate(tokens):
            token_columns[i].append(token)
        for i, sep in enumerate(seps):
            sep_columns[i].append(sep)

    def digit_pattern(values: List[str]) -> str:
        lengths = [len(v) for v in values]
        min_len, max_len = min(lengths), max(lengths)
        unique_vals = set(values)

        if digit_mode == "always_plus":
            return r"\d+"
        elif digit_mode == "always_fixed_length":
            return rf"\d{{{len(values[0])}}}"
        elif digit_mode == "fixed_and_min":
            if len(unique_vals) == 1:
                return rf"\d{{{len(values[0])}}}"  # точно фиксированное
            else:
                return rf"\d{{{digit_min_length},{max_len}}}"  # fallback
        elif digit_mode == "min_length":
            return rf"\d{{{digit_min_length},{max_len}}}" if digit_min_length != max_len else rf"\d{{{digit_min_length}}}"
        else:  # "standard"
            if len(unique_vals) == 1:
                return re.escape(values[0])
            elif min_len == max_len:
                return rf"\d{{{min_len}}}"
            elif max_len <= 5:
                return rf"\d{{{min_len},{max_len}}}"
            else:
                return r"\d+"

    token_patterns = []
    i = 0
    token_len = len(token_columns)
    sep_len = len(sep_columns)
    sep_i = 0

    while i < token_len:
        if i + 1 < token_len and sep_i < sep_len:
            sep = sep_columns[sep_i][0]
            if sep == ':' and not all(': ' in line or ':,' in line for line in lines):
                sep = None

            if sep in KEY_VALUE_SEPARATORS:
                keys = token_columns[i]
                values = token_columns[i + 1]

                key_pattern = re.escape(keys[0]) if len(set(keys)) == 1 else generalize_token(keys[0])

                if all(re.fullmatch(r'\d+', tok) for tok in values):
                    value_pattern = digit_pattern(values)
                elif len(set(values)) == 1:
                    value_pattern = re.escape(values[0])
                elif all(re.fullmatch(r'[A-Z]+', t) for t in values):
                    value_pattern = EnumRegexGenerator(values, ignore_case=case_insensitive, sort_by_length=True).generate()
                else:
                    value_pattern = generalize_token(values[0])

                token_patterns.append(f"{key_pattern}{re.escape(sep)}{value_pattern}")
                i += 2
                sep_i += 1
                if sep_i < sep_len:
                    token_patterns.append(re.escape(sep_columns[sep_i][0]))
                    sep_i += 1
                continue

        col = token_columns[i]
        unique_values = list(dict.fromkeys(col))

        if all(re.fullmatch(r'\d+', tok) for tok in col):
            pattern = digit_pattern(col)
        elif len(unique_values) == 1:
            pattern = re.escape(unique_values[0])
        elif prefer_alternatives and all(re.fullmatch(r'[A-Za-z]+', t) for t in unique_values) and len(unique_values) <= max_enum_options:
            if merge_by_common_prefix and len(unique_values) > 1:
                prefix = common_prefix(unique_values)
                suffix = common_suffix(unique_values)
                stripped = [t[len(prefix):len(t)-len(suffix) if suffix else len(t)] for t in unique_values]
                alt = EnumRegexGenerator(stripped, ignore_case=case_insensitive, sort_by_length=True).generate()
                pattern = f"{re.escape(prefix)}{alt}{re.escape(suffix)}"
            else:
                pattern = EnumRegexGenerator(unique_values, ignore_case=case_insensitive, sort_by_length=True).generate()
        elif all(re.fullmatch(r'[A-Z]+', t) for t in col):
            pattern = EnumRegexGenerator(col, ignore_case=case_insensitive, sort_by_length=True).generate()
        else:
            pattern = generalize_token(col[0])

        token_patterns.append(pattern)

        if sep_i < sep_len:
            token_patterns.append(re.escape(sep_columns[sep_i][0]))
            sep_i += 1

        i += 1

    core_pattern = ''.join(token_patterns)

    if window_left:
        core_pattern = f"(?<={re.escape(window_left)}){core_pattern}"
    if window_right:
        core_pattern = f"{core_pattern}(?={re.escape(window_right)})"

    core_pattern = core_pattern.strip()
    return core_pattern
