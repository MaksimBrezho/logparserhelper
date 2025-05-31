import re
from RegexGenerator import RegexGenerator
from trieregex import TrieRegEx

class CombinedRegexGenerator:
    def __init__(self, examples):
        self.examples = examples

    def generate(self):
        # Шаг 1: Генерация базового выражения
        base_generator = RegexGenerator(self.examples[0])
        for example in self.examples[1:]:
            base_generator.add_example(example)
        base_pattern = base_generator.get_regex()

        # Шаг 2: Обобщение конкретных значений
        # Заменим конкретные годы на \d{4}
        pattern = re.sub(r'202\d', r'\\d{4}', base_pattern)

        # Шаг 3: Обработка переменных частей с trieregex
        # Предположим, что уровни логирования находятся после ' - ' и до следующего ' - '
        log_levels = set()
        for example in self.examples:
            match = re.search(r' - (\w+) - ', example)
            if match:
                log_levels.add(match.group(1))
        if log_levels:
            tre = TrieRegEx(*log_levels)
            log_level_pattern = tre.regex()
            pattern = re.sub(r'\\d\{4\}-\d\{2\}-\d\{2\} \d\{2\}:\d\{2\}:\d\{2\},\d\{3\} - \w+ -',
                             rf'\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}},\\d{{3}} - {log_level_pattern} -',
                             pattern)

        return pattern
