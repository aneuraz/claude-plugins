"""GitHub's heading anchors (design §3): what `#anchor` links and sources point at."""

import re

_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_DROPPED = re.compile(r"[^\w\- ]")


def github_anchor(heading: str) -> str:
    text = _LINK.sub(r"\1", heading).strip().lower()
    return _DROPPED.sub("", text).replace(" ", "-")


class Anchors:
    """One document's anchors: GitHub suffixes a repeated one with -1, -2…"""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def of(self, heading: str) -> str:
        base = github_anchor(heading)
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count}"
