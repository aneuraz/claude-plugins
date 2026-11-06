"""The wiki's pages as read from the tree."""

import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from claude_plugins_tools.wiki.markdown import LINK
from claude_plugins_tools.wiki.model import FrontMatterError, split_front_matter

#: Files of the wiki directory that are not pages.
SPECIAL: Final = frozenset({"index.md", "log.md"})


@dataclass(frozen=True)
class Page:
    path: str
    raw: dict[str, object] | None
    body: str
    text: str
    #: Why the front matter could not be read; None when it could.
    error: str | None = None


def load_pages(root: Path, wiki: Path) -> list[Page]:
    """The pages under `root / wiki`, the wiki's directory."""
    base = root / wiki
    if not base.is_dir():
        return []
    pages: list[Page] = []
    for file in sorted(base.rglob("*.md")):
        if file.relative_to(base).as_posix() in SPECIAL:
            continue
        text = file.read_text(encoding="utf-8")
        path = file.relative_to(root).as_posix()
        try:
            raw, body = split_front_matter(text)
        except FrontMatterError as error:
            pages.append(Page(path, None, text, text, str(error)))
        else:
            pages.append(Page(path, raw, body, text))
    return pages


def internal_links(path: str, text: str) -> list[tuple[int, str]]:
    """Each relative link of a file: its line, and the repository path it points at."""
    found: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for match in LINK.finditer(line):
            url = match["url"]
            if "://" in url or url.startswith(("#", "mailto:")):
                continue
            target = url.partition("#")[0]
            found.append(
                (number, posixpath.normpath(posixpath.join(posixpath.dirname(path), target)))
            )
    return found
