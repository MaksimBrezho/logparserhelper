# Повторная реализация после сброса состояния среды

from typing import List, Optional
import re

class EnumRegexGenerator:
    def __init__(self, words: List[str], group_name: Optional[str] = None,
                 optional: bool = False, ignore_case: bool = False, sort_by_length: bool = False):
        self.words = sorted(set(words), key=lambda w: -len(w) if sort_by_length else w)
        self.group_name = group_name
        self.optional = optional
        self.ignore_case = ignore_case

    def generate(self) -> str:
        base = '|'.join(map(re.escape, self.words))
        base = f"(?:{base})"

        if self.ignore_case:
            base = f"(?i:{base})"
        if self.group_name:
            base = f"(?P<{self.group_name}>{base})"
        if self.optional:
            base = f"(?:{base})?"

        return base


# Пример использования
words = ['INFO', 'WARN', 'ERROR']
generator = EnumRegexGenerator(words, group_name='level', ignore_case=True, optional=False, sort_by_length=True)
regex = generator.generate()
regex
