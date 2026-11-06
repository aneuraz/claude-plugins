"""`search` and `show`: the project's wiki pages and the packs' rules, by citation."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath

from claude_plugins_tools.packs import Pack, UnknownCitation, resolve
from claude_plugins_tools.project import Project
from claude_plugins_tools.wiki.errors import WikiError
from claude_plugins_tools.wiki.grammar import PACK_CITATION, WIKI_CITATION
from claude_plugins_tools.wiki.model import split_front_matter, wiki_dir
from claude_plugins_tools.wiki.pages import load_pages


@dataclass(frozen=True)
class Hit:
    citation: str
    title: str

    def __str__(self) -> str:
        return f"{self.citation}  {self.title}"


def _matched(terms: Sequence[str], title: str, body: str) -> int:
    """How many distinct terms occur in the title or the body, ignoring case."""
    text = f"{title}\n{body}".casefold()
    return sum(term in text for term in {term.casefold() for term in terms})


def search(project: Project, terms: Sequence[str], packs: Mapping[str, Pack]) -> list[Hit]:
    """The wiki pages (when `[wiki]` is set) and live pack rules matching any term.

    Ranked by the number of distinct terms matched; ties keep citation order: the wiki's
    pages first, then the packs' rules by pack and slug.
    """
    scored: list[tuple[int, Hit]] = []
    if project.wiki_path is not None:
        for page in load_pages(project.root, wiki_dir(project)):
            path = PurePosixPath(page.path)
            title = str((page.raw or {}).get("title") or path.stem)
            scored.append(
                (
                    _matched(terms, title, page.body),
                    Hit(f"wiki:{path.parent.name}/{path.stem}", title),
                )
            )
    for name, pack in sorted(packs.items()):
        for slug, rule in sorted(pack.rules.items()):
            if rule.superseded_by is not None:
                continue
            _, body = split_front_matter(rule.path.read_text(encoding="utf-8"))
            scored.append((_matched(terms, rule.title, body), Hit(f"{name}:{slug}", rule.title)))
    ranked = sorted((item for item in scored if item[0]), key=lambda item: -item[0])
    return [hit for _, hit in ranked]


def show(project: Project, citation: str, packs: Mapping[str, Pack]) -> tuple[str, str | None]:
    """The cited page's or rule's text, and a notice when the citation is superseded."""
    if PACK_CITATION.fullmatch(citation):
        try:
            rule = resolve(citation, packs)
        except UnknownCitation as error:
            raise WikiError(str(error)) from error
        pack = citation.partition(":")[0]
        notice = None if rule.slug == citation.partition(":")[2] else f"{pack}:{rule.slug}"
        text = rule.path.read_text(encoding="utf-8")
        return text, notice and f"{citation} is superseded: cite {notice}"
    cited = WIKI_CITATION.fullmatch(citation)
    if cited:
        file = project.root / wiki_dir(project) / cited["directory"] / f"{cited['slug']}.md"
        if not file.is_file():
            raise WikiError(f"{citation} names no page")
        return file.read_text(encoding="utf-8"), None
    raise WikiError(f"{citation} is not a citation: wiki:<dir>/<slug> or <pack>:<slug>")
