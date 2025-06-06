import re
from typing import Sequence


def reorder_log_line(line: str, pattern: str, order: Sequence[int]) -> str:
    """Rearrange matched groups in ``line`` using ``pattern`` and ``order``.

    Parameters
    ----------
    line : str
        The log line to transform.
    pattern : str
        Regular expression with capturing groups.
    order : Sequence[int]
        1-based indices specifying the new order of the captured groups.

    Returns
    -------
    str
        The line with the first regex match replaced by the groups in the
        specified order. If the pattern does not match, the original line is
        returned unchanged.
    """
    regex = re.compile(pattern)
    match = regex.search(line)
    if not match:
        return line

    groups = match.groups()
    if any(i < 1 or i > len(groups) for i in order):
        raise ValueError("Invalid group order")

    new_segment = " ".join(groups[i - 1] for i in order)
    start, end = match.span()
    return line[:start] + new_segment + line[end:]
