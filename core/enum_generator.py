import re
from typing import List

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class EnumRegexGenerator:
    def __init__(self, words: List[str]):
        self.root = TrieNode()
        for word in words:
            self._insert(word)

    def _insert(self, word: str):
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_end = True

    def _build_regex(self, node: TrieNode) -> str:
        if not node.children:
            return ''
        parts = []
        for char, child in sorted(node.children.items()):
            subpattern = re.escape(char) + self._build_regex(child)
            if child.is_end:
                parts.append(subpattern + '?')
            else:
                parts.append(subpattern)
        if node.is_end:
            parts.append('')
        if len(parts) == 1:
            return parts[0]
        return '(?:' + '|'.join(parts) + ')'

    def generate(self) -> str:
        return self._build_regex(self.root)

if __name__ == "__main__":
    words = ['INFO', 'WARN', 'ERROR']
    generator = EnumRegexGenerator(words)
    regex = generator.generate()
    print("Сгенерированное регулярное выражение:")
    print(regex)
