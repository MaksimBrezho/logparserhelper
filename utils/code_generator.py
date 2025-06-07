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
        Mapping definitions. Supported keys:
        - 'cef': target CEF field name
        - 'pattern': source pattern name
        - 'group': capture group number (optional)
        - 'groups': list of capture groups to combine (optional)
        - 'transform': transformation definition
        - 'value': constant value if no pattern
        - 'value_map': mapping of values
        - 'replace_pattern': regex for replacement check
        - 'replace_with': replacement value
        - 'rule': special rule like 'incremental'
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
        "    " + repr(m) for m in mappings
    ) + "\n]"

    converter_code = f"""
import re
from utils.transform_logic import apply_transform

class LogToCEFConverter:
    def __init__(self):
        self.compiled_patterns = {pattern_repr}
        self.mappings = {mapping_repr}
        self.cef_header = {header_repr}
        self._sig_counter = -1

    def convert_line(self, line: str) -> str:
        matches = {{name: rgx.search(line) for name, rgx in self.compiled_patterns.items()}}
        fields = {{}}
        for m in self.mappings:
            if m.get('rule') == 'incremental':
                self._sig_counter += 1
                value = str(self._sig_counter)
            elif m.get('pattern'):
                match = matches.get(m['pattern'])
                if match:
                    if 'groups' in m:
                        parts = [match.group(g) for g in m['groups']]
                        value = ' '.join(parts)
                    else:
                        value = match.group(m.get('group', 0))
                else:
                    value = ''
            else:
                value = m.get('value', '')

            if m.get('replace_pattern'):
                if re.fullmatch(m['replace_pattern'], value):
                    value = m.get('replace_with', '')
            if m.get('value_map'):
                mapping = m['value_map']
                if value in mapping:
                    value = mapping[value]
                else:
                    for k, v in mapping.items():
                        if k in value:
                            value = value.replace(k, v)

            fields[m['cef']] = apply_transform(value, m.get('transform', 'none'))
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


