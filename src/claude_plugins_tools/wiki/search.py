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


def _matches(terms: Sequence[str], title: str, body: str) -> bool:
    text = f"{title}\n{body}".casefold()
    return all(term.casefold() in text for term in terms)


def search(project: Project, terms: Sequence[str], packs: Mapping[str, Pack]) -> list[Hit]:
    """Every wiki page (when `[wiki]` is set), then every live pack rule, matching all terms."""
    hits: list[Hit] = []
    if project.wiki_path is not None:
        for page in load_pages(project.root, wiki_dir(project)):
            path = PurePosixPath(page.path)
            title = str((page.raw or {}).get("title") or path.stem)
            if _matches(terms, title, page.body):
                hits.append(Hit(f"wiki:{path.parent.name}/{path.stem}", title))
    for name, pack in sorted(packs.items()):
        for slug, rule in sorted(pack.rules.items()):
            if rule.superseded_by is not None:
                continue
            _, body = split_front_matter(rule.path.read_text(encoding="utf-8"))
            if _matches(terms, rule.title, body):
                hits.append(Hit(f"{name}:{slug}", rule.title))
    return hits


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
