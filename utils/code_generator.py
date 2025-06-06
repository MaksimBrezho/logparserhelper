"""Generate CEF converter class and helper script."""

from __future__ import annotations

import os
from textwrap import dedent
from typing import List, Dict


def generate_files(header: Dict[str, str], mappings: List[Dict], patterns: List[Dict], output_dir: str) -> list[str]:
    """Generate converter and main script files.

    Parameters
    ----------
    header : dict
        Values for CEF header fields.
    mappings : list of dict
        Mapping definitions: {'cef': key, 'pattern': pattern_name, 'group': int, 'transform': str}
    patterns : list of dict
        Available patterns with 'name' and 'regex'.
    output_dir : str
        Directory to write generated files.
    """
    os.makedirs(output_dir, exist_ok=True)

    converter_path = os.path.join(output_dir, "cef_converter.py")
    main_path = os.path.join(output_dir, "main_cef_converter.py")

    header_repr = "{\n" + ",\n".join(f"    '{k}': '{v}'" for k, v in header.items()) + "\n}"
    pattern_repr = "{\n" + ",\n".join(
        f"    '{p['name']}': re.compile(r'''{p['regex']}''')" for p in patterns) + "\n}"
    mapping_repr = "[\n" + ",\n".join(
        "    {" + ", ".join([
            f"'cef': '{m['cef']}'",
            f"'pattern': '{m.get('pattern', '')}'",
            f"'group': {int(m.get('group', 0))}",
            f"'transform': '{m.get('transform', 'none')}'",
            f"'value': '{m.get('value', '')}'",
        ]) + "}" for m in mappings) + "\n]"

    converter_code = f"""
import re
from utils.transform_logic import apply_transform

class LogToCEFConverter:
    def __init__(self):
        self.compiled_patterns = {pattern_repr}
        self.mappings = {mapping_repr}
        self.cef_header = {header_repr}

    def convert_line(self, line: str) -> str:
        matches = {{name: rgx.search(line) for name, rgx in self.compiled_patterns.items()}}
        fields = {{}}
        for m in self.mappings:
            if m.get('pattern'):
                match = matches.get(m['pattern'])
                value = match.group(m['group']) if match else ''
            else:
                value = m.get('value', '')
            fields[m['cef']] = apply_transform(value, m['transform'])
        return self._build_cef_string(fields)

    def _build_cef_string(self, fields: dict) -> str:
        h = self.cef_header
        head = f"CEF:{{h.get('CEF Version')}}|{{h.get('Device Vendor')}}|{{h.get('Device Product')}}|{{h.get('Device Version')}}|{{h.get('Event Class ID')}}|{{h.get('Event Name')}}|{{h.get('Severity (int)')}}"
        ext = ' '.join(f"{{k}}={{v}}" for k, v in fields.items() if v)
        return head + '|' + ext

    def coverage_score(self, line: str) -> float:
        matches = [rgx.search(line) for rgx in self.compiled_patterns.values()]
        covered = sum(len(m.group(0)) for m in matches if m)
        significant = ''.join(ch for ch in line if ch.isalnum())
        return 100.0 if not significant else covered / len(significant) * 100

    def log_incomplete_coverage(self, line: str, coverage: float, fp):
        fp.write(f"{{line}} | coverage={{coverage:.1f}}%\\n")
"""

    main_code = dedent("""
    from cef_converter import LogToCEFConverter

    def main():
        conv = LogToCEFConverter()
        with open('input.log', 'r', encoding='utf-8') as fin, \
             open('output.cef', 'w', encoding='utf-8') as fout, \
             open('error.log', 'w', encoding='utf-8') as ferr:
            for line in fin:
                line = line.rstrip('\n')
                cef = conv.convert_line(line)
                fout.write(cef + '\n')
                cov = conv.coverage_score(line)
                if cov < 100.0:
                    conv.log_incomplete_coverage(line, cov, ferr)

    if __name__ == '__main__':
        main()
    """)

    with open(converter_path, 'w', encoding='utf-8') as f:
        f.write(converter_code)
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(main_code)

    return [converter_path, main_path]


