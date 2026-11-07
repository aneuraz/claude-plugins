"""Tracing facts to the specs by their `*Facts :*` lines (`[facts] orphans = "facts-lines"`).

A section of a spec closes with a line such as ``*Facts : SPL-001 à SPL-008, OCR-007a.*``.
The ids on those lines, in any spec of the specs directory but the fact-sets themselves,
are the ones the specs cite. A fact no line cites is an orphan; an id a line cites that no
fact defines is dangling. Both are faults.
"""

import re
from pathlib import Path

#: Letter suffixes carry split facts (OCR-007a); prefixes may contain digits (I18N-004).
ID_PATTERN = re.compile(r"\b([A-Z0-9]+)-(\d{3})([a-z]?)\b")
RANGE_PATTERN = re.compile(r"\b([A-Z0-9]+)-(\d{3})\s+(?:à|to)\s+([A-Z0-9]+)-(\d{3})\b")
FACTS_LINE = re.compile(r"\*Facts\s*:")


def ids_cited_in(text: str) -> set[str]:
    """Every id named in `text`, the ranges `X-001 à X-003` and `X-001 to X-003` expanded."""
    ids = {f"{prefix}-{num}{suffix}" for prefix, num, suffix in ID_PATTERN.findall(text)}
    for prefix_a, num_a, prefix_b, num_b in RANGE_PATTERN.findall(text):
        if prefix_a == prefix_b:
            ids.update(f"{prefix_a}-{n:03d}" for n in range(int(num_a), int(num_b) + 1))
    return ids


def cited_ids(specs: Path) -> set[str]:
    """The ids on the `*Facts :*` lines of every spec under `specs`."""
    lines = [
        line
        for spec in sorted(specs.glob("*.md"))
        if not spec.name.endswith("-facts.md")
        for line in spec.read_text(encoding="utf-8").splitlines()
        if FACTS_LINE.search(line)
    ]
    return ids_cited_in(" ".join(lines))
