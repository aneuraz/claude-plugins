"""The generated index: the wiki's pages, the glossary, `[wiki] index_sections`."""

import posixpath
import re
from pathlib import Path
from typing import Final

from claude_plugins_tools.project import IndexSection, Project
from claude_plugins_tools.wiki.anchors import Anchors
from claude_plugins_tools.wiki.model import PageType, Status, wiki_dir
from claude_plugins_tools.wiki.pages import load_pages

HEADER: Final = (
    "<!-- written by `wiki index` with the project's cpt command (`[tooling] command`):"
    " edit the pages, not this file -->"
)
_TITLES: Final[dict[PageType, str]] = {
    PageType.HUB: "Hubs",
    PageType.LESSON: "Lessons",
    PageType.RULE: "Rules",
    PageType.DEFECT: "Defects",
    PageType.DEBT: "Debts",
    PageType.DECISION: "Decisions",
    PageType.REFERENCE: "Reference",
    PageType.HOWTO: "How-to",
}
_TERM: Final = re.compile(r"^\*\*(?P<term>[^*]+)\*\*:")
_HEADING: Final = re.compile(r"^#{1,6} +(.*?) *$")


def index_path(project: Project) -> Path:
    return wiki_dir(project) / "index.md"


def _up(wiki: Path) -> str:
    """From the wiki's directory back to the repository root."""
    return "/".join([".."] * len(wiki.parts))


def _pages(project: Project) -> list[str]:
    wiki = wiki_dir(project)
    lines: list[str] = []
    pages = load_pages(project.root, wiki)
    for kind in PageType:
        entries: list[tuple[str, str, str]] = []
        for page in pages:
            raw = page.raw or {}
            if raw.get("type") != kind or raw.get("status") != Status.CURRENT or "title" not in raw:
                continue
            title = str(raw["title"])
            summary = f" — {raw['summary']}" if raw.get("summary") else ""
            entries.append(
                (
                    title.casefold(),
                    page.path,
                    f"- [{title}]({Path(page.path).relative_to(wiki).as_posix()}){summary}",
                )
            )
        if entries:
            lines += ["", f"## {_TITLES[kind]}", "", *(entry for _, _, entry in sorted(entries))]
    return lines


def _terms(project: Project) -> list[str]:
    file = project.root / "CONTEXT.md"
    if not file.is_file():
        return []
    context = f"{_up(wiki_dir(project))}/CONTEXT.md"
    anchors, anchor, terms = Anchors(), "", []
    for line in file.read_text(encoding="utf-8").splitlines():
        heading = _HEADING.match(line)
        if heading:
            anchor = anchors.of(heading.group(1))
        term = _TERM.match(line)
        if term:
            target = f"{context}#{anchor}" if anchor else context
            terms.append(f"- [{term['term']}]({target})")
    return ["", "## Glossary", "", *terms] if terms else []


def _first_heading(file: Path) -> str:
    for line in file.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return file.stem


def _section(project: Project, section: IndexSection) -> list[str]:
    found = sorted((project.root / section.dir).glob(section.glob))
    if not found:
        return []
    wiki = wiki_dir(project)
    # The two link forms of the committed indexes: a headings section links relative to the
    # wiki's directory, a files section through the repository root.
    if section.kind == "headings":
        relative = posixpath.relpath(section.dir, wiki.as_posix())
        entries = [f"- [{_first_heading(f)}]({relative}/{f.name})" for f in found]
    else:
        relative = f"{_up(wiki)}/{section.dir}"
        entries = [f"- [{f.name}]({relative}/{f.name})" for f in found]
    return ["", f"## {section.title}", "", *entries]


def render_index(project: Project) -> str:
    head = ["# Wiki index", "", HEADER]
    files = [line for section in project.index_sections for line in _section(project, section)]
    return "\n".join(head + _pages(project) + _terms(project) + files) + "\n"
