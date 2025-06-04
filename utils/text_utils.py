import os


def common_prefix(words):
    if not words:
        return ''
    prefix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(prefix), len(w))
        while i < max_i and prefix[i] == w[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


def common_suffix(words):
    if not words:
        return ''
    suffix = words[0]
    for w in words[1:]:
        i = 0
        max_i = min(len(suffix), len(w))
        while i < max_i and suffix[-1 - i] == w[-1 - i]:
            i += 1
        suffix = suffix[len(suffix)-i:]
        if not suffix:
            break
    return suffix
