"""The little markdown the tool needs: fences, links, and prose outside code."""

import re
from collections.abc import Callable, Iterator
from typing import Final

FENCE: Final = re.compile(r"^ {0,3}(`{3,}|~{3,})")
LINK: Final = re.compile(r"\[(?P<text>[^\]\n]*)\]\((?P<url>[^)\s]+)\)")
_CODE_OR_URL: Final = re.compile(r"(`[^`\n]*`|\]\([^)\n]*\))")


def fenced_lines(text: str) -> Iterator[tuple[str, bool]]:
    """Each line, with True when it opens, closes or sits inside a fence."""
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        opened = FENCE.match(line)
        if opened:
            char = opened.group(1)[0]
            if fence is None:
                fence = char
            elif char == fence:
                fence = None
            yield line, True
            continue
        yield line, fence is not None


def map_prose(text: str, change: Callable[[str], str]) -> str:
    """Apply `change` to the prose only: not in fences, inline code or link URLs."""
    out: list[str] = []
    for line, fenced in fenced_lines(text):
        if fenced:
            out.append(line)
            continue
        parts = _CODE_OR_URL.split(line)
        out.append("".join(change(p) if i % 2 == 0 else p for i, p in enumerate(parts)))
    return "".join(out)


def line_of(text: str, offset: int) -> int:
    """The 1-based line number of a character offset."""
    return text.count("\n", 0, offset) + 1
