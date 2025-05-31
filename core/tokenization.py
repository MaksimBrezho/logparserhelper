import re
from typing import List, Tuple

class TokenizedExample:
    def __init__(self, raw: str):
        self.raw = raw
        self.tokens: List[str] = []
        self.separators: List[str] = []
        self.token_separator_pairs: List[Tuple[str, str]] = []

        self._tokenize()

    def _tokenize(self):
        pattern = r'(\W+)'  # всё, что не является буквенно-цифровым символом, — разделитель
        parts = re.split(pattern, self.raw)
        parts = [p for p in parts if p != '']  # удалим пустые

        for i in range(0, len(parts), 2):
            token = parts[i]
            sep = parts[i+1] if i+1 < len(parts) else ''
            self.tokens.append(token)
            self.separators.append(sep)
            self.token_separator_pairs.append((token, sep))

    def __repr__(self):
        return f"TokenizedExample({self.token_separator_pairs})"
